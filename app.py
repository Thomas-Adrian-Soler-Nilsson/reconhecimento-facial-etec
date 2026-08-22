import cv2
import customtkinter as ctk

import core
from ui.components import botao, painel as criar_painel
from ui.theme import CORES, configurar_tema
from ui.screens.common import COR_FUNDO, COR_NEUTRA, COR_SELECAO, _carregar_logo, _icone
from ui.screens import (
    TelaCadastro,
    TelaConfiguracoes,
    TelaImportarCSV,
    TelaInicio,
    TelaPessoas,
    TelaRegistroGrupo,
    TelaRegistroIndividual,
    TelaRelatorios,
    TelaSalas,
)

configurar_tema()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_dados = core.carregar_config()
        configurar_tema(self.config_dados.get("tema", "Claro"))

        self.title("Sistema de Reconhecimento Facial")
        self.minsize(640, 600)

        self.cap = None
        self.camera_ativa = False

        self._montar_layout()
        self.mostrar_tela(TelaInicio)

        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    # ------------------------------------------------------------------
    # Layout base: sidebar + área de conteúdo
    # ------------------------------------------------------------------

    def _montar_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=CORES["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        self._popular_sidebar()

        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color=COR_FUNDO)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.tela_atual = None

    def mostrar_tela(self, classe_tela):
        self.parar_camera()

        if self.tela_atual is not None:
            self.tela_atual.destroy()

        for tela, btn in self.botoes_nav.items():
            btn.configure(fg_color=COR_SELECAO if tela == classe_tela else "transparent")

        self.tela_atual = classe_tela(self.container, self)
        self.tela_atual.grid(row=0, column=0, sticky="nsew")

    def recarregar_cabecalho(self):
        """Atualiza nome/tipo de organização na sidebar (após mudar em Configurações)."""
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self.sidebar.grid_rowconfigure(10, weight=1)
        self._popular_sidebar()

    def _popular_sidebar(self):
        # separado de _montar_layout para poder recriar sem duplicar o container
        chave_logo = "logo_escuro_path" if self.config_dados.get("tema") == "Escuro" else "logo_claro_path"
        caminho_logo = self.config_dados.get(chave_logo)
        logo = _carregar_logo(caminho_logo)
        if logo:
            self.logo_sidebar = logo
            cabecalho = ctk.CTkLabel(self.sidebar, text="", image=logo)
        else:
            cabecalho = ctk.CTkLabel(
                self.sidebar, text=self.config_dados["nome_organizacao"],
                font=ctk.CTkFont(size=18, weight="bold"), wraplength=190, justify="left"
            )
        cabecalho.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        subtitulo = ctk.CTkLabel(
            self.sidebar, text=f"Reconhecimento Facial · {self.config_dados['tipo_organizacao']}",
            font=ctk.CTkFont(size=12), text_color=COR_NEUTRA, wraplength=190, justify="left"
        )
        subtitulo.grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        botoes = [
            ("Início", TelaInicio, "house"),
            ("Cadastrar Pessoa", TelaCadastro, "user-plus"),
            ("Pessoas Cadastradas", TelaPessoas, "users-round"),
            ("Salas / Turmas", TelaSalas, "school"),
            ("Registrar Presença", TelaRegistroIndividual, "circle-check"),
            ("Chamada em Grupo", TelaRegistroGrupo, "users"),
            ("Relatórios", TelaRelatorios, "chart-no-axes-column"),
            ("Importar Pessoas (CSV)", TelaImportarCSV, "file-down"),
            ("Configurações", TelaConfiguracoes, "settings"),
        ]

        self.botoes_nav = {}
        for i, (texto, tela, icone) in enumerate(botoes, start=2):
            btn = botao(
                self.sidebar, texto, lambda t=tela: self.mostrar_tela(t),
                icone=_icone(icone), variante="transparente", anchor="w", height=42
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self.botoes_nav[tela] = btn

    # ------------------------------------------------------------------
    # Gerenciamento de câmera (compartilhado entre telas)
    # ------------------------------------------------------------------

    def iniciar_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        self.camera_ativa = True

    def parar_camera(self):
        self.camera_ativa = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def ler_frame(self):
        if self.cap is None or not self.camera_ativa:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def _ao_fechar(self):
        self.parar_camera()
        self.destroy()


# ==========================================================================
# Tela: Início
# ==========================================================================



if __name__ == "__main__":
    app = App()
    app.mainloop()
