import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *
from .cadastro import TelaCadastro
from .registro_grupo import TelaRegistroGrupo
from .relatorios import TelaRelatorios

class TelaInicio(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        self.grid_columnconfigure((0, 1, 2), weight=1)

        cfg = self.app.config_dados

        cabecalho = ctk.CTkLabel(
            self, text=f"Bem-vindo, {cfg['nome_organizacao']}",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        cabecalho.grid(row=0, column=0, columnspan=3, padx=30, pady=(30, 4), sticky="w")

        sub = ctk.CTkLabel(
            self, text="Painel geral do sistema de reconhecimento facial.",
            font=ctk.CTkFont(size=14), text_color=COR_NEUTRA
        )
        sub.grid(row=1, column=0, columnspan=3, padx=30, pady=(0, 24), sticky="w")

        pessoas = core.listar_pessoas_cadastradas()
        registros = core.ler_registros()
        salas = core.carregar_salas()

        self._card(0, "Pessoas cadastradas", str(len(pessoas)), COR_SELECAO)
        self._card(1, "Registros no total", str(len(registros)), COR_SUCESSO)
        self._card(2, f"{cfg.get('termo_sala', 'Turma')}s cadastradas", str(len(salas)), COR_ALERTA)

        acoes_label = ctk.CTkLabel(self, text="Ações rápidas", font=ctk.CTkFont(size=16, weight="bold"))
        acoes_label.grid(row=3, column=0, columnspan=3, padx=30, pady=(30, 10), sticky="w")

        botao(self, "Cadastrar nova pessoa", lambda: self.app.mostrar_tela(TelaCadastro),
              icone=_icone("user-plus")).grid(row=4, column=0, padx=(30, 10), pady=6, sticky="ew")

        botao(self, "Iniciar chamada em grupo", lambda: self.app.mostrar_tela(TelaRegistroGrupo),
              icone=_icone("users")).grid(row=4, column=1, padx=10, pady=6, sticky="ew")

        botao(self, "Ver relatórios", lambda: self.app.mostrar_tela(TelaRelatorios),
              icone=_icone("chart-no-axes-column")).grid(row=4, column=2, padx=(10, 30), pady=6, sticky="ew")

    def _card(self, coluna, titulo, valor, cor):
        card = criar_painel(self)
        card.grid(row=2, column=coluna, padx=(30 if coluna == 0 else 10, 30 if coluna == 2 else 10),
                  pady=6, sticky="ew")
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=13), text_color=COR_NEUTRA
                     ).pack(anchor="w", padx=18, pady=(16, 0))
        ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=28, weight="bold"), text_color=cor
                     ).pack(anchor="w", padx=18, pady=(0, 16))


# ==========================================================================
# Tela: Cadastro de pessoa
# ==========================================================================


