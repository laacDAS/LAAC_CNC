import cv2 as cv
import serial
import time
import os
import json
import signal
import sys
from PIL import Image
import datetime
import threading
import tkinter as tk
import tkinter.messagebox as msg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import subprocess
import shutil

def configure_camera(cam, use_cfg=True):
    """
    Configura os parâmetros da câmera para captura padronizada.
    
    Parâmetros:
    - cam: objeto cv.VideoCapture
    - use_cfg: se True, carrega configurações do cfg.json
    """
    # Resolução 1080p
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Carrega configurações do cfg.json se disponível
    settings = {
        "auto_exposure": False,
        "exposure": -6,
        "auto_wb": False,
        "wb_temperature": 4500,
        "auto_focus": False,
        "focus": 100,
        "brightness": 128,
        "contrast": 128,
        "saturation": 128,
        "gain": 50
    }
    
    if use_cfg:
        try:
            with open("cfg.json", "r") as f:
                cfg_data = json.load(f)
                if "camera_settings" in cfg_data:
                    settings.update(cfg_data["camera_settings"])
        except Exception:
            pass
    
    # Aplicar configurações
    cam.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25 if not settings["auto_exposure"] else 1.0)
    cam.set(cv.CAP_PROP_EXPOSURE, settings["exposure"])
    cam.set(cv.CAP_PROP_AUTO_WB, 0 if not settings["auto_wb"] else 1)
    cam.set(cv.CAP_PROP_WB_TEMPERATURE, settings["wb_temperature"])
    cam.set(cv.CAP_PROP_AUTOFOCUS, 0 if not settings["auto_focus"] else 1)
    cam.set(cv.CAP_PROP_FOCUS, settings["focus"])
    cam.set(cv.CAP_PROP_BRIGHTNESS, settings["brightness"])
    cam.set(cv.CAP_PROP_CONTRAST, settings["contrast"])
    cam.set(cv.CAP_PROP_SATURATION, settings["saturation"])
    cam.set(cv.CAP_PROP_GAIN, settings["gain"])

