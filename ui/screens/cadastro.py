import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaCadastro(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.fotos_tiradas = 0
        self._montar()
        self.app.iniciar_camera()
        self._atualizar_frame()

    def _montar(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        ctk.CTkLabel(self, text="Cadastrar Pessoa", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Tire de 3 a 5 fotos variando ângulo e expressão para melhor precisão.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

        formulario = criar_painel(self)
        formulario.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        ctk.CTkLabel(formulario, text="Nome completo", font=ctk.CTkFont(size=13)
                 ).pack(anchor="w", padx=20, pady=(20, 4))
        self.entry_nome = ctk.CTkEntry(formulario, placeholder_text="Ex: Thomas Adrian", height=38)
        self.entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(formulario, text=f"Nome da {termo_sala} (opcional)", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        salas_disponiveis = ["Nenhuma"] + core.carregar_salas()
        self.combo_sala = ctk.CTkOptionMenu(formulario, values=salas_disponiveis or [""])
        self.combo_sala.pack(fill="x", padx=20)

        ctk.CTkLabel(formulario, text="RA / Matrícula (opcional)", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.entry_ra = ctk.CTkEntry(formulario, height=38)
        self.entry_ra.pack(fill="x", padx=20)

        self.btn_capturar = ctk.CTkButton(formulario, text="Capturar foto", image=_icone("camera"), compound="left", height=42,
                                           command=self._capturar_foto)
        self.btn_capturar.pack(fill="x", padx=20, pady=(20, 8))

        self.label_contagem = ctk.CTkLabel(formulario, text="Fotos tiradas nesta sessão: 0",
                                            text_color=COR_NEUTRA)
        self.label_contagem.pack(anchor="w", padx=20, pady=(0, 20))

        self.label_status = ctk.CTkLabel(formulario, text="", wraplength=260, justify="left")
        self.label_status.pack(anchor="w", padx=20, pady=(0, 20))

    def _capturar_foto(self):
        nome_exibicao = self.entry_nome.get().strip()
        if not nome_exibicao:
            messagebox.showwarning("Nome obrigatório", "Digite o nome da pessoa antes de capturar.")
            return

        nome_chave = nome_exibicao.lower().replace(" ", "_")

        frame = self.app.ler_frame()
        if frame is None:
            self.label_status.configure(text="Câmera indisponível.", text_color=COR_ERRO)
            return

        caminho = core.salvar_foto_cadastro(nome_chave, frame)
        self.fotos_tiradas += 1
        self.label_contagem.configure(text=f"Fotos tiradas nesta sessão: {self.fotos_tiradas}")
        self.label_status.configure(text=f"Salvo: {os.path.basename(caminho)}", text_color=COR_SUCESSO)

        sala = self.combo_sala.get().strip()
        ra = self.entry_ra.get().strip()
        core.definir_pessoa_meta(nome_chave, nome_exibicao=nome_exibicao, sala=sala, ra=ra)

        core.limpar_cache_embeddings()

    def _atualizar_frame(self):
        frame = self.app.ler_frame()
        if frame is not None:
            self._exibir_frame(frame)
        self.after(30, self._atualizar_frame)

    def _exibir_frame(self, frame):
        _exibir_frame(self.video_label, frame)


# ==========================================================================
# Tela: Salas / Turmas
# ==========================================================================


