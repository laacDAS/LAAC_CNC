import cv2 as cv
import serial
import time
import os
import json
import signal
import sys

# Função para tratar a interrupção com Ctrl + C


def signal_handler(sig, frame):
    print("\n===============================================================")
    print("Interrupção detectada (Ctrl + C). Finalizando...")
    print("\n===============================================================")
    finalize()

# Função de finalização


def finalize():
    print("\n--- Fechando conexão... ---")
    grbl.close()
    cam.release()
    cv.destroyAllWindows()
    sys.exit(0)

# Funções existentes


def send_grbl(cmd):
    grbl.write((cmd + "\r\n").encode())
    while True:
        if grbl.inWaiting() > 0:
            response = grbl.readline().decode().strip()
            print("GRBL:", response)
            if "ok" in response or "error" in response:
                break
        time.sleep(0.01)


def wait_for_idle():
    while True:
        grbl.write(b"?")
        time.sleep(0.1)
        if grbl.inWaiting() > 0:
            status = grbl.readline().decode().strip()
            print("Status:", status)
            if "<Idle" in status:
                break


def wait_user(msg):
    cmd = input('\n' + msg + " ( y= yes  n= no ) >> ")
    if cmd.lower() == "n":
        finalize()


def GetImage(image_number):
    ret, frame = cam.read()
    if not ret:
        print(f"Erro ao capturar imagem {image_number:03d}")
        return
    frame_resized = cv.resize(frame, (640, 360))
    if os.environ.get("DISPLAY"):
        cv.imshow('Imagem', frame_resized)
        cv.waitKey(30)
    nome = dir_img + f"{image_number:03d}.jpg"  # Nome de 001 a 120
    cv.imwrite(nome, frame)

# Função para exibir a barra de progresso


def print_progress(current, total, width=50):
    progress = current / total
    filled = int(width * progress)
    bar = '#' * filled + '-' * (width - filled)
    percent = progress * 100
    print(f"Progresso: [{bar}] {percent:.1f}% ({current}/{total})")


# Configura o diretório para salvar
dir_img = "output_image/"
if not os.path.exists(dir_img):
    os.makedirs(dir_img)

# Configs iniciais
with open("cfg.json", "r") as file:
    data = json.load(file)

PORT = data["port"]
BAUDRATE = data["baudrate"]
ID_PLANT = [plant["id"] for plant in data["plants"]]
POS_X_PLANT = [plant["X"] for plant in data["plants"]]
POS_Y_PLANT = [plant["Y"] for plant in data["plants"]]

# Registra o manipulador de sinal para Ctrl + C
signal.signal(signal.SIGINT, signal_handler)

# Inicializa GRBL
print("Iniciando comunicacao GRBL...")
try:
    grbl = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    grbl.write(b"\r\n\r\n")
    time.sleep(2)
    grbl.flushInput()
    print("Conectado ao GRBL na porta:", PORT)
except Exception:
    print("Erro ao conectar na porta:", PORT)
    exit()

# Inicializa câmera
print("-> Iniciando Camera...")
cam = cv.VideoCapture(0, cv.CAP_DSHOW)
if not cam.isOpened():
    print("-> Erro ao abrir a câmera. Verifique a conexão...")
    grbl.close()
    exit()
cam.set(3, 1920)
cam.set(4, 1080)

# Sequência de comandos
print(f"Processando 12 plantas, 10 vezes cada (120 capturas)...")
print_progress(0, 120)  # Progresso inicial
send_grbl('$X')  # Unlock
wait_for_idle()
send_grbl('$H')  # Home
wait_for_idle()
send_grbl('$')   # Configs
send_grbl('?')   # Status
wait_user('-> Iniciar Captura Automatica? ')
send_grbl('G1 F14000')  # Velocidade

# Loop para 12 plantas, 10 repetições cada
total_images = 120
image_counter = 1  # Começa em 1 para nomear de 001 a 120

for repetition in range(10):  # 10 repetições
    for plant in range(12):  # 12 plantas
        print("===============================================================")
        print(
            f'Repetição {repetition + 1}/10 - Planta {plant + 1}/12 - Deslocando para {ID_PLANT[plant]}')
        send_grbl(
            'G1 X' + str(POS_X_PLANT[plant]) + ' Y' + str(POS_Y_PLANT[plant]))
        wait_for_idle()
        GetImage(image_counter)
        print(
            f"Imagem capturada: {image_counter:03d}.jpg para {ID_PLANT[plant]}")
        print_progress(image_counter, total_images)
        image_counter += 1

# Finaliza com 100%
print_progress(total_images, total_images)
print("\nConcluído!")

# Retorna para origem
send_grbl('G0 X0 Y0')
wait_for_idle()

# Finaliza normalmente
finalize()