def multi_images_capture():
    """
    Rotina de captura múltipla baseada em multi_images_capture.py
    """
    def signal_handler(sig, frame):
        print("\n===============================================================")
        print("Interrupção detectada (Ctrl + C). Finalizando...")
        print("\n===============================================================")
        finalize()

    def finalize():
        print("\n--- Fechando conexão... ---")
        grbl.close()
        cam.release()
        cv.destroyAllWindows()
        sys.exit(0)

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
            return None
        frame_resized = cv.resize(frame, (640, 360))
        if os.environ.get("DISPLAY"):
            cv.imshow('Imagem', frame_resized)
            cv.waitKey(30)
        # monta nome com timestamp e sequência
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        nome = dir_img + f"capture-{timestamp}-{image_number:04d}.jpg"
        cv.imwrite(nome, frame)
        return nome
    # pasta de saída padrão para captura múltipla (compatível com demais nomes do projeto)
    dir_img = "output_unitarias"
    if not os.path.exists(dir_img):
        os.makedirs(dir_img)

    with open("cfg.json", "r") as file:
        data = json.load(file)

    PORT = data["port"]
    BAUDRATE = data["baudrate"]
    ID_PLANT = [plant["id"] for plant in data["plants"]]
    POS_X_PLANT = [plant["X"] for plant in data["plants"]]
    POS_Y_PLANT = [plant["Y"] for plant in data["plants"]]

    signal.signal(signal.SIGINT, signal_handler)

    print("Iniciando comunicacao GRBL...")
    try:
        global grbl
        grbl = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        grbl.write(b"\r\n\r\n")
        time.sleep(2)
        grbl.flushInput()
        print("Conectado ao GRBL na porta:", PORT)
    except Exception:
        print("Erro ao conectar na porta:", PORT)
        exit()

    print("-> Iniciando Camera...")
    global cam
    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    if not cam.isOpened():
        print("-> Erro ao abrir a câmera. Verifique a conexão...")
        grbl.close()
        exit()
    configure_camera(cam)

    print(f"Processando 12 plantas, 10 vezes cada (120 capturas)...")
    print_progress(0, 120)
    send_grbl('$X')
    wait_for_idle()
    send_grbl('$H')
    wait_for_idle()
    send_grbl('$')
    send_grbl('?')
    wait_user('-> Iniciar Captura Automatica? ')
    send_grbl('G1 F14000')

    total_images = 120
    image_counter = 1
    for repetition in range(10):
        for plant in range(12):
            print("===============================================================")
            print(f'Repetição {repetition + 1}/10 - Planta {plant + 1}/12 - Deslocando para {ID_PLANT[plant]}')
            send_grbl('G1 X' + str(POS_X_PLANT[plant]) + ' Y' + str(POS_Y_PLANT[plant]))
            wait_for_idle()
            fname = GetImage(image_counter)
            print(f"Imagem capturada: {fname} para {ID_PLANT[plant]}")
            print_progress(image_counter, total_images)
            image_counter += 1

    print_progress(total_images, total_images)
    print("\nConcluído!")
    send_grbl('G0 X0 Y0')
    wait_for_idle()
    finalize()

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
    # Aplica rotação de 180 graus se checkbox estiver ativo na interface
    try:
        if hasattr(self, 'rotate_180_var') and self.rotate_180_var.get():
            frame = cv.rotate(frame, cv.ROTATE_180)
    except Exception:
        pass
    # Sequência por execução
    if not hasattr(self, 'image_sequence') or self.image_sequence is None:
        self.image_sequence = 0
    self.image_sequence += 1
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    nome = os.path.join(self.session_dir, f"unitaria-{timestamp}-{self.image_sequence:04d}-{self.ID_PLANT[plant_idx]}.jpg")
    # Aplica rotação se necessário (já aplicado acima in-place), salva e injeta metadata XMP/EXIF
    cv.imwrite(nome, frame)
    # Coordenadas da planta (para metadata)
    x = float(self.POS_X_PLANT[plant_idx]) if hasattr(self, 'POS_X_PLANT') else 0.0
    y = float(self.POS_Y_PLANT[plant_idx]) if hasattr(self, 'POS_Y_PLANT') else 0.0
    # Tenta gravar EXIF UserComment com X-LAT/Y-LONG e também XMP position tags
    try:
        import piexif
        pil_img = Image.open(nome)
        try:
            exif_dict = piexif.load(nome)
        except Exception:
            exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
            user_comment = f"X-LAT:{x:.2f};Y-LONG:{y:.2f}"
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = b'ASCII\x00\x00\x00' + user_comment.encode('utf-8')
        exif_bytes = piexif.dump(exif_dict)
        pil_img.save(nome, exif=exif_bytes)
        pil_img.close()
    except Exception:
        pass
    try:
        _embed_xmp_tags(nome, x, y)
    except Exception:
        pass
    log(self, f"Imagem capturada para {self.ID_PLANT[plant_idx]} em {nome}")

def start_process(self):
    if self.running:
        return

    # Sempre processa todas as plantas do JSON, na ordem
    selected_indices = list(range(len(self.ID_PLANT)))
    log(self, "Processando todas as plantas do JSON, na ordem definida.")

    # Cria pasta com data/hora
    
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    self.session_dir = os.path.join("output_unitarias", now)
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
    configure_camera(self.cam)
    
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

def captura_adensada_functions(self):
    """
    Wrapper para rotina de captura adensada, integrando logs e interface.
    """
    import threading
    # from capture_dense import captura_adensada  # Removido, função agora está em functions.py
    log(self, "Iniciando Captura Adensada...")
    def run():
        try:
            captura_adensada()
            log(self, "Captura Adensada finalizada com sucesso.")
        except Exception as e:
            log(self, f"Erro na Captura Adensada: {e}")
    t = threading.Thread(target=run, daemon=True)
    t.start()

def start_dense_process(self):
    if self.running:
        return

    log(self, "Iniciando Captura Adensada (alta sobreposição)...")
    # Cria pasta com data/hora
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    self.session_dir = os.path.join("output_dense", now)
    if not os.path.exists(self.session_dir):
        os.makedirs(self.session_dir)
    log(self, f"Imagens adensadas serão salvas em: {self.session_dir}")

    self.start_button.config(state='disabled')
    self.cancel_button.config(state='normal')
    self.running = True

    self.thread = threading.Thread(
        target=lambda: run_dense_process(self))
    self.thread.daemon = True
    self.thread.start()

