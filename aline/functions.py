import cv2 as cv
from tkinter import messagebox
import sys
import serial
import time
import os
import threading
import datetime
from PIL import Image, ImageTk
import tkinter as tk
import threading


def iniciar_camera(camera_id=0, largura=1920, altura=1080):
    print("Iniciando câmera...")
    cam_local = cv.VideoCapture(camera_id)
    if not cam_local.isOpened():
        messagebox.showerror("Erro", "Não foi possível abrir a câmera. Verifique a conexão.")
        sys.exit(1)
    cam_local.set(3, largura)
    cam_local.set(4, altura)
    return cam_local

def iniciar_serial(porta, baudrate):
    print("Iniciando comunicação com GRBL...")
    try:
        grbl_local = serial.Serial(porta, baudrate, timeout=1)
        time.sleep(2)
        grbl_local.write(b"\r\n\r\n")
        time.sleep(2)
        grbl_local.flushInput()
        print("Conectado ao GRBL na porta:", porta)
        return grbl_local
    except serial.SerialException as e:
        messagebox.showerror("Erro", f"Erro ao conectar na porta {porta}: {e}")
        sys.exit(1)

def send_grbl(cmd, grbl, delay=0.1):
    if grbl is None:
        print("GRBL não inicializado!")
        return
    comando = cmd + "\r\n"
    grbl.write(comando.encode())
    time.sleep(delay)
    while grbl.inWaiting() > 0:
        response = grbl.readline().decode().strip()
        print("GRBL:", response)

def capturar_imagem(indice, cam, dir_img, id_plant):
    if cam is None:
        print("Câmera não inicializada!")
        return None, None
    ret, frame = cam.read()
    if not ret:
        print("Erro ao capturar imagem!")
        return None, None
    frame_resized = cv.resize(frame, (640, 360))
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = os.path.join(dir_img, f"{id_plant[indice]}_{current_time}.jpg")
    cv.imwrite(nome_arquivo, frame)
    cv.waitKey(30)
    print(f"Imagem da planta {id_plant[indice]} salva em {nome_arquivo}")
    return nome_arquivo, id_plant[indice]

def processar_planta(indice, grbl, velocidade, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay):
    try:
        cmd_vel = f'G1 F{velocidade}'
        print("Configurando velocidade:", cmd_vel)
        send_grbl(cmd_vel, grbl)

        cmd_move = f"G1 X{pos_x_plant[indice]} Y{pos_y_plant[indice]}"
        print("Movendo para:", cmd_move)
        send_grbl(cmd_move, grbl)

        time.sleep(move_delay)

        cam = iniciar_camera()
        caminho_imagem, nome_imagem = capturar_imagem(indice, cam, dir_img, id_plant)
        cam.release()

        print("Retornando para a posição inicial (X0 Y0)...")
        send_grbl('G0 X0 Y0', grbl)
        time.sleep(move_delay)

        if caminho_imagem:
            print(f"Imagem da planta {nome_imagem} capturada com sucesso.")
        else:
            print(f"Erro ao capturar a imagem da planta {nome_imagem}.")

        return caminho_imagem, nome_imagem
    except Exception as e:
        messagebox.showerror("Erro", f"Erro durante o processo da planta {id_plant[indice]}: {e}")
        return None, None

def init_system(dir_img, id_plant, port, baudrate):
    cam = iniciar_camera()
    grbl = iniciar_serial(port, baudrate)
    return cam, grbl

def close_system(grbl, cam, root):
    if grbl is not None:
        grbl.close()
    if cam is not None:
        cam.release()
    cv.destroyAllWindows()
    root.quit()  

def toggle_plant_selection(plant_id, selected_plants, plant_buttons):
        if selected_plants.get(plant_id):
            selected_plants.pop(plant_id)
            plant_buttons[plant_id].config(bg="white", fg="black")
        else:
            selected_plants[plant_id] = True
            plant_buttons[plant_id].config(bg="lightgreen", fg="black")

def processo_bloco(speed_entry, start_idx, end_idx, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay, grbl, img_label, img_name_entry):
    try:
        velocidade = int(speed_entry.get())
        for idx in range(start_idx, end_idx + 1):
            caminho_imagem, nome_imagem = processar_planta(
                idx,
                grbl,
                velocidade,
                pos_x_plant,
                pos_y_plant,
                dir_img,
                id_plant,
                move_delay
            )
            atualizar_imagem(caminho_imagem, nome_imagem, img_label, img_name_entry)

    except ValueError:
        messagebox.showerror("Erro", "Velocidade inválida.")

def executar_captura(selected_plants, speed_entry, id_plant, grbl, pos_x_plant, pos_y_plant, dir_img, move_delay, img_label, img_name_entry, plant_buttons):
    thread = threading.Thread(
        target=_executar_captura_thread,
        args=(selected_plants, speed_entry, id_plant, grbl, pos_x_plant, pos_y_plant, dir_img, move_delay, img_label, img_name_entry, plant_buttons)
    )
    thread.start()

def _executar_captura_thread(selected_plants, speed_entry, id_plant, grbl, pos_x_plant, pos_y_plant, dir_img, move_delay, img_label, img_name_entry, plant_buttons):
    try:
        velocidade = int(speed_entry.get())

        if not selected_plants:
            messagebox.showerror("Erro", "Nenhuma planta selecionada.")
            return

        sequence = list(selected_plants.keys())

        for plant_id in sequence:
            idx = id_plant.index(plant_id)
            caminho_imagem, nome_imagem = processar_planta(idx, grbl, velocidade, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay)

            if caminho_imagem:
                img_label.after(0, atualizar_imagem, caminho_imagem, nome_imagem, img_label, img_name_entry)
                plant_buttons[plant_id].after(0, lambda pid=plant_id: plant_buttons[pid].config(bg="lightgreen"))
            else:
                plant_buttons[plant_id].after(0, lambda pid=plant_id: plant_buttons[pid].config(bg="red"))

    except ValueError:
        messagebox.showerror("Erro", "Entradas inválidas. Verifique os campos.")

def executar_coleta_bloco(bloco, speed_entry, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay, grbl, img_label, img_name_entry):
    thread = threading.Thread(
        target=_executar_coleta_bloco_thread,
        args=(bloco, speed_entry, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay, grbl, img_label, img_name_entry)
    )
    thread.start()

def _executar_coleta_bloco_thread(bloco, speed_entry, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay, grbl, img_label, img_name_entry):
    if bloco == 3:
        start_idx, end_idx = 6, 11
    elif bloco == 4:
        start_idx, end_idx = 0, 5
    else:
        messagebox.showerror("Erro", "Bloco inválido.")
        return
    processo_bloco(speed_entry, start_idx, end_idx, pos_x_plant, pos_y_plant, dir_img, id_plant, move_delay, grbl, img_label, img_name_entry)

def atualizar_imagem(caminho_imagem, nome_imagem, img_label, img_name_entry):
    img = Image.open(caminho_imagem)
    img = img.resize((1920, 1080))
    img_tk = ImageTk.PhotoImage(img)
    img_label.config(image=img_tk)
    img_label.image = img_tk
    img_name_entry.delete(0, tk.END)
    img_name_entry.insert(0, nome_imagem)
