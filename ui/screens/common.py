import os

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from iconipy import IconFactory

from ui.theme import CORES


__all__ = [
    "_icone",
    "_exibir_frame",
    "_layout_responsivo_duplo",
    "_layout_responsivo_inicio",
    "_carregar_logo",
    "_sem_sala_label",
    "COR_SUCESSO",
    "COR_ALERTA",
    "COR_ERRO",
    "COR_NEUTRA",
    "COR_TEXTO",
    "COR_FUNDO",
    "COR_PAINEL",
    "COR_LISTA",
    "COR_SELECAO",
    "COR_HOVER",
]


icon_factory = IconFactory(icon_set="lucide", icon_size=22, font_color="white")


def _icone(nome, tamanho=22):
    imagem = icon_factory.asPil(nome)
    return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(tamanho, tamanho))


def _exibir_frame(video_label, frame):
    video_label.frame_atual = frame
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagem = Image.fromarray(frame_rgb)
    largura = max(video_label.winfo_width() - 20, 320)
    altura = max(video_label.winfo_height() - 20, 240)
    imagem.thumbnail((largura, altura), Image.Resampling.LANCZOS)
    imagem_tk = ImageTk.PhotoImage(image=imagem)
    video_label.imgtk = imagem_tk
    video_label.configure(image=imagem_tk)


def _layout_responsivo_duplo(tela, video_label, painel):
    """Empilha câmera e formulário quando a área útil fica estreita."""
    estado_anterior = None

    def ajustar(event=None):
        nonlocal estado_anterior
        estreito = tela.winfo_width() < 800
        if estreito == estado_anterior:
            return
        estado_anterior = estreito

        if estreito:
            tela.grid_columnconfigure(0, weight=1)
            tela.grid_columnconfigure(1, weight=0)
            tela.grid_rowconfigure(2, weight=0)
            tela.grid_rowconfigure(3, weight=1)
            video_label.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
            painel.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        else:
            tela.grid_columnconfigure(0, weight=1)
            tela.grid_columnconfigure(1, weight=1)
            tela.grid_rowconfigure(2, weight=1)
            tela.grid_rowconfigure(3, weight=0)
            video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")
            painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        tela.after_idle(lambda: _exibir_frame(video_label, video_label.frame_atual)
                if hasattr(video_label, "frame_atual") else None)

    tela.bind("<Configure>", ajustar)
    tela.after_idle(ajustar)


def _layout_responsivo_inicio(tela, cards, titulo_acoes, acoes):
    estado_anterior = None

    def ajustar(event=None):
        nonlocal estado_anterior
        estreito = tela.winfo_width() < 800
        if estreito == estado_anterior:
            return
        estado_anterior = estreito

        if estreito:
            for indice, card in enumerate(cards):
                card.grid(row=2 + indice, column=0, padx=30, pady=6, sticky="ew")
            titulo_acoes.grid(row=5, column=0, columnspan=1, padx=30, pady=(30, 10), sticky="w")
            for indice, acao in enumerate(acoes):
                acao.grid(row=6 + indice, column=0, padx=30, pady=6, sticky="ew")
        else:
            for indice, card in enumerate(cards):
                margem_esquerda = 30 if indice == 0 else 10
                margem_direita = 30 if indice == 2 else 10
                card.grid(row=2, column=indice, padx=(margem_esquerda, margem_direita), pady=6, sticky="ew")
            titulo_acoes.grid(row=3, column=0, columnspan=3, padx=30, pady=(30, 10), sticky="w")
            margens = [(30, 10), (10, 10), (10, 30)]
            for indice, acao in enumerate(acoes):
                acao.grid(row=4, column=indice, padx=margens[indice], pady=6, sticky="ew")

    tela.bind("<Configure>", ajustar)
    tela.after_idle(ajustar)


def _carregar_logo(caminho, tamanho=(180, 90)):
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        imagem = Image.open(caminho)
        return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=tamanho)
    except (OSError, ValueError):
        return None


def _sem_sala_label(cfg):
    return f"Todas as {cfg.get('termo_sala', 'Turma')}s"


COR_SUCESSO = CORES["sucesso"]
COR_ALERTA = CORES["alerta"]
COR_ERRO = CORES["erro"]
COR_NEUTRA = CORES["neutra"]
COR_TEXTO = CORES["texto"]
COR_FUNDO = CORES["fundo"]
COR_PAINEL = CORES["painel"]
COR_LISTA = CORES["painel_secundario"]
COR_SELECAO = CORES["selecao"]
COR_HOVER = CORES["hover"]