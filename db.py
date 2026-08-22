import sqlite3
import json
import uuid
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "sistema_presenca.db"


# ---------------------------------------------------------------------------
# Conexão e schema
# ---------------------------------------------------------------------------

@contextmanager
def conectar():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def inicializar_banco():
    with conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS turmas (
            identificador TEXT PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            categoria TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS salas (
            identificador TEXT PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            capacidade INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS pessoas (
            identificador TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            nome_chave TEXT NOT NULL UNIQUE,     -- usado para casar com a pasta do database/ (DeepFace)
            categoria TEXT DEFAULT '',
            turma_ou_setor TEXT,
            ativo INTEGER DEFAULT 1,
            fotos TEXT DEFAULT '[]',             -- lista JSON de caminhos de foto
            ra TEXT DEFAULT '',                  -- RA / matrícula (opcional)
            FOREIGN KEY (turma_ou_setor) REFERENCES turmas(identificador)
        );

        CREATE TABLE IF NOT EXISTS sessoes (
            identificador TEXT PRIMARY KEY,
            tipo_operacao TEXT NOT NULL,
            sala TEXT,
            turma_ou_setor TEXT,
            responsavel_id TEXT,
            inicio_data TEXT NOT NULL,
            inicio_hora TEXT NOT NULL,
            fim_data TEXT,
            fim_hora TEXT,
            FOREIGN KEY (sala) REFERENCES salas(identificador),
            FOREIGN KEY (turma_ou_setor) REFERENCES turmas(identificador),
            FOREIGN KEY (responsavel_id) REFERENCES pessoas(identificador)
        );

        CREATE TABLE IF NOT EXISTS registros (
            identificador TEXT PRIMARY KEY,
            sessao_id TEXT NOT NULL,
            pessoa_id TEXT NOT NULL,
            status TEXT NOT NULL,
            presente INTEGER NOT NULL,
            recognition_result TEXT DEFAULT '',
            registrado_em TEXT NOT NULL,
            FOREIGN KEY (sessao_id) REFERENCES sessoes(identificador),
            FOREIGN KEY (pessoa_id) REFERENCES pessoas(identificador)
        );

        CREATE INDEX IF NOT EXISTS idx_registros_sessao ON registros(sessao_id);
        CREATE INDEX IF NOT EXISTS idx_registros_pessoa ON registros(pessoa_id);
        CREATE INDEX IF NOT EXISTS idx_sessoes_sala ON sessoes(sala);
        CREATE INDEX IF NOT EXISTS idx_sessoes_turma ON sessoes(turma_ou_setor);
        """)


def gerar_id():
    return uuid.uuid4().hex[:8]


def _linha_para_dict(linha):
    return dict(linha) if linha is not None else None


# ---------------------------------------------------------------------------
# Turmas
# ---------------------------------------------------------------------------

def criar_turma(nome, categoria=""):
    identificador = gerar_id()
    with conectar() as conn:
        try:
            conn.execute(
                "INSERT INTO turmas (identificador, nome, categoria) VALUES (?, ?, ?)",
                (identificador, nome.strip(), categoria.strip())
            )
        except sqlite3.IntegrityError:
            return None  # nome já existe
    return identificador


def listar_turmas(somente_ativas=True):
    with conectar() as conn:
        query = "SELECT * FROM turmas"
        if somente_ativas:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        return [_linha_para_dict(l) for l in conn.execute(query).fetchall()]


def obter_turma(identificador):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM turmas WHERE identificador = ?", (identificador,)).fetchone()
        return _linha_para_dict(linha)


def obter_turma_por_nome(nome):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM turmas WHERE nome = ?", (nome,)).fetchone()
        return _linha_para_dict(linha)


def desativar_turma(identificador):
    with conectar() as conn:
        conn.execute("UPDATE turmas SET ativo = 0 WHERE identificador = ?", (identificador,))


# ---------------------------------------------------------------------------
# Salas
# ---------------------------------------------------------------------------

def criar_sala(nome, capacidade=0):
    identificador = gerar_id()
    with conectar() as conn:
        try:
            conn.execute(
                "INSERT INTO salas (identificador, nome, capacidade) VALUES (?, ?, ?)",
                (identificador, nome.strip(), capacidade)
            )
        except sqlite3.IntegrityError:
            return None
    return identificador


def listar_salas(somente_ativas=True):
    with conectar() as conn:
        query = "SELECT * FROM salas"
        if somente_ativas:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        return [_linha_para_dict(l) for l in conn.execute(query).fetchall()]


def obter_sala(identificador):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM salas WHERE identificador = ?", (identificador,)).fetchone()
        return _linha_para_dict(linha)


def obter_sala_por_nome(nome):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM salas WHERE nome = ?", (nome,)).fetchone()
        return _linha_para_dict(linha)


def desativar_sala(identificador):
    with conectar() as conn:
        conn.execute("UPDATE salas SET ativo = 0 WHERE identificador = ?", (identificador,))


# ---------------------------------------------------------------------------
# Pessoas
# ---------------------------------------------------------------------------

def _nome_chave(nome):
    return nome.strip().lower().replace(" ", "_")


def criar_pessoa(nome, categoria="", turma_ou_setor=None, ra=""):
    identificador = gerar_id()
    nome_chave = _nome_chave(nome)
    with conectar() as conn:
        try:
            conn.execute(
                """INSERT INTO pessoas (identificador, nome, nome_chave, categoria, turma_ou_setor, fotos, ra)
                   VALUES (?, ?, ?, ?, ?, '[]', ?)""",
                (identificador, nome.strip(), nome_chave, categoria, turma_ou_setor, ra)
            )
        except sqlite3.IntegrityError:
            return obter_pessoa_por_nome_chave(nome_chave)["identificador"]
    return identificador


def obter_pessoa(identificador):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM pessoas WHERE identificador = ?", (identificador,)).fetchone()
        return _dict_pessoa(linha)


def obter_pessoa_por_nome_chave(nome_chave):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM pessoas WHERE nome_chave = ?", (nome_chave,)).fetchone()
        return _dict_pessoa(linha)


def _dict_pessoa(linha):
    if linha is None:
        return None
    d = dict(linha)
    d["fotos"] = json.loads(d.get("fotos") or "[]")
    d["ativo"] = bool(d["ativo"])
    return d


def listar_pessoas(turma_ou_setor=None, somente_ativas=True):
    with conectar() as conn:
        query = "SELECT * FROM pessoas WHERE 1=1"
        params = []
        if turma_ou_setor:
            query += " AND turma_ou_setor = ?"
            params.append(turma_ou_setor)
        if somente_ativas:
            query += " AND ativo = 1"
        query += " ORDER BY nome"
        linhas = conn.execute(query, params).fetchall()
        return [_dict_pessoa(l) for l in linhas]


def atualizar_pessoa(identificador, nome=None, categoria=None, turma_ou_setor=None, ra=None):
    campos, valores = [], []
    if nome is not None:
        campos.append("nome = ?")
        valores.append(nome.strip())
        campos.append("nome_chave = ?")
        valores.append(_nome_chave(nome))
    if categoria is not None:
        campos.append("categoria = ?")
        valores.append(categoria)
    if turma_ou_setor is not None:
        campos.append("turma_ou_setor = ?")
        valores.append(turma_ou_setor)
    if ra is not None:
        campos.append("ra = ?")
        valores.append(ra)

    if not campos:
        return

    valores.append(identificador)
    with conectar() as conn:
        conn.execute(f"UPDATE pessoas SET {', '.join(campos)} WHERE identificador = ?", valores)


def adicionar_foto_pessoa(identificador, caminho_foto):
    pessoa = obter_pessoa(identificador)
    if pessoa is None:
        return
    fotos = pessoa["fotos"]
    fotos.append(caminho_foto)
    with conectar() as conn:
        conn.execute(
            "UPDATE pessoas SET fotos = ? WHERE identificador = ?",
            (json.dumps(fotos, ensure_ascii=False), identificador)
        )


def desativar_pessoa(identificador):
    with conectar() as conn:
        conn.execute("UPDATE pessoas SET ativo = 0 WHERE identificador = ?", (identificador,))


# ---------------------------------------------------------------------------
# Sessões (ex: uma aula, uma reunião, um período de chamada)
# ---------------------------------------------------------------------------

def abrir_sessao(tipo_operacao, sala=None, turma_ou_setor=None, responsavel_id=None):
    identificador = gerar_id()
    agora = datetime.now()
    with conectar() as conn:
        conn.execute(
            """INSERT INTO sessoes
               (identificador, tipo_operacao, sala, turma_ou_setor, responsavel_id, inicio_data, inicio_hora)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (identificador, tipo_operacao, sala, turma_ou_setor, responsavel_id,
             agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M:%S"))
        )
    return identificador


def encerrar_sessao(identificador):
    agora = datetime.now()
    with conectar() as conn:
        conn.execute(
            "UPDATE sessoes SET fim_data = ?, fim_hora = ? WHERE identificador = ?",
            (agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M:%S"), identificador)
        )


def obter_sessao(identificador):
    with conectar() as conn:
        linha = conn.execute("SELECT * FROM sessoes WHERE identificador = ?", (identificador,)).fetchone()
        return _linha_para_dict(linha)


def listar_sessoes(sala=None, turma_ou_setor=None, data_inicio=None, data_fim=None):
    with conectar() as conn:
        query = "SELECT * FROM sessoes WHERE 1=1"
        params = []
        if sala:
            query += " AND sala = ?"
            params.append(sala)
        if turma_ou_setor:
            query += " AND turma_ou_setor = ?"
            params.append(turma_ou_setor)
        query += " ORDER BY inicio_data DESC, inicio_hora DESC"
        linhas = conn.execute(query, params).fetchall()

    resultado = [_linha_para_dict(l) for l in linhas]

    if data_inicio or data_fim:
        def dentro_intervalo(sessao):
            d = datetime.strptime(sessao["inicio_data"], "%d/%m/%Y").date()
            if data_inicio and d < data_inicio:
                return False
            if data_fim and d > data_fim:
                return False
            return True
        resultado = [s for s in resultado if dentro_intervalo(s)]

    return resultado


# ---------------------------------------------------------------------------
# Registros de presença
# ---------------------------------------------------------------------------

def registrar_presenca(sessao_id, pessoa_id, status="Presente", presente=True, recognition_result=""):
    identificador = gerar_id()
    agora = datetime.now().isoformat()
    with conectar() as conn:
        conn.execute(
            """INSERT INTO registros
               (identificador, sessao_id, pessoa_id, status, presente, recognition_result, registrado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (identificador, sessao_id, pessoa_id, status, int(presente), recognition_result, agora)
        )
    return identificador


def ja_registrado_na_sessao(sessao_id, pessoa_id):
    with conectar() as conn:
        linha = conn.execute(
            "SELECT 1 FROM registros WHERE sessao_id = ? AND pessoa_id = ? LIMIT 1",
            (sessao_id, pessoa_id)
        ).fetchone()
        return linha is not None


def ja_registrado_recentemente(pessoa_id, minutos, turma_ou_setor=None):
    """Verifica se a pessoa tem algum registro nos últimos N minutos (opcionalmente filtrando por turma/setor)."""
    with conectar() as conn:
        query = """
            SELECT r.registrado_em FROM registros r
            JOIN sessoes s ON r.sessao_id = s.identificador
            WHERE r.pessoa_id = ?
        """
        params = [pessoa_id]
        if turma_ou_setor:
            query += " AND s.turma_ou_setor = ?"
            params.append(turma_ou_setor)
        query += " ORDER BY r.registrado_em DESC LIMIT 1"

        linha = conn.execute(query, params).fetchone()

    if linha is None:
        return False

    registrado_em = datetime.fromisoformat(linha["registrado_em"])
    diferenca_min = (datetime.now() - registrado_em).total_seconds() / 60
    return diferenca_min < minutos


def listar_registros(sessao_id=None, pessoa_id=None, sala=None, turma_ou_setor=None,
                      data_inicio=None, data_fim=None):
    """Retorna registros com dados já unidos (nome da pessoa, sala, turma, tipo de sessão)."""
    with conectar() as conn:
        query = """
            SELECT
                r.identificador, r.status, r.presente, r.recognition_result, r.registrado_em,
                p.nome AS nome_pessoa,
                s.tipo_operacao, s.inicio_data, s.inicio_hora,
                sala_t.nome AS nome_sala,
                turma_t.nome AS nome_turma
            FROM registros r
            JOIN pessoas p ON r.pessoa_id = p.identificador
            JOIN sessoes s ON r.sessao_id = s.identificador
            LEFT JOIN salas sala_t ON s.sala = sala_t.identificador
            LEFT JOIN turmas turma_t ON s.turma_ou_setor = turma_t.identificador
            WHERE 1=1
        """
        params = []
        if sessao_id:
            query += " AND r.sessao_id = ?"
            params.append(sessao_id)
        if pessoa_id:
            query += " AND r.pessoa_id = ?"
            params.append(pessoa_id)
        if sala:
            query += " AND s.sala = ?"
            params.append(sala)
        if turma_ou_setor:
            query += " AND s.turma_ou_setor = ?"
            params.append(turma_ou_setor)

        query += " ORDER BY r.registrado_em DESC"

        linhas = [_linha_para_dict(l) for l in conn.execute(query, params).fetchall()]

    if data_inicio or data_fim:
        def dentro_intervalo(reg):
            d = datetime.strptime(reg["inicio_data"], "%d/%m/%Y").date()
            if data_inicio and d < data_inicio:
                return False
            if data_fim and d > data_fim:
                return False
            return True
        linhas = [l for l in linhas if dentro_intervalo(l)]

    return linhas


def calcular_presenca_falta(turma_ou_setor, sessao_id=None):
    """
    Compara pessoas esperadas na turma com quem tem registro de presença,
    retornando (presentes, ausentes) - listas de dicts de pessoa.
    """
    esperados = listar_pessoas(turma_ou_setor=turma_ou_setor)

    with conectar() as conn:
        query = """
            SELECT DISTINCT r.pessoa_id FROM registros r
            JOIN sessoes s ON r.sessao_id = s.identificador
            WHERE s.turma_ou_setor = ?
        """
        params = [turma_ou_setor]
        if sessao_id:
            query += " AND r.sessao_id = ?"
            params.append(sessao_id)
        ids_presentes = {l["pessoa_id"] for l in conn.execute(query, params).fetchall()}

    presentes = [p for p in esperados if p["identificador"] in ids_presentes]
    ausentes = [p for p in esperados if p["identificador"] not in ids_presentes]

    return presentes, ausentes


def exportar_registros_csv(caminho_destino, **filtros):
    """Exporta o resultado de listar_registros(**filtros) para um CSV."""
    import csv as csv_module

    registros = listar_registros(**filtros)
    campos = ["nome_pessoa", "nome_sala", "nome_turma", "tipo_operacao",
              "status", "inicio_data", "inicio_hora", "registrado_em"]

    with open(caminho_destino, mode="w", newline="", encoding="utf-8") as f:
        writer = csv_module.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in registros:
            writer.writerow({campo: r.get(campo, "") for campo in campos})

    return len(registros)