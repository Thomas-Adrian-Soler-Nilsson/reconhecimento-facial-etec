"""Tokens visuais compartilhados pela interface."""

import customtkinter as ctk

CORES = {
    "sucesso": ("#2fa84f", "#55c96b"),
    "alerta": ("#a66f00", "#e7b34c"),
    "erro": ("#c0392b", "#e05a4f"),
    "neutra": ("#303235", "#b7b7b7"),
    "texto": ("#202124", "#f2f2f2"),
    "fundo": ("#ffffff", "#181818"),
    "sidebar": ("#4c4c4c", "#222222"),
    "painel": ("#f4f4f4", "#282828"),
    "painel_secundario": ("#e9e9e9", "#202020"),
    "selecao": ("#b5122b", "#c92540"),
    "hover": ("#8f0e21", "#a91b32"),
}

FONTES = {
    "titulo": (26, "bold"),
    "secao": (16, "bold"),
    "subtitulo": (14, None),
    "corpo": (13, None),
    "botao": (14, None),
}

RAIO_PAINEL = 12
ALTURA_BOTAO = 44


def configurar_tema(modo="Claro"):
    """Configura o tema escolhido e a paleta vermelha padrão dos widgets."""
    ctk.set_appearance_mode("dark" if modo == "Escuro" else "light")
    ctk.set_default_color_theme("blue")

    tema = ctk.ThemeManager.theme
    tema["CTkButton"].update(
        fg_color=CORES["selecao"],
        hover_color=CORES["hover"],
        text_color="#ffffff",
    )
    tema["CTkOptionMenu"].update(
        fg_color=CORES["selecao"],
        button_color=CORES["hover"],
        button_hover_color="#750a1a",
        text_color="#ffffff",
    )
    tema["CTkLabel"].update(text_color=CORES["texto"])
    tema["CTkEntry"].update(text_color=CORES["texto"])
    tema["CTkTextbox"].update(text_color=CORES["texto"])