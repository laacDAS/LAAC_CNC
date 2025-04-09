import cv2 as cv
import serial
import time
import os
import json
import signal
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import threading


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle GRBL e Captura de Imagens")
        self.root.geometry("1000x700")

        # Frame principal para organizar o layout
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame para log e status (parte superior)
        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_label = ttk.Label(self.log_frame, text="Log de Saída")
        self.log_label.pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, height=10, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.status_label = ttk.Label(
            self.log_frame, text="Status: Aguardando inicialização...")
        self.status_label.pack(anchor=tk.W, pady=5)

        # Frame para seleção de plantas (esquerda)
        self.selection_frame = ttk.Frame(self.main_frame)
        self.selection_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.plant_label = ttk.Label(
            self.selection_frame, text="Selecione as Plantas:")
        self.plant_label.pack(anchor=tk.W)
        self.plant_listbox = tk.Listbox(
            self.selection_frame, selectmode=tk.MULTIPLE, height=15, width=20)
        self.plant_listbox.pack(fill=tk.Y)

        # Carrega as plantas do JSON e popula a Listbox
        with open("cfg.json", "r") as file:
            data = json.load(file)
        self.ID_PLANT = [plant["id"] for plant in data["plants"]]
        self.POS_X_PLANT = [plant["X"] for plant in data["plants"]]
        self.POS_Y_PLANT = [plant["Y"] for plant in data["plants"]]
        for i, plant_id in enumerate(self.ID_PLANT):
            if plant_id != "B00":
                self.plant_listbox.insert(tk.END, plant_id)

        # Frame para progresso e botões (centro)
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.LEFT, fill=tk.X, expand=False)

        self.progress_frame = ttk.Frame(self.control_frame)
        self.progress_frame.pack(fill=tk.X, pady=5)
        self.progress_label = ttk.Label(self.progress_frame, text="Progresso:")
        self.progress_label.pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, length=500, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_text = ttk.Label(self.progress_frame, text="0.0% (0/0)")
        self.progress_text.pack(side=tk.LEFT, padx=5)

        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        self.start_button = ttk.Button(
            self.button_frame, text="Iniciar", command=self.start_process)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(
            self.button_frame, text="Cancelar", command=self.cancel, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Frame para visualização da imagem (direita)
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_label = ttk.Label(
            self.image_frame, text="Imagem Atual: Nenhuma planta selecionada")
        self.image_label.pack(anchor=tk.W)
        self.canvas = tk.Canvas(self.image_frame, width=640, height=360)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Variáveis globais
        self.grbl = None
        self.cam = None
        self.running = False
        self.thread = None

        # Registra o manipulador de sinal na thread principal
        signal.signal(signal.SIGINT, self.signal_handler)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status):
        self.status_label.config(text=f"Status: {status}")

    def update_progress(self, current, total):
        percent = (current / total) * 100 if total > 0 else 0
        self.progress_bar['value'] = percent
        self.progress_text.config(text=f"{percent:.1f}% ({current}/{total})")
        self.root.update_idletasks()

    def update_image(self, frame, plant_name):
        frame_resized = cv.resize(frame, (640, 360))
        img = cv.cvtColor(frame_resized, cv.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        photo = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Mantém referência para evitar garbage collection
        self.image_label.config(text=f"Imagem Atual: {plant_name}")
        self.root.update_idletasks()

    def signal_handler(self, sig, frame):
        self.log("===============================================================")
        self.log("\nInterrupção detectada (Ctrl + C). Finalizando...")
        self.log("===============================================================")
        self.finalize()

    def cancel(self):
        self.log("===============================================================")
        self.log("\nCancelamento solicitado. Finalizando...")
        self.log("===============================================================")
        self.finalize()

    def finalize(self):
        self.log("\n--- Fechando conexão... ---")
        if self.grbl:
            self.grbl.close()
        if self.cam:
            self.cam.release()
        cv.destroyAllWindows()
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.image_label.config(
            text="Imagem Atual: Nenhuma planta selecionada")

    def send_grbl(self, cmd):
        self.grbl.write((cmd + "\r\n").encode())
        while True:
            if self.grbl.inWaiting() > 0:
                response = self.grbl.readline().decode().strip()
                self.log("GRBL: " + response)
                if "ok" in response or "error" in response:
                    break
            time.sleep(0.01)

    def wait_for_idle(self):
        while self.running:
            self.grbl.write(b"?")
            time.sleep(0.1)
            if self.grbl.inWaiting() > 0:
                status = self.grbl.readline().decode().strip()
                self.update_status(status)
                self.log("Status: " + status)
                if "<Idle" in status:
                    break

    def get_image(self, plant_idx):
        # Skip B00 processing completely
        if self.ID_PLANT[plant_idx] == "B00":
            self.log(f"Ignorando planta B00 conforme solicitado")
            return

        ret, frame = self.cam.read()
        if not ret:
            self.log(
                f"Erro ao capturar imagem para {self.ID_PLANT[plant_idx]}")
            return
        # Passa o nome da planta
        self.update_image(frame, self.ID_PLANT[plant_idx])
        frame_resized = cv.resize(frame, (640, 360))
        nome = dir_img + self.ID_PLANT[plant_idx] + '.jpg'
        cv.imwrite(nome, frame)
        self.log(f"Imagem capturada para {self.ID_PLANT[plant_idx]}")

    def start_process(self):
        if self.running:
            return  # Evita iniciar múltiplas threads

        # Obtém os índices das plantas selecionadas na UI
        ui_selected_indices = list(self.plant_listbox.curselection())

        # Converter para índices reais e sempre incluir B00
        selected_indices = []
        b00_index = None

        # Encontrar o índice de B00
        for i, plant_id in enumerate(self.ID_PLANT):
            if plant_id == "B00":
                b00_index = i
                break

        # Se nenhuma planta for selecionada, usar todas (incluindo B00)
        if not ui_selected_indices:
            selected_indices = list(range(len(self.ID_PLANT)))
            self.log(
                "Nenhuma planta selecionada. Processando todas as plantas como padrão.")
        else:
            # Mapear seleções da UI para índices reais (considerando que B00 não está na UI)
            visible_idx = 0
            for i, plant_id in enumerate(self.ID_PLANT):
                if plant_id != "B00":
                    if visible_idx in ui_selected_indices:
                        selected_indices.append(i)
                    visible_idx += 1

            self.log(
                f"Processando {len(ui_selected_indices)} plantas selecionadas.")

        # Sempre incluir B00 se existir
        if b00_index is not None and b00_index not in selected_indices:
            selected_indices.append(b00_index)

        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.running = True
        self.thread = threading.Thread(
            target=self.run_process, args=(selected_indices,))
        self.thread.daemon = True
        self.thread.start()

    def run_process(self, selected_indices):
        global grbl, cam, dir_img
        self.grbl = None
        self.cam = None

        # Configura o diretório para salvar
        dir_img = "TT2/"
        if not os.path.exists(dir_img):
            os.makedirs(dir_img)

        # Configs iniciais
        with open("cfg.json", "r") as file:
            data = json.load(file)

        PORT = data["port"]
        BAUDRATE = data["baudrate"]

        # Inicializa GRBL
        self.log("Iniciando comunicacao GRBL...")
        try:
            self.grbl = serial.Serial(PORT, BAUDRATE, timeout=1)
            time.sleep(2)
            self.grbl.write(b"\r\n\r\n")
            time.sleep(2)
            self.grbl.flushInput()
            self.log("Conectado ao GRBL na porta: " + PORT)
        except Exception as e:
            self.log("Erro ao conectar na porta: " + str(e))
            self.finalize()
            return

        # Inicializa câmera
        self.log("-> Iniciando Camera...")
        self.cam = cv.VideoCapture(0, cv.CAP_DSHOW)
        if not self.cam.isOpened():
            self.log("-> Erro ao abrir a câmera. Verifique a conexão...")
            self.grbl.close()
            self.finalize()
            return
        self.cam.set(3, 1920)
        self.cam.set(4, 1080)

        # Sequência de comandos
        num_plants = len(selected_indices)
        self.log(f"Processando {num_plants} plantas...")
        self.update_progress(0, num_plants)
        self.send_grbl('$X')  # Unlock
        self.wait_for_idle()
        self.send_grbl('$H')  # Home
        self.wait_for_idle()
        self.send_grbl('$')   # Configs
        self.send_grbl('?')   # Status
        self.send_grbl('G1 F14000')  # Velocidade

        # Loop para as plantas selecionadas (ou todas, se padrão)
        for i, plant_idx in enumerate(selected_indices):
            if not self.running:
                break
            self.log(
                "===============================================================")
            self.log(
                f'Planta {i + 1} de {num_plants} - Deslocando para ' + self.ID_PLANT[plant_idx])
            self.send_grbl(
                'G1 X' + str(self.POS_X_PLANT[plant_idx]) + ' Y' + str(self.POS_Y_PLANT[plant_idx]))
            self.wait_for_idle()
            self.get_image(plant_idx)
            self.update_progress(i + 1, num_plants)

        # Finaliza com 100%
        self.update_progress(num_plants, num_plants)
        self.log("\nConcluído!")

        # Verifica e remove B00.jpg
        b00_path = os.path.join(dir_img, "B00.jpg")
        if os.path.exists(b00_path):
            self.log(f"-> Arquivo {b00_path} encontrado. Removendo...")
            os.remove(b00_path)
            self.log(f"-> {b00_path} removido com sucesso.")
        else:
            self.log(f"-> Nenhum arquivo B00.jpg encontrado em {dir_img}.")

        # Retorna para origem
        self.send_grbl('G0 X0 Y0')
        self.wait_for_idle()

        # Finaliza normalmente
        self.finalize()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
