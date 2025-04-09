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
            print("Status:", status)  # Rola normalmente no log
            if "<Idle" in status:
                break


def wait_user(msg):
    cmd = input('\n' + msg + " ( y= yes  n= no ) >> ")
    if cmd.lower() == "n":
        finalize()


def GetImage(plant):
    ret, frame = cam.read()
    if not ret:
        print(f"Erro ao capturar imagem para {ID_PLANT[plant]}")
        return
    frame_resized = cv.resize(frame, (640, 360))
    if os.environ.get("DISPLAY"):
        cv.imshow('Imagem', frame_resized)
        cv.waitKey(30)
    nome = dir_img + ID_PLANT[plant] + '.jpg'
    cv.imwrite(nome, frame)

# Função para exibir a barra de progresso no fluxo normal


def print_progress(current, total, width=50):
    progress = current / total
    filled = int(width * progress)
    bar = '#' * filled + '-' * (width - filled)
    percent = progress * 100
    print(f"Progresso: [{bar}] {percent:.1f}% ({current}/{total})")


# Configura o diretório para salvar
dir_img = "TT2/"
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
print(f"Processando {len(ID_PLANT)} plantas...")
print_progress(0, len(ID_PLANT))  # Progresso inicial
send_grbl('$X')  # Unlock
wait_for_idle()
send_grbl('$H')  # Home
wait_for_idle()
send_grbl('$')   # Configs
send_grbl('?')   # Status
wait_user('-> Iniciar Captura Automatica? ')
send_grbl('G1 F14000')  # Velocidade

# Loop para as plantas
num_plants = len(ID_PLANT)
for plant in range(42):
    print("===============================================================")
    print(
        f'Planta {plant + 1} de {num_plants} - Deslocando para ' + ID_PLANT[plant])
    send_grbl('G1 X' + str(POS_X_PLANT[plant]
                           ) + ' Y' + str(POS_Y_PLANT[plant]))
    wait_for_idle()
    GetImage(plant)
    print(
        f"Imagem capturada para {ID_PLANT[plant]} ({plant + 1}/{num_plants})")
    print_progress(plant + 1, num_plants)  # Progresso rola com o log

# Finaliza com 100%
print_progress(num_plants, num_plants)
print("\nConcluído!")

# Verifica e remove B00.jpg, se existir
b00_path = os.path.join(dir_img, "B00.jpg")
if os.path.exists(b00_path):
    print(f"-> Arquivo {b00_path} encontrado. Removendo...")
    os.remove(b00_path)
    print(f"-> {b00_path} removido com sucesso.")
else:
    print(f"-> Nenhum arquivo B00.jpg encontrado em {dir_img}.")

# Retorna para origem
send_grbl('G0 X0 Y0')
wait_for_idle()

# Finaliza normalmente
finalize()
