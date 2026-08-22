"""Componentes visuais reutilizáveis da interface CustomTkinter."""

import customtkinter as ctk

from .theme import ALTURA_BOTAO, CORES, FONTES, RAIO_PAINEL


def fonte(nome):
    tamanho, peso = FONTES[nome]
    kwargs = {"size": tamanho}
    if peso:
        kwargs["weight"] = peso
    return ctk.CTkFont(**kwargs)


def painel(parent, **kwargs):
    opcoes = {
        "fg_color": CORES["painel"],
        "corner_radius": RAIO_PAINEL,
    }
    opcoes.update(kwargs)
    return ctk.CTkFrame(parent, **opcoes)


def botao(parent, texto, comando, icone=None, variante="padrao", **kwargs):
    opcoes = {
        "text": texto,
        "command": comando,
        "height": ALTURA_BOTAO,
        "font": fonte("botao"),
    }
    if icone:
        opcoes["image"] = icone
        opcoes["compound"] = "left"
    if variante == "transparente":
        opcoes.update(fg_color="transparent", hover_color=CORES["hover"])
    elif variante == "sucesso":
        opcoes.update(fg_color=CORES["sucesso"], hover_color="#237a3d")
    opcoes.update(kwargs)
    return ctk.CTkButton(parent, **opcoes)