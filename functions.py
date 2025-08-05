import cv2 as cv
import serial
import time
import os
import json
import datetime
import threading

def log(self, message):
    self.log_text.insert('end', message + "\n")
    self.log_text.see('end')
    self.root.update_idletasks()

def update_status(self, status):
    self.status_label.config(text=f"Status: {status}")

def update_progress(self, current, total):
    percent = (current / total) * 100 if total > 0 else 0
    self.progress_bar['value'] = percent
    self.progress_text.config(text=f"{percent:.1f}% ({current}/{total})")
    self.root.update_idletasks()

def update_image(self, frame, plant_name):
    from PIL import Image, ImageTk
    frame_resized = cv.resize(frame, (640, 360))
    img = cv.cvtColor(frame_resized, cv.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    photo = ImageTk.PhotoImage(image=img)
    self.canvas.create_image(0, 0, anchor='nw', image=photo)
    self.canvas.image = photo
    self.image_label.config(text=f"Imagem Atual: {plant_name}")
    self.root.update_idletasks()

def signal_handler(self, sig, frame):
    log(self, "===============================================================")
    log(self, "\nInterrupção detectada (Ctrl + C). Finalizando...")
    log(self, "===============================================================")
    finalize(self)

def cancel(self):
    log(self, "===============================================================")
    log(self, "\nCancelamento solicitado. Finalizando...")
    log(self, "===============================================================")
    finalize(self)

def finalize(self):
    log(self, "\n--- Fechando conexão... ---")
    if self.grbl:
        self.grbl.close()
    if self.cam:
        self.cam.release()
    cv.destroyAllWindows()
    self.running = False
    self.start_button.config(state='normal')
    self.cancel_button.config(state='disabled')
    self.image_label.config(text="Imagem Atual: Nenhuma planta selecionada")

def send_grbl(self, cmd):
    self.grbl.write((cmd + "\r\n").encode())
    while True:
        if self.grbl.inWaiting() > 0:
            response = self.grbl.readline().decode().strip()
            log(self, "GRBL: " + response)
            if "ok" in response or "error" in response:
                break
        time.sleep(0.01)

def wait_for_idle(self):
    while self.running:
        self.grbl.write(b"?")
        time.sleep(0.1)
        if self.grbl.inWaiting() > 0:
            status = self.grbl.readline().decode().strip()
            update_status(self, status)
            log(self, "Status: " + status)
            if "<Idle" in status:
                break

def get_image(self, plant_idx):
    self.cam.read() # importante para descartar o primeiro frame
    time.sleep(0.1)  # Aguarda um pouco para estabilizar a câmera
    ret, frame = self.cam.read()
    if not ret:
        log(self, f"Erro ao capturar imagem para {self.ID_PLANT[plant_idx]}")
        return
    update_image(self, frame, self.ID_PLANT[plant_idx])
    nome = os.path.join(self.session_dir, f"{self.ID_PLANT[plant_idx]}.jpg")
    cv.imwrite(nome, frame)
    log(self, f"Imagem capturada para {self.ID_PLANT[plant_idx]} em {nome}")

def start_process(self):
    if self.running:
        return

    # Sempre processa todas as plantas do JSON, na ordem
    selected_indices = list(range(len(self.ID_PLANT)))
    log(self, "Processando todas as plantas do JSON, na ordem definida.")

    # Cria pasta com data/hora
    
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    self.session_dir = os.path.join("output_images", now)
    if not os.path.exists(self.session_dir):
        os.makedirs(self.session_dir)
    log(self, f"Imagens serão salvas em: {self.session_dir}")

    self.start_button.config(state='disabled')
    self.cancel_button.config(state='normal')
    self.running = True
    
    self.thread = threading.Thread(
        target=lambda: run_process(self, selected_indices))
    self.thread.daemon = True
    self.thread.start()

def run_process(self, selected_indices):
    self.grbl = None
    self.cam = None

    with open("cfg.json", "r") as file:
        data = json.load(file)

    PORT = data["port"]
    BAUDRATE = data["baudrate"]

    log(self, "Iniciando comunicacao GRBL...")
    try:
        self.grbl = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        self.grbl.write(b"\r\n\r\n")
        time.sleep(2)
        self.grbl.flushInput()
        log(self, "Conectado ao GRBL na porta: " + PORT)
    except Exception as e:
        log(self, "Erro ao conectar na porta: " + str(e))
        finalize(self)
        return

    log(self, "-> Iniciando Camera...")
    self.cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    if not self.cam.isOpened():
        log(self, "-> Erro ao abrir a câmera. Verifique a conexão...")
        self.grbl.close()
        finalize(self)
        return
    else:
        log(self, "-> Camera iniciada com sucesso...")
    #define o tamanho da imagem
    self.cam.set(3, 1920)
    self.cam.set(4, 1080)
    
    
    num_plants = len(selected_indices)
    log(self, f"Processando {num_plants} plantas...")
    update_progress(self, 0, num_plants)
    send_grbl(self, '$X')
    wait_for_idle(self)
    send_grbl(self, '$H')
    wait_for_idle(self)
    send_grbl(self, '$')
    send_grbl(self, '?')
    send_grbl(self, 'G1 F14000')

    # Loop para as plantas do JSON, na ordem
    for i, plant_idx in enumerate(selected_indices):
        if not self.running:
            break
        log(self, "===============================================================")
        log(self, f'Planta {i + 1} de {num_plants} - Deslocando para ' + self.ID_PLANT[plant_idx])
        send_grbl(self, 'G1 X' + str(self.POS_X_PLANT[plant_idx]) + ' Y' + str(self.POS_Y_PLANT[plant_idx]))
        wait_for_idle(self)
        get_image(self, plant_idx)
        update_progress(self, i + 1, num_plants)

    update_progress(self, num_plants, num_plants)
    log(self, "\nConcluído!")

    # Retorna para origem SEM capturar imagem
    send_grbl(self, 'G0 X0 Y0')
    wait_for_idle(self)
    finalize(self)