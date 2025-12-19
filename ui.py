"""
Integração do botão 'Captura Adensada' à interface Tkinter existente.
"""

from tkinter import ttk
import threading
from capture_dense import captura_adensada


def adicionar_botao_captura_adensada(app):
    """
    Adiciona o botão 'Captura Adensada' na interface principal.
    """
    btn = ttk.Button(
        app.button_frame,
        text="Captura Adensada",
        command=lambda: threading.Thread(
            target=captura_adensada, daemon=True).start()
    )
    btn.pack(side='left', padx=5)
    return btn
