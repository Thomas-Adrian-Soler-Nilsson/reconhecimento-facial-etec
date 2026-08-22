import os
from datetime import datetime

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox, filedialog
from collections import Counter
from iconipy import IconFactory


import core
from ui.components import botao, painel as criar_painel
from ui.theme import CORES, configurar_tema

configurar_tema()

icon_factory = IconFactory(icon_set="lucide", icon_size=22, font_color="white")


def _icone(nome, tamanho=22):
    imagem = icon_factory.asPil(nome)
    return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(tamanho, tamanho))


def _exibir_frame(video_label, frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagem = Image.fromarray(frame_rgb).resize((560, 420))
    imagem_tk = ImageTk.PhotoImage(image=imagem)
    video_label.imgtk = imagem_tk
    video_label.configure(image=imagem_tk)


def _carregar_logo(caminho, tamanho=(180, 90)):
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        imagem = Image.open(caminho)
        return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=tamanho)
    except (OSError, ValueError):
        return None


COR_SUCESSO = CORES["sucesso"]
COR_ALERTA = CORES["alerta"]
COR_ERRO = CORES["erro"]
COR_NEUTRA = CORES["neutra"]
COR_TEXTO = CORES["texto"]
COR_FUNDO = CORES["fundo"]
COR_PAINEL = CORES["painel"]
COR_LISTA = CORES["painel_secundario"]
COR_SELECAO = CORES["selecao"]
COR_HOVER = CORES["hover"]


def _sem_sala_label(cfg):
    return f"Todas as {cfg.get('termo_sala', 'Turma')}s"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_dados = core.carregar_config()
        configurar_tema(self.config_dados.get("tema", "Claro"))

        self.title("Sistema de Reconhecimento Facial")
        self.geometry("1150x700")
        self.minsize(1000, 640)

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
        logo = _carregar_logo(self.config_dados.get("logo_path"))
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

        ctk.CTkLabel(formulario, text=f"{termo_sala} (opcional)", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        salas_disponiveis = [""] + core.carregar_salas()
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


if __name__ == "__main__":
    app = App()
    app.mainloop()