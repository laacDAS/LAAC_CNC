"""
Módulo responsável pela rotina de Captura Adensada.
"""
import os
from pathlib import Path
from cnc_controller import CNCController
from camera import Camera
from PIL import Image
import piexif
import logging


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
        output_dir = Path("Fotos Adensadas")
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
            filename = f"imagem_{i+1:03d}.jpg"
            filepath = output_dir / filename
            # Salvar imagem com EXIF
            salvar_imagem_com_exif(img, filepath, filename, dpi, x, y)
            logging.info(f"Imagem salva: {filepath} (X={x}, Y={y})")
            # Próxima posição
            x += step_mm
        # Retornar à origem
        cnc.return_to_origin()
        logging.info("[Captura Adensada] Finalizada com sucesso.")
    except Exception as e:
        logging.error(f"Erro na captura adensada: {e}")


def salvar_imagem_com_exif(img, filepath, filename, dpi, x, y):
    """
    Salva a imagem com metadados EXIF personalizados.
    """
    exif_dict = {
        "0th": {
            piexif.ImageIFD.ImageDescription: filename.encode(),
            piexif.ImageIFD.XResolution: (dpi, 1),
            piexif.ImageIFD.YResolution: (dpi, 1),
        },
        "Exif": {
            piexif.ExifIFD.UserComment: f"X={x}, Y={y}".encode()
        }
    }
    exif_bytes = piexif.dump(exif_dict)
    img.save(filepath, "jpeg", exif=exif_bytes)
