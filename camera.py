"""
Stub da câmera para integração com a rotina de captura adensada.
"""
from PIL import Image


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