def run_dense_process(self):
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
    configure_camera(self.cam)

    # Lê coordenadas do pontos.json
    try:
        with open("pontos.json", "r") as f:
            pontos = json.load(f)
    except Exception as e:
        log(self, f"Erro ao ler pontos.json: {e}")
        finalize(self)
        return

    if not isinstance(pontos, list) or not pontos:
        log(self, "Nenhuma coordenada encontrada em pontos.json!")
        finalize(self)
        return

    total_imgs = len(pontos)
    log(self, f"Capturando {total_imgs} imagens adensadas conforme pontos.json...")
    update_progress(self, 0, total_imgs)
    send_grbl(self, '$X')
    wait_for_idle(self)
    send_grbl(self, '$H')
    wait_for_idle(self)
    send_grbl(self, '$')
    send_grbl(self, '?')
    send_grbl(self, 'G1 F14000')

    img_count = 0
    for pt in pontos:
        if not self.running:
            break
        x = pt.get("X", 0.0)
        y = pt.get("Y", 0.0)
        log(self, f"Adensada {img_count+1} de {total_imgs} - X={x:.2f} Y={y:.2f}")
        send_grbl(self, f'G1 X{x:.2f} Y{y:.2f}')
        wait_for_idle(self)
        self.cam.read()
        time.sleep(0.1)
        ret, frame = self.cam.read()
        if not ret:
            log(self, f"Erro ao capturar imagem adensada {img_count+1}")
            continue
        # Rotaciona a imagem se solicitado pela interface
        try:
            if hasattr(self, 'rotate_180_var') and self.rotate_180_var.get():
                frame = cv.rotate(frame, cv.ROTATE_180)
        except Exception:
            pass
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        nome = os.path.join(self.session_dir, f"adensada-{timestamp}-{img_count+1:04d}.jpg")
        cv.imwrite(nome, frame)
        try:
            _embed_xmp_tags(nome, x, y)
        except Exception:
            pass
        # Salva coordenadas X-LAT e Y-LONG no EXIF imediatamente após a captura
        try:
            import piexif
            from PIL import Image
            pil_img = Image.open(nome)
            # Cria EXIF mínimo se não existir
            try:
                exif_dict = piexif.load(nome)
            except Exception:
                exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
            # Concatena ambos os campos no UserComment
            user_comment = f"X-LAT:{x:.2f};Y-LONG:{y:.2f}"
            # Prepend EXIF UserComment encoding marker (ASCII) for compatibility
            user_comment_bytes = b'ASCII\x00\x00\x00' + user_comment.encode('utf-8')
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = user_comment_bytes
            exif_bytes = piexif.dump(exif_dict)
            pil_img.save(nome, exif=exif_bytes)
            pil_img.close()
        except Exception as e:
            log(self, f"Não foi possível gravar EXIF X-LAT/Y-LONG: {e}")
        log(self, f"Imagem adensada salva: {nome}")
        img_count += 1
        update_progress(self, img_count, total_imgs)

    update_progress(self, img_count, total_imgs)
    log(self, "\nCaptura Adensada Concluída!")
    send_grbl(self, 'G0 X0 Y0')
    wait_for_idle(self)
    finalize(self)

def gerar_pontos_adensados(self, step_x=100, step_y=100):
    """
    Gera pontos adensados em padrão zig-zag, salva em pontos.json e mostra popup para confirmação.
    step_x: espaçamento entre pontos no eixo X (mm)
    step_y: espaçamento entre pontos no eixo Y (mm)
    """
    width = 900
    length = 2000
    points = []
    pid = 1
    xs = list(range(0, width + 1, step_x))
    ys = list(range(0, length + 1, step_y))
    for xi, x in enumerate(xs):
        linha = []
        # Inverte o início em Y para começar pelo lado maior (length)
        # Alterna a direção a cada coluna para criar o padrão zigue-zague
        y_iter = ys[::-1] if xi % 2 == 0 else ys
        for y in y_iter:
            linha.append({
                "id": pid,
                "X": float(-x),
                "Y": float(-y)
            })
            pid += 1
        points.extend(linha)
    # Visualização: quadrado de borda preta e 'x' azul dentro
    fig, ax = plt.subplots(figsize=(5, 10))
    for p in points:
        x = -p['X']
        y = -p['Y']
        # Quadrado de borda preta
        rect = patches.Rectangle(
            (x - 50, y - 50), 100, 100,
            linewidth=2, edgecolor='black', facecolor='none', alpha=1.0
        )
        ax.add_patch(rect)
        # 'X' azul
        ax.plot([x - 40, x + 40], [y - 40, y + 40], color='blue', linewidth=2)
        ax.plot([x - 40, x + 40], [y + 40, y - 40], color='blue', linewidth=2)
    ax.set_xlim(-50, width + 50)
    ax.set_ylim(-50, length + 50)
    ax.set_aspect('auto')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(f'Visualização dos Pontos Adensados ({len(points)} pontos, passo X={step_x}mm Y={step_y}mm)')
    plt.tight_layout()
    plt.show()
    confirm = msg.askyesno("Confirmação de Grade", f"Grade de pontos gerada com passo X={step_x}mm e Y={step_y}mm.\n\nA visualização foi exibida.\n\nDeseja salvar pontos.json?")
    if confirm:
        with open("pontos.json", "w") as f:
            json.dump(points, f, indent=4)
        msg.showinfo("Pontos Gerados", f"{len(points)} pontos salvos em pontos.json.")
    else:
        msg.showinfo("Cancelado", "Geração de pontos cancelada.")
