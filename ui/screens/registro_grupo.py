import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaRegistroGrupo(ctk.CTkFrame):
    PROCESSAR_A_CADA_N_FRAMES = 15

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.sessao_ativa = False
        self.frame_count = 0
        self.registrados_na_sessao = set()
        self._montar()

    def _montar(self):
        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Chamada em Grupo", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Reconhecimento contínuo — cada pessoa é registrada automaticamente uma vez.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")

        painel = criar_painel(self)
        painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        ctk.CTkLabel(painel, text=f"{termo_sala} desta chamada", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        salas_disponiveis = core.carregar_salas() or [""]
        self.combo_sala = ctk.CTkOptionMenu(painel, values=salas_disponiveis)
        self.combo_sala.pack(fill="x", padx=20)

        self.btn_iniciar = ctk.CTkButton(painel, text="Iniciar chamada", image=_icone("play"), compound="left", height=44,
                                          fg_color=COR_SELECAO, hover_color=COR_HOVER,
                                          command=self._alternar_sessao)
        self.btn_iniciar.pack(fill="x", padx=20, pady=(16, 10))

        self.label_status = ctk.CTkLabel(painel, text="Sessão parada.", font=ctk.CTkFont(size=15, weight="bold"))
        self.label_status.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(painel, text="Presentes nesta sessão:", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(10, 4))

        self.lista_presentes = ctk.CTkTextbox(painel, height=240)
        self.lista_presentes.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.lista_presentes.configure(state="disabled")

    def _alternar_sessao(self):
        if not self.sessao_ativa:
            self.sessao_ativa = True
            self.registrados_na_sessao = set()
            self._atualizar_lista()
            self.app.iniciar_camera()
            self.combo_sala.configure(state="disabled")
            self.btn_iniciar.configure(text="Encerrar chamada", image=_icone("square"), fg_color=COR_ERRO, hover_color=COR_HOVER)
            self.label_status.configure(text="Sessão em andamento...", text_color=COR_SUCESSO)
            self._loop_reconhecimento()
        else:
            self.sessao_ativa = False
            self.app.parar_camera()
            self.combo_sala.configure(state="normal")
            self.btn_iniciar.configure(text="Iniciar chamada", image=_icone("play"), fg_color=COR_SELECAO, hover_color=COR_HOVER)
            self.label_status.configure(
                text=f"Sessão encerrada. Total: {len(self.registrados_na_sessao)} pessoa(s).",
                text_color=COR_NEUTRA
            )

    def _loop_reconhecimento(self):
        if not self.sessao_ativa:
            return

        frame = self.app.ler_frame()
        if frame is not None:
            self.frame_count += 1
            self._exibir_frame(frame)

            if self.frame_count % self.PROCESSAR_A_CADA_N_FRAMES == 0:
                nome = core.identificar_pessoa(frame, exigir_rosto=False)
                if nome and nome not in self.registrados_na_sessao:
                    sala = self.combo_sala.get().strip()
                    core.registrar_presenca(nome, tipo="Chamada em grupo", sala=sala)
                    self.registrados_na_sessao.add(nome)
                    self._atualizar_lista()

        self.after(30, self._loop_reconhecimento)

    def _atualizar_lista(self):
        self.lista_presentes.configure(state="normal")
        self.lista_presentes.delete("1.0", "end")
        for nome in sorted(self.registrados_na_sessao):
            self.lista_presentes.insert("end", f"✔ {nome}\n")
        self.lista_presentes.configure(state="disabled")

    def _exibir_frame(self, frame):
        _exibir_frame(self.video_label, frame)

    def destroy(self):
        self.sessao_ativa = False
        super().destroy()


# ==========================================================================
# Tela: Relatórios (com filtros por sala/data e presença x falta)
# ==========================================================================


