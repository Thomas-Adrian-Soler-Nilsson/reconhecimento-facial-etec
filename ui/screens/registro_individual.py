import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaRegistroIndividual(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()
        self.app.iniciar_camera()
        self._atualizar_frame()

    def _montar(self):
        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Registrar Presença", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Posicione o rosto na câmera e clique em Registrar.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")

        painel = criar_painel(self)
        painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        ctk.CTkLabel(painel, text=f"{termo_sala} (opcional)", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        salas_disponiveis = [""] + core.carregar_salas()
        self.combo_sala = ctk.CTkOptionMenu(painel, values=salas_disponiveis or [""])
        self.combo_sala.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Tipo de registro", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.combo_tipo = ctk.CTkOptionMenu(painel, values=["Entrada", "Saída"])
        self.combo_tipo.pack(fill="x", padx=20)

        self.btn_registrar = ctk.CTkButton(painel, text="Registrar presença", image=_icone("circle-check"), compound="left", height=44,
                                            command=self._registrar)
        self.btn_registrar.pack(fill="x", padx=20, pady=(20, 8))

        self.label_status = ctk.CTkLabel(painel, text="", wraplength=260, justify="left",
                                          font=ctk.CTkFont(size=15, weight="bold"))
        self.label_status.pack(anchor="w", padx=20, pady=(10, 20))

    def _registrar(self):
        frame = self.app.ler_frame()
        if frame is None:
            self.label_status.configure(text="Câmera indisponível.", text_color=COR_ERRO)
            return

        self.label_status.configure(text="Identificando...", text_color=COR_NEUTRA)
        self.update_idletasks()

        nome = core.identificar_pessoa(frame, exigir_rosto=True)
        minutos = self.app.config_dados.get("minutos_entre_registros", 5)
        sala = self.combo_sala.get().strip()

        if nome is None:
            self.label_status.configure(text="Rosto não reconhecido.", text_color=COR_ERRO)
        elif core.ja_registrado_recentemente(nome, minutos, sala=sala or None):
            self.label_status.configure(text=f"{nome} já registrado recentemente.", text_color=COR_ALERTA)
        else:
            core.registrar_presenca(nome, tipo=self.combo_tipo.get(), sala=sala)
            self.label_status.configure(text=f"Presença registrada: {nome}", text_color=COR_SUCESSO)

    def _atualizar_frame(self):
        frame = self.app.ler_frame()
        if frame is not None:
            self._exibir_frame(frame)
        self.after(30, self._atualizar_frame)

    def _exibir_frame(self, frame):
        _exibir_frame(self.video_label, frame)


# ==========================================================================
# Tela: Chamada em grupo (reconhecimento contínuo)
# ==========================================================================


