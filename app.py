"""
app.py
Interface gráfica única do sistema de reconhecimento facial.
Unifica: cadastro de pessoas, registro de presença (individual e em grupo)
e relatórios. Genérico para uso em escolas ou empresas.
"""

import os
import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox
from collections import Counter

import core

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COR_SUCESSO = "#2fa84f"
COR_ALERTA = "#d99a2b"
COR_ERRO = "#c0392b"
COR_NEUTRA = "#8a8a8a"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_dados = core.carregar_config()

        self.title("Sistema de Reconhecimento Facial")
        self.geometry("1100x680")
        self.minsize(980, 620)

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

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        titulo = ctk.CTkLabel(
            self.sidebar, text=self.config_dados["nome_organizacao"],
            font=ctk.CTkFont(size=18, weight="bold"), wraplength=190, justify="left"
        )
        titulo.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        subtitulo = ctk.CTkLabel(
            self.sidebar, text=f"Reconhecimento Facial · {self.config_dados['tipo_organizacao']}",
            font=ctk.CTkFont(size=12), text_color=COR_NEUTRA, wraplength=190, justify="left"
        )
        subtitulo.grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        botoes = [
            ("🏠  Início", TelaInicio),
            ("➕  Cadastrar Pessoa", TelaCadastro),
            ("✅  Registrar Presença", TelaRegistroIndividual),
            ("👥  Chamada em Grupo", TelaRegistroGrupo),
            ("📊  Relatórios", TelaRelatorios),
            ("⚙️  Configurações", TelaConfiguracoes),
        ]

        self.botoes_nav = {}
        for i, (texto, tela) in enumerate(botoes, start=2):
            btn = ctk.CTkButton(
                self.sidebar, text=texto, anchor="w", height=42,
                fg_color="transparent", hover_color="#2b2b2b",
                font=ctk.CTkFont(size=14),
                command=lambda t=tela: self.mostrar_tela(t)
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self.botoes_nav[tela] = btn

        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.tela_atual = None

    def mostrar_tela(self, classe_tela):
        # encerra a câmera se a tela anterior estava usando
        self.parar_camera()

        if self.tela_atual is not None:
            self.tela_atual.destroy()

        for tela, btn in self.botoes_nav.items():
            btn.configure(fg_color="#2b6cb0" if tela == classe_tela else "transparent")

        self.tela_atual = classe_tela(self.container, self)
        self.tela_atual.grid(row=0, column=0, sticky="nsew")

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

        self._card(0, "Pessoas cadastradas", str(len(pessoas)), "#2b6cb0")
        self._card(1, "Registros no total", str(len(registros)), COR_SUCESSO)
        self._card(2, "Tipo de organização", cfg["tipo_organizacao"], COR_ALERTA)

        acoes_label = ctk.CTkLabel(self, text="Ações rápidas", font=ctk.CTkFont(size=16, weight="bold"))
        acoes_label.grid(row=3, column=0, columnspan=3, padx=30, pady=(30, 10), sticky="w")

        ctk.CTkButton(self, text="➕ Cadastrar nova pessoa", height=44,
                       command=lambda: self.app.mostrar_tela(TelaCadastro)
                       ).grid(row=4, column=0, padx=(30, 10), pady=6, sticky="ew")

        ctk.CTkButton(self, text="✅ Registrar presença", height=44,
                       command=lambda: self.app.mostrar_tela(TelaRegistroIndividual)
                       ).grid(row=4, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(self, text="👥 Iniciar chamada em grupo", height=44,
                       command=lambda: self.app.mostrar_tela(TelaRegistroGrupo)
                       ).grid(row=4, column=2, padx=(10, 30), pady=6, sticky="ew")

    def _card(self, coluna, titulo, valor, cor):
        card = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
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

        ctk.CTkLabel(self, text="Cadastrar Pessoa", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Tire de 3 a 5 fotos variando ângulo e expressão para melhor precisão.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        # Coluna esquerda: vídeo
        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

        # Coluna direita: formulário
        painel = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
        painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        ctk.CTkLabel(painel, text="Nome completo", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        self.entry_nome = ctk.CTkEntry(painel, placeholder_text="Ex: Thomas Adrian", height=38)
        self.entry_nome.pack(fill="x", padx=20)

        self.btn_capturar = ctk.CTkButton(painel, text="📸 Capturar foto", height=42,
                                           command=self._capturar_foto)
        self.btn_capturar.pack(fill="x", padx=20, pady=(20, 8))

        self.label_contagem = ctk.CTkLabel(painel, text="Fotos tiradas nesta sessão: 0",
                                            text_color=COR_NEUTRA)
        self.label_contagem.pack(anchor="w", padx=20, pady=(0, 20))

        self.label_status = ctk.CTkLabel(painel, text="", wraplength=260, justify="left")
        self.label_status.pack(anchor="w", padx=20, pady=(0, 20))

    def _capturar_foto(self):
        nome = self.entry_nome.get().strip().lower().replace(" ", "_")
        if not nome:
            messagebox.showwarning("Nome obrigatório", "Digite o nome da pessoa antes de capturar.")
            return

        frame = self.app.ler_frame()
        if frame is None:
            self.label_status.configure(text="Câmera indisponível.", text_color=COR_ERRO)
            return

        caminho = core.salvar_foto_cadastro(nome, frame)
        self.fotos_tiradas += 1
        self.label_contagem.configure(text=f"Fotos tiradas nesta sessão: {self.fotos_tiradas}")
        self.label_status.configure(text=f"Salvo: {os.path.basename(caminho)}", text_color=COR_SUCESSO)

        # nova pessoa cadastrada invalida o cache de embeddings
        core.limpar_cache_embeddings()

    def _atualizar_frame(self):
        frame = self.app.ler_frame()
        if frame is not None:
            self._exibir_frame(frame)
        self.after(30, self._atualizar_frame)

    def _exibir_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((560, 420))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)


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
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Registrar Presença", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Posicione o rosto na câmera e clique em Registrar.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")

        painel = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
        painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        ctk.CTkLabel(painel, text="Tipo de registro", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        self.combo_tipo = ctk.CTkOptionMenu(painel, values=["Entrada", "Saída"])
        self.combo_tipo.pack(fill="x", padx=20)

        self.btn_registrar = ctk.CTkButton(painel, text="✅ Registrar presença", height=44,
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

        if nome is None:
            self.label_status.configure(text="Rosto não reconhecido.", text_color=COR_ERRO)
        elif core.ja_registrado_recentemente(nome, minutos):
            self.label_status.configure(text=f"{nome} já registrado recentemente.", text_color=COR_ALERTA)
        else:
            core.registrar_presenca(nome, tipo=self.combo_tipo.get())
            self.label_status.configure(text=f"Presença registrada: {nome}", text_color=COR_SUCESSO)

    def _atualizar_frame(self):
        frame = self.app.ler_frame()
        if frame is not None:
            self._exibir_frame(frame)
        self.after(30, self._atualizar_frame)

    def _exibir_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((560, 420))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)


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
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Chamada em Grupo", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(self, text="Reconhecimento contínuo — cada pessoa é registrada automaticamente uma vez.",
                     text_color=COR_NEUTRA).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        self.video_label = ctk.CTkLabel(self, text="", fg_color="black", corner_radius=10)
        self.video_label.grid(row=2, column=0, padx=(30, 10), pady=10, sticky="nsew")

        painel = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
        painel.grid(row=2, column=1, padx=(10, 30), pady=10, sticky="new")

        self.btn_iniciar = ctk.CTkButton(painel, text="▶️ Iniciar chamada", height=44,
                                          fg_color=COR_SUCESSO, hover_color="#237a3d",
                                          command=self._alternar_sessao)
        self.btn_iniciar.pack(fill="x", padx=20, pady=(20, 10))

        self.label_status = ctk.CTkLabel(painel, text="Sessão parada.", font=ctk.CTkFont(size=15, weight="bold"))
        self.label_status.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(painel, text="Presentes nesta sessão:", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(10, 4))

        self.lista_presentes = ctk.CTkTextbox(painel, height=260)
        self.lista_presentes.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.lista_presentes.configure(state="disabled")

    def _alternar_sessao(self):
        if not self.sessao_ativa:
            self.sessao_ativa = True
            self.registrados_na_sessao = set()
            self._atualizar_lista()
            self.app.iniciar_camera()
            self.btn_iniciar.configure(text="⏹️ Encerrar chamada", fg_color=COR_ERRO, hover_color="#8f2b20")
            self.label_status.configure(text="Sessão em andamento...", text_color=COR_SUCESSO)
            self._loop_reconhecimento()
        else:
            self.sessao_ativa = False
            self.app.parar_camera()
            self.btn_iniciar.configure(text="▶️ Iniciar chamada", fg_color=COR_SUCESSO, hover_color="#237a3d")
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
                    core.registrar_presenca(nome, tipo="Chamada em grupo")
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
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((560, 420))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def destroy(self):
        self.sessao_ativa = False
        super().destroy()


# ==========================================================================
# Tela: Relatórios
# ==========================================================================

class TelaRelatorios(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._montar()

    def _montar(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text="Relatórios", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")

        registros = core.ler_registros()
        contagem = Counter(r["nome"] for r in registros)

        resumo = ctk.CTkLabel(
            self, text=f"{len(registros)} registro(s) no total · {len(contagem)} pessoa(s) distintas",
            text_color=COR_NEUTRA
        )
        resumo.grid(row=1, column=0, padx=30, pady=(0, 16), sticky="w")

        ctk.CTkButton(self, text="🔄 Atualizar", width=140, command=self._recarregar
                       ).grid(row=2, column=0, padx=30, pady=(0, 10), sticky="w")

        self.tabela = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13))
        self.tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self._preencher_tabela(registros)

    def _preencher_tabela(self, registros):
        self.tabela.configure(state="normal")
        self.tabela.delete("1.0", "end")

        cabecalho = f"{'NOME':<20} {'TIPO':<20} {'DATA':<12} {'HORA':<10}\n"
        self.tabela.insert("end", cabecalho)
        self.tabela.insert("end", "-" * 64 + "\n")

        for linha in reversed(registros):
            texto = f"{linha['nome']:<20} {linha.get('tipo', '-'): <20} {linha['data']:<12} {linha['hora']:<10}\n"
            self.tabela.insert("end", texto)

        if not registros:
            self.tabela.insert("end", "Nenhum registro encontrado ainda.\n")

        self.tabela.configure(state="disabled")

    def _recarregar(self):
        registros = core.ler_registros()
        self._preencher_tabela(registros)


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

        painel = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
        painel.grid(row=1, column=0, padx=30, pady=0, sticky="ew")

        cfg = self.app.config_dados

        ctk.CTkLabel(painel, text="Nome da instituição/empresa", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(20, 4))
        self.entry_nome = ctk.CTkEntry(painel, height=38)
        self.entry_nome.insert(0, cfg["nome_organizacao"])
        self.entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Tipo de organização", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.combo_tipo = ctk.CTkOptionMenu(painel, values=["Escola", "Empresa"])
        self.combo_tipo.set(cfg["tipo_organizacao"])
        self.combo_tipo.pack(fill="x", padx=20)

        ctk.CTkLabel(painel, text="Minutos entre registros repetidos", font=ctk.CTkFont(size=13)
                     ).pack(anchor="w", padx=20, pady=(16, 4))
        self.entry_minutos = ctk.CTkEntry(painel, height=38)
        self.entry_minutos.insert(0, str(cfg["minutos_entre_registros"]))
        self.entry_minutos.pack(fill="x", padx=20)

        ctk.CTkButton(painel, text="💾 Salvar configurações", height=42, command=self._salvar
                       ).pack(fill="x", padx=20, pady=(24, 20))

        # Manutenção do banco de rostos
        painel2 = ctk.CTkFrame(self, corner_radius=12, fg_color="#242424")
        painel2.grid(row=2, column=0, padx=30, pady=20, sticky="ew")

        ctk.CTkLabel(painel2, text="Manutenção", font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        pessoas = core.listar_pessoas_cadastradas()
        ctk.CTkLabel(painel2, text=f"{len(pessoas)} pessoa(s) cadastrada(s) no banco de rostos.",
                     text_color=COR_NEUTRA).pack(anchor="w", padx=20)

        ctk.CTkButton(painel2, text="🗑️ Limpar cache de reconhecimento", height=38,
                       fg_color="transparent", border_width=1,
                       command=self._limpar_cache
                       ).pack(fill="x", padx=20, pady=(14, 20))

    def _salvar(self):
        try:
            minutos = int(self.entry_minutos.get())
        except ValueError:
            messagebox.showwarning("Valor inválido", "Minutos deve ser um número inteiro.")
            return

        self.app.config_dados["nome_organizacao"] = self.entry_nome.get().strip() or "Minha Instituição"
        self.app.config_dados["tipo_organizacao"] = self.combo_tipo.get()
        self.app.config_dados["minutos_entre_registros"] = minutos
        core.salvar_config(self.app.config_dados)

        messagebox.showinfo("Salvo", "Configurações salvas. Reabra a tela Início para atualizar o cabeçalho.")

    def _limpar_cache(self):
        removidos = core.limpar_cache_embeddings()
        messagebox.showinfo("Cache limpo", f"{removidos or 0} arquivo(s) de cache removido(s).")


if __name__ == "__main__":
    app = App()
    app.mainloop()