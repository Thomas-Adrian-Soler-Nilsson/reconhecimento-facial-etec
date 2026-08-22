import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaPessoas(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        cfg = self.app.config_dados
        termo_pessoa = cfg.get("termo_pessoa", "Pessoa").split("/")[0]
        termo_sala = cfg.get("termo_sala", "Turma")

        ctk.CTkLabel(
            self, text=f"{termo_pessoa}s cadastrados",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(
            self, text=f"Consulte e remova {termo_pessoa.lower()}s cadastrados no sistema.",
            text_color=COR_NEUTRA
        ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color=COR_LISTA)
        self.lista_frame.grid(row=2, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.lista_frame.grid_columnconfigure(0, weight=1)
        self._atualizar_lista(termo_sala)

    def _atualizar_lista(self, termo_sala=None):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        cfg = self.app.config_dados
        termo_sala = termo_sala or cfg.get("termo_sala", "Turma")
        pessoas = core.listar_pessoas()

        if not pessoas:
            ctk.CTkLabel(
                self.lista_frame, text="Nenhuma pessoa cadastrada ainda.",
                text_color=COR_NEUTRA
            ).grid(row=0, column=0, padx=16, pady=16, sticky="w")
            return

        for linha_numero, pessoa in enumerate(pessoas):
            linha = ctk.CTkFrame(self.lista_frame, fg_color=COR_PAINEL, corner_radius=10)
            linha.grid(row=linha_numero, column=0, padx=4, pady=4, sticky="ew")
            linha.grid_columnconfigure(0, weight=1)

            detalhes = (
                f"{pessoa['nome']}\n"
                f"{termo_sala}: {pessoa.get('sala') or '-'}  |  "
                f"RA: {pessoa.get('ra') or '-'}  |  "
                f"Fotos: {pessoa['quantidade_fotos']}"
            )
            ctk.CTkLabel(
                linha, text=detalhes, justify="left", anchor="w",
                font=ctk.CTkFont(size=14)
            ).grid(row=0, column=0, padx=16, pady=12, sticky="w")
            ctk.CTkButton(
                linha, text="Excluir", image=_icone("trash-2"), compound="left",
                width=110, height=34, fg_color="transparent",
                border_width=1, text_color=COR_ERRO, border_color=COR_ERRO,
                command=lambda identificador=pessoa["identificador"], nome=pessoa["nome"]:
                    self._excluir(identificador, nome)
            ).grid(row=0, column=1, padx=16, pady=12)

    def _excluir(self, identificador, nome):
        confirmar = messagebox.askyesno(
            "Excluir pessoa",
            f"Excluir '{nome}'? As fotos serão removidas, mas o histórico de presença será preservado."
        )
        if confirmar and core.excluir_pessoa(identificador):
            self._atualizar_lista()
            messagebox.showinfo("Excluído", f"'{nome}' foi removido do cadastro.")


# ==========================================================================
# Tela: Registro individual de presença (sob demanda)
# ==========================================================================


