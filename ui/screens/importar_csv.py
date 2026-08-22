import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaImportarCSV(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.caminho_csv = None
        self.colunas_disponiveis = []
        self._montar()

    def _montar(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Importar Pessoas via CSV", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")

        aviso = ctk.CTkLabel(
            self,
            text=("Importa nome, sala e RA/matrícula de um arquivo CSV exportado de outro sistema.\n"
                "Não existe integração direta com o sistema da CPS/SIGA — esta é uma importação "
                "genérica: você mapeia manualmente qual coluna do arquivo é qual dado.\n"
                  "A foto de cada pessoa ainda precisa ser cadastrada em \"Cadastrar Pessoa\"."),
            text_color=COR_NEUTRA, justify="left", wraplength=700
        )
        aviso.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        painel = criar_painel(self)
        painel.grid(row=2, column=0, padx=30, pady=0, sticky="ew")
        painel.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(painel, text="Selecionar arquivo CSV", image=_icone("folder-open"), compound="left", command=self._selecionar_arquivo
                       ).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.label_arquivo = ctk.CTkLabel(painel, text="Nenhum arquivo selecionado.", text_color=COR_NEUTRA)
        self.label_arquivo.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="w")

        ctk.CTkLabel(painel, text="Delimitador do arquivo", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, pady=(0, 4), sticky="w")
        self.combo_delimitador = ctk.CTkOptionMenu(painel, values=["Vírgula ( , )", "Ponto e vírgula ( ; )"])
        self.combo_delimitador.grid(row=1, column=1, padx=20, pady=(0, 14), sticky="w")

        ctk.CTkLabel(painel, text="Coluna do nome", font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, pady=4, sticky="w")
        self.combo_col_nome = ctk.CTkOptionMenu(painel, values=["—"])
        self.combo_col_nome.grid(row=2, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(painel, text="Coluna da sala/turma (opcional)", font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, padx=20, pady=4, sticky="w")
        self.combo_col_sala = ctk.CTkOptionMenu(painel, values=["—"])
        self.combo_col_sala.grid(row=3, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(painel, text="Coluna do RA/matrícula (opcional)", font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, padx=20, pady=(4, 20), sticky="w")
        self.combo_col_ra = ctk.CTkOptionMenu(painel, values=["—"])
        self.combo_col_ra.grid(row=4, column=1, padx=20, pady=(4, 20), sticky="w")

        self.btn_importar = ctk.CTkButton(self, text="Importar", image=_icone("download"), compound="left", height=44, state="disabled",
                                           command=self._importar)
        self.btn_importar.grid(row=3, column=0, padx=30, pady=20, sticky="w")

        self.resultado_box = ctk.CTkTextbox(self, height=220, font=ctk.CTkFont(family="Consolas", size=13))
        self.resultado_box.grid(row=4, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        self.resultado_box.configure(state="disabled")

    def _obter_delimitador(self):
        return ";" if self.combo_delimitador.get().startswith("Ponto") else ","

    def _selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")])
        if not caminho:
            return

        self.caminho_csv = caminho
        self.label_arquivo.configure(text=os.path.basename(caminho), text_color=COR_TEXTO)
        self._atualizar_colunas()

    def _atualizar_colunas(self):
        if not self.caminho_csv:
            return
        try:
            colunas = core.prever_colunas_csv(self.caminho_csv, delimitador=self._obter_delimitador())
        except Exception as e:
            messagebox.showerror("Erro ao ler arquivo", str(e))
            return

        if not colunas:
            messagebox.showwarning("Arquivo vazio", "Não foi possível encontrar colunas nesse arquivo.")
            return

        self.colunas_disponiveis = colunas
        opcoes_obrigatorio = colunas
        opcoes_opcional = ["—"] + colunas

        self.combo_col_nome.configure(values=opcoes_obrigatorio)
        self.combo_col_nome.set(colunas[0])

        self.combo_col_sala.configure(values=opcoes_opcional)
        self.combo_col_sala.set("—")

        self.combo_col_ra.configure(values=opcoes_opcional)
        self.combo_col_ra.set("—")

        self.btn_importar.configure(state="normal")

    def _importar(self):
        if not self.caminho_csv:
            return

        coluna_nome = self.combo_col_nome.get()
        coluna_sala = self.combo_col_sala.get()
        coluna_ra = self.combo_col_ra.get()

        coluna_sala = None if coluna_sala == "—" else coluna_sala
        coluna_ra = None if coluna_ra == "—" else coluna_ra

        try:
            importados, sem_foto = core.importar_pessoas_csv(
                self.caminho_csv,
                coluna_nome=coluna_nome,
                coluna_sala=coluna_sala,
                coluna_ra=coluna_ra,
                delimitador=self._obter_delimitador()
            )
        except Exception as e:
            messagebox.showerror("Erro na importação", str(e))
            return

        self.resultado_box.configure(state="normal")
        self.resultado_box.delete("1.0", "end")
        self.resultado_box.insert("end", f"{importados} pessoa(s) importada(s) com sucesso.\n\n")

        if sem_foto:
            self.resultado_box.insert(
                "end", f"⚠ {len(sem_foto)} pessoa(s) ainda sem foto cadastrada (necessário para reconhecimento):\n\n"
            )
            for nome in sem_foto:
                self.resultado_box.insert("end", f"   • {nome}\n")
        else:
            self.resultado_box.insert("end", "Todas as pessoas importadas já possuem fotos cadastradas.\n")

        self.resultado_box.configure(state="disabled")

        messagebox.showinfo("Importação concluída", f"{importados} pessoa(s) importada(s).")


# ==========================================================================
# Tela: Configurações
# ==========================================================================


