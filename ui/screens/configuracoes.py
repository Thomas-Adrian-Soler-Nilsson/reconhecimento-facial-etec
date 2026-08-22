import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaConfiguracoes(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Configurações", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        painel = criar_painel(self)
        painel.grid(row=1, column=0, padx=30, pady=0, sticky="ew")

        cfg = self.app.config_dados

        ctk.CTkLabel(painel, text="Nome da instituição/empresa", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        self.entry_nome = ctk.CTkEntry(painel, height=38)
        self.entry_nome.insert(0, cfg["nome_organizacao"])
        self.entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Tipo de organização", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.combo_tipo = ctk.CTkOptionMenu(painel, values=["Escola", "Empresa"], command=self._ao_trocar_tipo)
        self.combo_tipo.set(cfg["tipo_organizacao"])
        self.combo_tipo.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Tema da interface", font=ctk.CTkFont(size=13)
                 ).pack(anchor="w", padx=20, pady=(16, 4))
        self.combo_tema = ctk.CTkOptionMenu(painel, values=["Claro", "Escuro"])
        self.combo_tema.set(cfg.get("tema", "Claro"))
        self.combo_tema.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Como chamar as 'salas' (ex: Turma, Setor, Departamento)",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(16, 4))
        self.entry_termo_sala = ctk.CTkEntry(painel, height=38)
        self.entry_termo_sala.insert(0, cfg.get("termo_sala", "Turma"))
        self.entry_termo_sala.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Minutos entre registros repetidos", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.entry_minutos = ctk.CTkEntry(painel, height=38)
        self.entry_minutos.insert(0, str(cfg["minutos_entre_registros"]))
        self.entry_minutos.pack(fill="x", padx=20)

        ctk.CTkButton(painel, text="Salvar configurações", image=_icone("save"), compound="left", height=42, command=self._salvar
                       ).pack(fill="x", padx=20, pady=(24, 20))

        painel2 = criar_painel(self)
        painel2.grid(row=2, column=0, padx=30, pady=20, sticky="ew")

        ctk.CTkLabel(painel2, text="Manutenção", font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        pessoas = core.listar_pessoas_cadastradas()
        ctk.CTkLabel(painel2, text=f"{len(pessoas)} pessoa(s) cadastrada(s) no banco de rostos.",
                     text_color=COR_NEUTRA).pack(anchor="w", padx=20)

        ctk.CTkButton(painel2, text="Limpar cache de reconhecimento", image=_icone("trash-2"), compound="left", height=38,
                       fg_color="transparent", border_width=1,
                       command=self._limpar_cache
                       ).pack(fill="x", padx=20, pady=(14, 20))

    def _ao_trocar_tipo(self, valor):
        if not self.entry_termo_sala.get().strip() or self.entry_termo_sala.get() in ("Turma", "Setor"):
            sugestao = "Turma" if valor == "Escola" else "Setor"
            self.entry_termo_sala.delete(0, "end")
            self.entry_termo_sala.insert(0, sugestao)

    def _salvar(self):
        try:
            minutos = int(self.entry_minutos.get())
        except ValueError:
            messagebox.showwarning("Valor inválido", "Minutos deve ser um número inteiro.")
            return

        self.app.config_dados["nome_organizacao"] = self.entry_nome.get().strip() or "Minha Instituição"
        self.app.config_dados["tipo_organizacao"] = self.combo_tipo.get()
        self.app.config_dados["tema"] = self.combo_tema.get()
        self.app.config_dados["termo_sala"] = self.entry_termo_sala.get().strip() or "Turma"
        self.app.config_dados["minutos_entre_registros"] = minutos
        core.salvar_config(self.app.config_dados)

        configurar_tema(self.app.config_dados["tema"])
        self.app.recarregar_cabecalho()
        messagebox.showinfo("Salvo", "Configurações salvas com sucesso.")

    def _limpar_cache(self):
        removidos = core.limpar_cache_embeddings()
        messagebox.showinfo("Cache limpo", f"{removidos or 0} arquivo(s) de cache removido(s).")



