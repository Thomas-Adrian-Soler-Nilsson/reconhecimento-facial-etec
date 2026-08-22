import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaSalas(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text=f"{termo_sala}s", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text=f"Gerencie as {termo_sala.lower()}s usadas no cadastro e nos relatórios.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        painel_add = criar_painel(self)
        painel_add.grid(row=2, column=0, padx=30, pady=(0, 16), sticky="ew")
        painel_add.grid_columnconfigure(0, weight=1)

        self.entry_nova_sala = ctk.CTkEntry(painel_add, placeholder_text=f"Nome da(o) nova(o) {termo_sala.lower()}",
                                             height=38)
        self.entry_nova_sala.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="ew")

        ctk.CTkButton(painel_add, text="Adicionar", image=_icone("plus"), compound="left", width=140, height=38,
                       command=self._adicionar).grid(row=0, column=1, padx=(0, 16), pady=16)

        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color=COR_LISTA)
        self.lista_frame.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.lista_frame.grid_columnconfigure(0, weight=1)

        self._atualizar_lista()

    def _adicionar(self):
        nome = self.entry_nova_sala.get().strip()
        if not nome:
            return
        if core.adicionar_sala(nome):
            self.entry_nova_sala.delete(0, "end")
            self._atualizar_lista()
        else:
            messagebox.showinfo("Já existe", "Essa sala/turma já está cadastrada.")

    def _remover(self, nome):
        confirmar = messagebox.askyesno(
            "Remover", f"Remover '{nome}'? Pessoas já associadas a ela continuam com o vínculo salvo."
        )
        if confirmar:
            core.remover_sala(nome)
            self._atualizar_lista()

    def _atualizar_lista(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        salas = core.carregar_salas()

        if not salas:
            ctk.CTkLabel(self.lista_frame, text="Nenhuma sala/turma cadastrada ainda.",
                         text_color=COR_NEUTRA).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        for i, sala in enumerate(salas):
            linha = ctk.CTkFrame(self.lista_frame, fg_color=COR_PAINEL, corner_radius=10)
            linha.grid(row=i, column=0, padx=4, pady=4, sticky="ew")
            linha.grid_columnconfigure(0, weight=1)

            qtd_pessoas = len(core.listar_pessoas_por_sala(sala))
            ctk.CTkLabel(linha, text=f"{sala}", font=ctk.CTkFont(size=15, weight="bold")
                         ).grid(row=0, column=0, padx=16, pady=12, sticky="w")
            ctk.CTkLabel(linha, text=f"{qtd_pessoas} pessoa(s)", text_color=COR_NEUTRA
                         ).grid(row=0, column=1, padx=16, pady=12)
            ctk.CTkButton(linha, text="Remover", width=90, height=30, fg_color="transparent",
                          border_width=1, text_color=COR_ERRO, border_color=COR_ERRO,
                          command=lambda s=sala: self._remover(s)
                          ).grid(row=0, column=2, padx=16, pady=12)


# ===========================================================================
# Tela: Pessoas cadastradas
# ===========================================================================