def criar_interface_gerar_pontos(self):
    """
    Adiciona botão e entrada para gerar pontos adensados na interface principal.
    """
    from tkinter import ttk
    frame = tk.Frame(self.root)
    frame.pack(pady=10)
    tk.Label(frame, text="Passo X (mm):").pack(side=tk.LEFT)
    passo_x_entry = tk.Entry(frame, width=5)
    passo_x_entry.insert(0, "100")
    passo_x_entry.pack(side=tk.LEFT)
    tk.Label(frame, text="Passo Y (mm):").pack(side=tk.LEFT, padx=(8,0))
    passo_y_entry = tk.Entry(frame, width=5)
    passo_y_entry.insert(0, "100")
    passo_y_entry.pack(side=tk.LEFT)
    def on_gerar():
        try:
            step_x = int(passo_x_entry.get())
        except Exception:
            step_x = 100
        try:
            step_y = int(passo_y_entry.get())
        except Exception:
            step_y = 100
        gerar_pontos_adensados(self, step_x=step_x, step_y=step_y)
    btn = ttk.Button(frame, text="Gerar Pontos Adensados", command=on_gerar)
    btn.pack(side=tk.LEFT)
    
    # Botão de calibração de câmera
    btn_calibrar = ttk.Button(frame, text="Calibrar Câmera", command=lambda: abrir_calibracao_camera(self))
    btn_calibrar.pack(side=tk.LEFT, padx=(10, 0))

