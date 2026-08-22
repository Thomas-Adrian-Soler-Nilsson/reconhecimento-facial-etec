import customtkinter as ctk
from tkinter import messagebox, filedialog
from collections import Counter
from datetime import datetime
import os
import core
from ui.components import botao, painel as criar_painel
from ui.theme import configurar_tema
from .common import *

class TelaRelatorios(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self, text="Relatórios", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")

        # ---- Painel de filtros ----
        painel_filtros = criar_painel(self)
        painel_filtros.grid(row=1, column=0, padx=30, pady=(10, 10), sticky="ew")
        painel_filtros.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(painel_filtros, text=termo_sala, font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=(16, 8), pady=(14, 2), sticky="w")
        salas = [_sem_sala_label(cfg)] + core.carregar_salas()
        self.combo_sala = ctk.CTkOptionMenu(painel_filtros, values=salas)
        self.combo_sala.grid(row=1, column=0, padx=(16, 8), pady=(0, 14), sticky="ew")

        ctk.CTkLabel(painel_filtros, text="Data início (dd/mm/aaaa)", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=1, padx=8, pady=(14, 2), sticky="w")
        self.entry_data_inicio = ctk.CTkEntry(painel_filtros, placeholder_text="Opcional")
        self.entry_data_inicio.grid(row=1, column=1, padx=8, pady=(0, 14), sticky="ew")

        ctk.CTkLabel(painel_filtros, text="Data fim (dd/mm/aaaa)", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=2, padx=8, pady=(14, 2), sticky="w")
        self.entry_data_fim = ctk.CTkEntry(painel_filtros, placeholder_text="Opcional")
        self.entry_data_fim.grid(row=1, column=2, padx=8, pady=(0, 14), sticky="ew")

        ctk.CTkButton(painel_filtros, text="Filtrar", image=_icone("search"), compound="left", command=self._aplicar_filtros
                       ).grid(row=1, column=3, padx=(8, 16), pady=(0, 14), sticky="ew")

        # ---- Resumo ----
        self.label_resumo = ctk.CTkLabel(self, text="", text_color=COR_NEUTRA)
        self.label_resumo.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="w")

        # ---- Botões de ação ----
        painel_acoes = ctk.CTkFrame(self, fg_color="transparent")
        painel_acoes.grid(row=3, column=0, padx=30, pady=(0, 10), sticky="w")

        ctk.CTkButton(painel_acoes, text="Exportar CSV", image=_icone("upload"), compound="left", width=160,
                       command=self._exportar).grid(row=0, column=0, padx=(0, 10))
        ctk.CTkButton(painel_acoes, text="Ver presença x falta", image=_icone("clipboard-list"), compound="left", width=200,
                       command=self._ver_presenca_falta).grid(row=0, column=1)

        # ---- Tabela ----
        self.tabela = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13))
        self.tabela.grid(row=4, column=0, padx=30, pady=(0, 30), sticky="nsew")

        self._aplicar_filtros()

    def _obter_datas(self):
        def parse(texto):
            texto = texto.strip()
            if not texto:
                return None
            try:
                return datetime.strptime(texto, "%d/%m/%Y").date()
            except ValueError:
                messagebox.showwarning("Data inválida", f"Use o formato dd/mm/aaaa: '{texto}'")
                return "erro"

        di = parse(self.entry_data_inicio.get())
        df = parse(self.entry_data_fim.get())
        if di == "erro" or df == "erro":
            return None, None, False
        return di, df, True

    def _sala_selecionada(self):
        cfg = self.app.config_dados
        sala = self.combo_sala.get()
        if sala == _sem_sala_label(cfg):
            return None
        return sala

    def _aplicar_filtros(self):
        di, df, ok = self._obter_datas()
        if not ok:
            return

        sala = self._sala_selecionada()
        registros = core.filtrar_registros(sala=sala, data_inicio=di, data_fim=df)
        self._preencher_tabela(registros)

        contagem = Counter(r["nome"] for r in registros)
        self.label_resumo.configure(
            text=f"{len(registros)} registro(s) · {len(contagem)} pessoa(s) distintas"
        )

    def _preencher_tabela(self, registros):
        cfg = self.app.config_dados
        termo_sala = cfg.get("termo_sala", "Turma")

        self.tabela.configure(state="normal")
        self.tabela.delete("1.0", "end")

        cabecalho = f"{'NOME':<20} {termo_sala.upper():<15} {'TIPO':<20} {'DATA':<12} {'HORA':<10}\n"
        self.tabela.insert("end", cabecalho)
        self.tabela.insert("end", "-" * 80 + "\n")

        for linha in reversed(registros):
            texto = (f"{linha['nome']:<20} {linha.get('sala', '-') or '-':<15} "
                      f"{linha.get('tipo', '-'):<20} {linha['data']:<12} {linha['hora']:<10}\n")
            self.tabela.insert("end", texto)

        if not registros:
            self.tabela.insert("end", "Nenhum registro encontrado com esses filtros.\n")

        self.tabela.configure(state="disabled")

    def _ver_presenca_falta(self):
        sala = self._sala_selecionada()
        if not sala:
            messagebox.showinfo("Selecione uma sala", "Escolha uma sala/turma específica para ver presença x falta.")
            return

        presentes, ausentes = core.calcular_presencas_faltas(sala)

        self.tabela.configure(state="normal")
        self.tabela.delete("1.0", "end")
        self.tabela.insert("end", f"PRESENÇA x FALTA — {sala}\n")
        self.tabela.insert("end", "-" * 60 + "\n\n")
        self.tabela.insert("end", f"✔ PRESENTES ({len(presentes)}):\n")
        for nome in presentes:
            self.tabela.insert("end", f"   {nome}\n")
        self.tabela.insert("end", f"\n✘ AUSENTES ({len(ausentes)}):\n")
        for nome in ausentes:
            self.tabela.insert("end", f"   {nome}\n")
        if not presentes and not ausentes:
            self.tabela.insert("end", "\nNenhuma pessoa cadastrada nessa sala ainda.\n")
        self.tabela.configure(state="disabled")

    def _exportar(self):
        di, df, ok = self._obter_datas()
        if not ok:
            return
        sala = self._sala_selecionada()

        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")],
            initialfile="relatorio_presenca.csv"
        )
        if not caminho:
            return

        qtd = core.exportar_relatorio_csv(caminho, sala=sala, data_inicio=di, data_fim=df)
        messagebox.showinfo("Exportado", f"{qtd} registro(s) exportado(s) para:\n{caminho}")


# ==========================================================================
# Tela: Importar pessoas via CSV externo (ex.: exportação de sistema acadêmico)
# ==========================================================================


