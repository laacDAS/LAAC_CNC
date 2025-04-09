# -*- coding: utf-8 -*-
"""
DEMO CNC + CAMERA USB

- DESLOCA SOBRE AS PLANTAS
- CAPTURA FOTO E SALVA NO DIRETORIO FOTOS

Autor= Andre Luiz de Freitas Coelho
Data = 20 / 02 /2025
"""

# pacotes
import cv2 as cv
import serial
import time
import os
import json

# configura o diretorio para salvar
dir_img = "TT1/"
if not os.path.exists(dir_img):
    os.makedirs(dir_img)

# configuracoes do usuario
with open("cfg.json", "r") as file:
    data = json.load(file)

PORT = data["port"]        # Porta de comunicação com Arduino/GRBL
BAUDRATE = data["baudrate"]     # Taxa de transferência - padrão GRBL


'''
 P1 a P6 direita , P7 a P12 direita
<---- -X
P1 P2   
P3 P4
....
P11 P12
'''
ID_PLANT = [plant["id"] for plant in data["plants"]]
POS_X_PLANT = [plant["X"] for plant in data["plants"]]
POS_Y_PLANT = [plant["Y"] for plant in data["plants"]]


# Inicia camera
print("Iniciando Camera...")
cam = cv.VideoCapture(0)
if not cam.isOpened():
    print("Erro ao abrir a câmera. Verifique a conexão..")

# configura resolucao camera
cam.set(3, 1920)  # largura
cam.set(4, 1080)  # altura


# Inicializa a comunicação serial com GRBL
print("Iniciando comunicacao GRBL...")
try:
    grbl = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)  # Aguarda inicialização do GRBL
    grbl.write(b"\r\n\r\n")  # Reset da comunicação
    time.sleep(2)
    grbl.flushInput()  # Limpa buffer de entrada
    print("Conectado ao GRBL na porta  : ", PORT)

except Exception:
    print("Erro ao conectar na porta : ", PORT)
    exit()


# funcao para enviar comando GRBL e aguardar resposta
def send_grbl(cmd):
    grbl.write((cmd + "\r\n").encode())  # Envia comando
    time.sleep(0.1)  # Pequeno delay para resposta
    while grbl.inWaiting() > 0:
        response = grbl.readline().decode().strip()  # Lê resposta do GRBL
        print("GRBL:", response)

# espera usuario para continuar


def wait_user(msg):
    cmd = input('\n'+msg + " ( y= yes  n= no ) >> ")
    if cmd.lower() == "n":
        grbl.close()
        exit()

# obtem imagem


def GetImage(plant):
    _, frame = cam.read()
    # Reduz a resolução para exibição
    frame_resized = cv.resize(frame, (640, 360))
    cv.imshow('Imagem', frame_resized)
    nome = dir_img+ID_PLANT[plant]+'.jpg'  # nome do arquivo
    cv.imwrite(nome, frame)  # grava imagem
    cv.waitKey(30) & 0xff  # comando obrigatorio para o imshow


# Mostra para verificar se camera está funcionando
GetImage(0)

# comando Unlock
# wait_user('Unlock ?')
print("Desbloqueando...")
send_grbl('$X')
time.sleep(2)

# comando ToHome
# wait_user('To Home ?')
print("Go to home...")
send_grbl('$H')
time.sleep(10)

# Comando ir ao ponto X0 Y0 -- Precisa começar em X0 Y0????
# wait_user('To X0 Y0 ? ')
print("Go to X0 Y0...")
send_grbl('G0X0Y0')
time.sleep(10)

# comando mostra configuracoes GRBL
print("Configuracoes GRBL...")
send_grbl('$')

# comando mostra status da maquina
print("Status Maquina...")
send_grbl('?')


# inicia captura automatizada
# Vai até cada planta e captura 1 imagem
# wait_user('Iniciar Captura Automatica? ')
print("Iniciando Captura...")

# define velocidade de deslocamento
print("Configurando velocidade...")
send_grbl('G1 F7000')  # precisa do G1 ?????

# Loop para as 12 plantas
for plant in range(12):
    print("Planta " + ID_PLANT[plant])
    print('Deslocando...')
    send_grbl('G1 X'+str(POS_X_PLANT[plant])+'Y'+str(POS_Y_PLANT[plant]))
    time.sleep(10)  # aguarda chegar
    GetImage(plant)  # obtem imagem para a planta
    # if plant < 11: wait_user('Proxima planta? ')

# Retorna para X0 Y0
# wait_user('To X0 Y0 ? ')
print("Go to X0 Y0...")
send_grbl('G0X0Y0')
time.sleep(10)

print("Fechando conexão...")
grbl.close()