def abrir_calibracao_camera(self):
    """
    Abre janela de calibração de câmera com sliders para todos os parâmetros.
    """
    from tkinter import ttk, Scale
    from PIL import Image, ImageTk
    import threading
    import time
    
    # Carrega configurações atuais
    try:
        with open("cfg.json", "r") as f:
            cfg_data = json.load(f)
            camera_settings = cfg_data.get("camera_settings", {})
    except Exception:
        camera_settings = {}
    
    # Valores padrão
    defaults = {
        "auto_exposure": False,
        "exposure": -6,
        "auto_wb": False,
        "wb_temperature": 4500,
        "auto_focus": False,
        "focus": 100,
        "brightness": 128,
        "contrast": 128,
        "saturation": 128,
        "gain": 50
    }
    
    for key, val in defaults.items():
        if key not in camera_settings:
            camera_settings[key] = val
    
    # Cria janela de calibração
    calibration_window = tk.Toplevel(self.root)
    calibration_window.title("Calibração de Câmera")
    calibration_window.geometry("1200x700")
    
    # Frame esquerdo para sliders
    left_frame = ttk.Frame(calibration_window)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)
    
    ttk.Label(left_frame, text="Parâmetros da Câmera", font=("Arial", 12, "bold")).pack()
    
    # Dicionário para armazenar valores dos sliders
    slider_values = {}
    auto_flags = {}
    
    # Configuração dos parâmetros
    params = [
        ("exposure", "Exposure", -13, 0, -6),
        ("wb_temperature", "White Balance (K)", 2500, 6500, 4500),
        ("focus", "Focus", 0, 255, 100),
        ("brightness", "Brightness", 0, 255, 128),
        ("contrast", "Contrast", 0, 255, 128),
        ("saturation", "Saturation", 0, 255, 128),
        ("gain", "Gain", 0, 100, 50),
    ]
    
    # Lista para rastrear threads de atualização
    update_threads = {"preview": None}
    stop_preview = {"flag": False}
    
    for param_key, label, min_val, max_val, default_val in params:
        param_frame = ttk.Frame(left_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text=label, width=20).pack(side=tk.LEFT)
        
        # Slider
        slider_var = tk.DoubleVar(value=camera_settings.get(param_key, default_val))
        slider_values[param_key] = slider_var
        slider = Scale(param_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, 
                      variable=slider_var, length=250)
        slider.pack(side=tk.LEFT, padx=5)
        
        # Valor exibido
        value_label = ttk.Label(param_frame, text=str(int(slider_var.get())), width=5)
        value_label.pack(side=tk.LEFT, padx=5)
        
        def update_label(val, label_widget=value_label):
            label_widget.config(text=str(int(float(val))))
        
        slider.config(command=update_label)
    
    # Parâmetros com botão Auto
    auto_params = [
        ("auto_exposure", "Auto Exposure", "exposure"),
        ("auto_wb", "Auto White Balance", "wb_temperature"),
        ("auto_focus", "Auto Focus", "focus"),
    ]
    
    auto_frame = ttk.LabelFrame(left_frame, text="Modo Automático", padding=10)
    auto_frame.pack(fill=tk.X, pady=10)
    
    for auto_key, label, linked_param in auto_params:
        checkbox_var = tk.BooleanVar(value=camera_settings.get(auto_key, False))
        auto_flags[auto_key] = checkbox_var
        checkbox = ttk.Checkbutton(auto_frame, text=label, variable=checkbox_var)
        checkbox.pack(anchor=tk.W)
    
    # Frame direito para preview
    right_frame = ttk.Frame(calibration_window)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(right_frame, text="Preview da Câmera", font=("Arial", 12, "bold")).pack()
    
    canvas = tk.Canvas(right_frame, width=480, height=360, bg="black")
    canvas.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Variáveis para armazenar foto
    current_image = {"pil": None, "tk": None}
    
    def apply_camera_settings():
        """Aplica as configurações atuais da câmera"""
        try:
            cam = cv.VideoCapture(0, cv.CAP_DSHOW)
            if cam.isOpened():
                cam.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
                cam.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
                
                # Aplicar auto flags
                cam.set(cv.CAP_PROP_AUTO_EXPOSURE, 1.0 if auto_flags["auto_exposure"].get() else 0.25)
                cam.set(cv.CAP_PROP_AUTO_WB, 1 if auto_flags["auto_wb"].get() else 0)
                cam.set(cv.CAP_PROP_AUTOFOCUS, 1 if auto_flags["auto_focus"].get() else 0)
                
                # Aplicar sliders
                cam.set(cv.CAP_PROP_EXPOSURE, int(slider_values["exposure"].get()))
                cam.set(cv.CAP_PROP_WB_TEMPERATURE, int(slider_values["wb_temperature"].get()))
                cam.set(cv.CAP_PROP_FOCUS, int(slider_values["focus"].get()))
                cam.set(cv.CAP_PROP_BRIGHTNESS, int(slider_values["brightness"].get()))
                cam.set(cv.CAP_PROP_CONTRAST, int(slider_values["contrast"].get()))
                cam.set(cv.CAP_PROP_SATURATION, int(slider_values["saturation"].get()))
                cam.set(cv.CAP_PROP_GAIN, int(slider_values["gain"].get()))
                
                return cam
        except Exception as e:
            print(f"Erro ao aplicar configurações: {e}")
        return None
    
    def update_preview():
        """Atualiza a preview da câmera em tempo real"""
        cam = apply_camera_settings()
        if not cam:
            return
        
        try:
            while not stop_preview["flag"]:
                ret, frame = cam.read()
                if ret:
                    # Redimensionar para caber no canvas
                    frame = cv.resize(frame, (480, 360))
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    
                    pil_image = Image.fromarray(frame)
                    current_image["pil"] = pil_image
                    current_image["tk"] = ImageTk.PhotoImage(pil_image)
                    
                    canvas.create_image(0, 0, image=current_image["tk"], anchor=tk.NW)
                
                time.sleep(0.1)
        except Exception as e:
            print(f"Erro na atualização da preview: {e}")
        finally:
            cam.release()
    
    def start_preview():
        """Inicia a thread de preview"""
        stop_preview["flag"] = False
        if update_threads["preview"] is None or not update_threads["preview"].is_alive():
            update_threads["preview"] = threading.Thread(target=update_preview, daemon=True)
            update_threads["preview"].start()
    
    def stop_preview_thread():
        """Para a thread de preview"""
        stop_preview["flag"] = True
        if update_threads["preview"]:
            update_threads["preview"].join(timeout=1)
    
    def save_settings():
        """Salva as configurações no cfg.json"""
        try:
            with open("cfg.json", "r") as f:
                cfg_data = json.load(f)
            
            cfg_data["camera_settings"] = {
                "auto_exposure": auto_flags["auto_exposure"].get(),
                "exposure": int(slider_values["exposure"].get()),
                "auto_wb": auto_flags["auto_wb"].get(),
                "wb_temperature": int(slider_values["wb_temperature"].get()),
                "auto_focus": auto_flags["auto_focus"].get(),
                "focus": int(slider_values["focus"].get()),
                "brightness": int(slider_values["brightness"].get()),
                "contrast": int(slider_values["contrast"].get()),
                "saturation": int(slider_values["saturation"].get()),
                "gain": int(slider_values["gain"].get()),
            }
            
            with open("cfg.json", "w") as f:
                json.dump(cfg_data, f, indent=4)
            
            msg.showinfo("Sucesso", "Configurações de câmera salvas com sucesso!")
        except Exception as e:
            msg.showerror("Erro", f"Erro ao salvar configurações: {e}")
    
    # Frame para botões
    button_frame = ttk.Frame(calibration_window)
    button_frame.pack(fill=tk.X, pady=10, padx=10)
    
    ttk.Button(button_frame, text="Salvar Configurações", command=save_settings).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Fechar", command=lambda: [stop_preview_thread(), calibration_window.destroy()]).pack(side=tk.LEFT, padx=5)
    
    # Inicia preview ao abrir a janela
    start_preview()
    
    # Para preview ao fechar a janela
    def on_closing():
        stop_preview_thread()
        calibration_window.destroy()
    
    calibration_window.protocol("WM_DELETE_WINDOW", on_closing)

