import tkinter as tk
from tkinter import ttk, messagebox
import cv2 as cv
import serial
import time
import os
import threading
import sys
import functions
import time
import json
from PIL import Image, ImageTk
import threading


def main():
    with open("cfg.json", "r") as file:
        data = json.load(file)

    DIR_IMG = "TT1/"
    os.makedirs(DIR_IMG, exist_ok=True)

    port = data["port"]
    baudrate = data["baudrate"]

    id_plant = [plant["id"] for plant in data["plants"]]
    pos_x_plant = [plant["X"] for plant in data["plants"]]
    pos_y_plant = [plant["Y"] for plant in data["plants"]]

    MOVE_DELAY = 10

    fonte_padrao = ("Open Sans", 10)
    fonte_titulo = ("Open Sans", 10, "bold")

    root = tk.Tk()
    root.title("Interface CNC + Camera USB")
    root.geometry("700x600")
    root.configure(bg="#E0E7E9")

    selected_plants = {}

    # Frame de Configurações
    frame_config = tk.Frame(root, bg="#E0E7E9")
    frame_config.grid(row=0, column=0, padx=20, pady=10, sticky="nw")

    ttk.Label(frame_config, text="Configurações", background="#E0E7E9", font=fonte_titulo).grid(
        row=0, column=0, columnspan=2, pady=5, sticky="nsew")

    ttk.Label(frame_config, text="Velocidade (F):", background="#E0E7E9",
              font=fonte_padrao).grid(row=1, column=0, sticky="e", pady=2)
    speed_entry = ttk.Entry(frame_config, width=10, font=fonte_padrao)
    speed_entry.insert(0, "14000")
    speed_entry.grid(row=1, column=1, pady=2)

    # Frame para seleção de plantas
    frame_plants = tk.Frame(root, bg="#E0E7E9")
    frame_plants.grid(row=1, column=0, padx=20, pady=10, sticky="nw")

    ttk.Label(frame_plants, text="Select Plants", background="#E0E7E9", font=fonte_titulo).grid(
        row=0, column=0, columnspan=2, pady=5, sticky="nsew")

    plant_buttons = {}

    new_order = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    for i, plant_id in enumerate(new_order):
        btn = tk.Button(frame_plants, text=f"B{plant_id:02}", width=5, height=2, bg="white", fg="black",
                        relief="flat", borderwidth=0, font=fonte_padrao,
                        command=lambda pid=f"B{plant_id:02}": functions.toggle_plant_selection(pid, selected_plants, plant_buttons))
        row = i % 6
        col = 0 if i < 6 else 1
        btn.grid(row=row + 1, column=col, padx=10, pady=5, sticky="nsew")
        plant_buttons[f"B{plant_id:02}"] = btn

    # Frame para Coleta por Bloco
    bloco_frame = tk.Frame(frame_plants, bg="#E0E7E9")
    bloco_frame.grid(row=7, column=0, columnspan=2,
                     pady=(15, 5), sticky="nsew")

    ttk.Label(bloco_frame, text="Coleta por Bloco", background="#E0E7E9", font=fonte_titulo).grid(
        row=0, column=0, columnspan=2, pady=(0, 5), sticky="nsew")

    btn_bloco3 = ttk.Button(bloco_frame, text="Coletar Bloco 3", command=lambda: functions.executar_coleta_bloco(
        3, speed_entry, pos_x_plant, pos_y_plant, DIR_IMG, id_plant, MOVE_DELAY, grbl, img_label, img_name_entry))
    btn_bloco3.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    btn_bloco4 = ttk.Button(bloco_frame, text="Coletar Bloco 4", command=lambda: functions.executar_coleta_bloco(
        4, speed_entry, pos_x_plant, pos_y_plant, DIR_IMG, id_plant, MOVE_DELAY, grbl, img_label, img_name_entry))
    btn_bloco4.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

    # Botão Iniciar Coleta
    btn_start = ttk.Button(frame_plants, text="Iniciar Coleta", command=lambda: functions.executar_captura(
        selected_plants, speed_entry, id_plant, grbl, pos_x_plant, pos_y_plant, DIR_IMG, MOVE_DELAY, img_label, img_name_entry, plant_buttons))
    btn_start.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")

    # Área de visualização da imagem
    frame_image = tk.Frame(root, bg="#E0E7E9")
    frame_image.grid(row=0, column=1, rowspan=3,
                     padx=20, pady=10, sticky="nsew")

    # Título "Imagem Coletada" em negrito
    ttk.Label(frame_image, text="Imagem Coletada", background="#E0E7E9",
              font=fonte_titulo).pack(pady=5, anchor="w")

    # Linha para "Nome da imagem" e entrada
    frame_img_name = tk.Frame(frame_image, bg="#E0E7E9")
    frame_img_name.pack(pady=2, padx=10)

    img_name_label = ttk.Label(
        frame_img_name, text="Nome da imagem:", background="#E0E7E9", font=fonte_padrao)
    img_name_label.pack(side="left", padx=(0, 5))

    img_name_entry = tk.Entry(
        frame_img_name, relief="flat", borderwidth=0, font=fonte_padrao)
    img_name_entry.pack(side="left")

    img_label = tk.Label(frame_image, bg="white",
                         width=40, height=30, relief="solid")
    img_label.pack(padx=10, pady=10)

    # Botão Fechar Sistema
    btn_close = ttk.Button(root, text="Fechar Sistema",
                           command=lambda: functions.close_system(grbl, cam, root))
    btn_close.place(relx=0.5, rely=0.98, anchor="s")

    # Inicialização do sistema
    cam, grbl = functions.init_system(DIR_IMG, id_plant, port, baudrate)

    root.protocol("WM_DELETE_WINDOW",
                  lambda: functions.close_system(grbl, cam, root))
    root.mainloop()


if __name__ == "__main__":
    main()
