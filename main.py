import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import threading
import signal
import json

from functions import (
    log, update_status, update_progress, update_image,
    signal_handler, cancel, finalize, send_grbl, wait_for_idle,
    get_image, start_process, run_process, criar_interface_gerar_pontos,
    execute_homing_automatic
)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle GRBL e Captura de Imagens")
        self.root.geometry("1000x700")

        # Adiciona interface para geração de pontos adensados
        criar_interface_gerar_pontos(self)

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

        # Carrega as plantas do JSON
        with open("cfg.json", "r") as file:
            self.data_json = json.load(file)

        # Adiciona opção para selecionar o Room
        self.room_var = tk.StringVar(value="Room B")
        self.room_label = ttk.Label(self.selection_frame, text="Selecione o Room:")
        self.room_label.pack(anchor=tk.W, pady=(10, 0))
        self.room_combo = ttk.Combobox(
            self.selection_frame, textvariable=self.room_var, state="readonly",
            values=["Room A", "Room B"]
        )
        self.room_combo.pack(fill=tk.X, pady=(0, 10))
        self.room_combo.bind("<<ComboboxSelected>>", self.update_plants_list)

        self.update_plants_list()

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
            self.button_frame, text="Iniciar", command=lambda: start_process(self))
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(
            self.button_frame, text="Cancelar", command=lambda: cancel(self), state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Botão Captura Adensada
        from functions import start_dense_process
        self.captura_adensada_button = ttk.Button(
            self.button_frame,
            text="Captura Adensada",
            command=lambda: start_dense_process(self)
        )
        self.captura_adensada_button.pack(side=tk.LEFT, padx=5)
        # Checkbox para rotacionar 180 graus a captura da webcam
        self.rotate_180_var = tk.BooleanVar(value=False)
        self.rotate_180_chk = ttk.Checkbutton(
            self.button_frame,
            text="Rotacionar Imagem 180°",
            variable=self.rotate_180_var
        )
        self.rotate_180_chk.pack(side=tk.LEFT, padx=5)

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
        self.homing_executed = False  # Rastreia se homing foi executado automaticamente

        # Registra o manipulador de sinal na thread principal
        signal.signal(signal.SIGINT, lambda sig,
                      frame: signal_handler(self, sig, frame))
        
        # Executa homing automático na inicialização (via root.after para evitar bloqueio)
        self.root.after(500, lambda: execute_homing_automatic(self))

    def update_plants_list(self, event=None):
        room_key = self.room_var.get()
        plants = self.data_json[room_key]
        self.ID_PLANT = [plant["id"] for plant in plants]
        self.POS_X_PLANT = [plant["X"] for plant in plants]
        self.POS_Y_PLANT = [plant["Y"] for plant in plants]
        self.plant_listbox.delete(0, tk.END)
        for plant in plants:
            self.plant_listbox.insert(tk.END, plant['id'])


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