# --- Classes utilitárias (de camera.py e cnc_controller.py) ---
class Camera:
    def get_field_of_view_mm(self):
        """Retorna o campo de visão da câmera em mm."""
        return 10.0  # valor exemplo

    def get_num_capturas_x(self):
        """Retorna o número de capturas na linha (exemplo fixo)."""
        return 10

    def get_dpi(self):
        """Retorna o DPI da imagem capturada."""
        return 300

    def capturar_imagem(self):
        """Captura e retorna uma imagem PIL.Image (stub: imagem branca)."""
        return Image.new('RGB', (1024, 768), color='white')

class CNCController:
    def initialize(self):
        """Inicializa a CNC."""
        pass

    def unlock(self):
        """Desbloqueia a CNC."""
        pass

    def home(self):
        """Executa o homing da CNC."""
        pass

    def mover_para(self, x, y):
        """Move a CNC para a posição (x, y)."""
        pass

    def return_to_origin(self):
        """Retorna a CNC à posição de origem."""
        pass

# --- Funções de captura adensada (de capture_dense.py) ---
import logging
import piexif
from pathlib import Path

def _embed_xmp_tags(jpeg_path, x, y):
    """
    Tenta adicionar tags XMP customizadas 'position-x' e 'position-y'.
    Primeiro tenta usar pyexiv2; se não disponível, injeta manualmente um bloco APP1 XMP.
    """
    try:
        import pyexiv2
        # Prefer ImageMetadata API if available
        try:
            meta = pyexiv2.ImageMetadata(jpeg_path)
            meta.read()
            # Try to write XMP fields directly
            try:
                meta['Xmp.laac.position-x'] = str(x)
                meta['Xmp.laac.position-y'] = str(y)
                meta.write()
                return
            except Exception:
                # Some pyexiv2 builds accept direct assignment differently; try lower-level XMP tag
                try:
                    from pyexiv2.xmp import XmpTag
                    meta['Xmp.laac.position-x'] = XmpTag('Xmp.laac.position-x', str(x))
                    meta['Xmp.laac.position-y'] = XmpTag('Xmp.laac.position-y', str(y))
                    meta.write()
                    return
                except Exception:
                    pass
        except Exception:
            # Older pyexiv2 API fallback
            try:
                img = pyexiv2.Image(jpeg_path)
                xmp_keys = {
                    'Xmp.laac.position-x': str(x),
                    'Xmp.laac.position-y': str(y)
                }
                img.modify_xmp(xmp_keys)
                img.close()
                return
            except Exception:
                pass
    except Exception:
        pass

    try:
        # Monta pacote XMP mínimo (RDF) com namespace laac
        xmp_xml = (
            '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>'
            '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description xmlns:laac="http://ns.laac.ufv/1.0/" '
            'laac:position-x="{xval}" laac:position-y="{yval}" />'
            '</rdf:RDF></x:xmpmeta><?xpacket end="w"?>'
        ).format(xval=str(x), yval=str(y))

        xmp_header = b"http://ns.adobe.com/xap/1.0/\x00"
        xmp_bytes = xmp_xml.encode('utf-8')
        app1_payload = xmp_header + xmp_bytes
        # Comprimento do segmento APP1 = payload + 2 bytes do tamanho
        seg_len = len(app1_payload) + 2
        if seg_len > 0xFFFF:
            return

        marker = b'\xff\xe1' + seg_len.to_bytes(2, byteorder='big') + app1_payload

        # Lê arquivo JPEG e injeta após o SOI (0xFFD8)
        with open(jpeg_path, 'rb') as f:
            data = f.read()
        if data[0:2] != b'\xff\xd8':
            return
        # Evita duplicar blocos XMP: se já existir header XMP, substitui (simplesmente insere)
        new_data = data[0:2] + marker + data[2:]
        with open(jpeg_path, 'wb') as f:
            f.write(new_data)
    except Exception:
        return
    return False

def salvar_imagem_com_exif(img, filepath, filename, dpi, x, y):
    """
    Salva a imagem com metadados EXIF personalizados.
    """
    # Formato customizado: X-LAT e Y-LONG no UserComment
    user_comment = f"X-LAT:{x};Y-LONG:{y}"
    user_comment_bytes = b'ASCII\x00\x00\x00' + user_comment.encode('utf-8')
    exif_dict = {
        "0th": {
            piexif.ImageIFD.ImageDescription: filename.encode(),
            piexif.ImageIFD.XResolution: (dpi, 1),
            piexif.ImageIFD.YResolution: (dpi, 1),
        },
        "Exif": {
            piexif.ExifIFD.UserComment: user_comment_bytes
        }
    }
    exif_bytes = piexif.dump(exif_dict)
    img.save(filepath, "jpeg", exif=exif_bytes)
    # Also embed XMP tags position-x / position-y for tools like exiftool to show separate fields
    try:
        _embed_xmp_tags(str(filepath), x, y)
    except Exception:
        pass

def captura_adensada():
    """
    Executa a rotina de captura adensada:
    1. Inicializa e desbloqueia CNC
    2. Executa homing
    3. Realiza capturas com alta sobreposição
    4. Retorna CNC à origem
    """
    try:
        # Inicialização dos módulos
        cnc = CNCController()
        camera = Camera()

        logging.info("[Captura Adensada] Inicializando CNC...")
        cnc.initialize()
        cnc.unlock()
        cnc.home()

        # Pasta de destino
        output_dir = Path("output_dense")
        output_dir.mkdir(exist_ok=True)

        # Parâmetros de captura
        field_of_view_mm = camera.get_field_of_view_mm()  # Ex: 10mm
        step_mm = field_of_view_mm * 0.1  # 90% sobreposição
        n_capturas = camera.get_num_capturas_x()
        dpi = camera.get_dpi()

        x, y = 0.0, 0.0
        for i in range(n_capturas):
            # Mover CNC
            cnc.mover_para(x, y)
            # Capturar imagem
            img = camera.capturar_imagem()
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            filename = f"adensada-{timestamp}-{i+1:04d}.jpg"
            filepath = output_dir / filename
            # Salvar imagem com EXIF and embed XMP
            salvar_imagem_com_exif(img, filepath, filename, dpi, x, y)
            logging.info(f"Imagem salva: {filepath} (X={x}, Y={y})")
            # Próxima posição
            x += step_mm
        # Retornar à origem
        cnc.return_to_origin()
        logging.info("[Captura Adensada] Finalizada com sucesso.")
    except Exception as e:
        logging.error(f"Erro na captura adensada: {e}")