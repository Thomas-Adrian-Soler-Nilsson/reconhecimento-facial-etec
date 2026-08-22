import os
import csv
import json
import shutil
from datetime import datetime

from deepface import DeepFace

import db

DB_PATH = "database"          # pasta de fotos (usada pelo DeepFace)
CONFIG_PATH = "config.json"   # preferências de interface, não dados estruturados

MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "mtcnn"

CONFIG_PADRAO = {
    "nome_organizacao": "Minha Instituição",
    "tipo_organizacao": "Escola",   # "Escola" ou "Empresa"
    "termo_pessoa": "Aluno/Funcionário",
    "termo_sala": "Turma",          # "Turma" (escola) ou "Setor"/"Departamento" (empresa)
    "minutos_entre_registros": 5,
    "tema": "Claro",
    "logo_claro_path": "img/fatec_etec_fundo_claro_transparente.png",
    "logo_escuro_path": "img/fatec_etec_modo_escuro_transparente.png"
}

# garante que as tabelas existam assim que este módulo é importado
db.inicializar_banco()


# ---------------------------------------------------------------------------
# Configuração (continua em JSON — é preferência de interface, não dado estruturado)
# ---------------------------------------------------------------------------

def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        salvar_config(CONFIG_PADRAO)
        return dict(CONFIG_PADRAO)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    for chave, valor in CONFIG_PADRAO.items():
        config.setdefault(chave, valor)

    return config


def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Salas / Turmas / Setores  (agora gerenciadas via db.turmas)
# ---------------------------------------------------------------------------

def carregar_salas():
    """Retorna lista ordenada de nomes de turmas/salas cadastradas."""
    return sorted(t["nome"] for t in db.listar_turmas())


def adicionar_sala(nome_sala):
    nome_sala = nome_sala.strip()
    if not nome_sala:
        return False
    if db.obter_turma_por_nome(nome_sala):
        return False
    return db.criar_turma(nome_sala) is not None


def remover_sala(nome_sala):
    turma = db.obter_turma_por_nome(nome_sala)
    if not turma:
        return False
    db.desativar_turma(turma["identificador"])
    return True


def listar_pessoas_por_sala(nome_sala):
    turma = db.obter_turma_por_nome(nome_sala)
    if not turma:
        return []
    pessoas = db.listar_pessoas(turma_ou_setor=turma["identificador"])
    return sorted(p["nome"] for p in pessoas)


# ---------------------------------------------------------------------------
# Metadados de pessoas (sala, RA/matrícula) — agora em db.pessoas
# ---------------------------------------------------------------------------

def definir_pessoa_meta(nome_chave, nome_exibicao=None, sala=None, ra=None):
    """Cria ou atualiza os metadados (nome de exibição, turma, RA) de uma pessoa."""
    turma_id = None
    if sala:
        turma = db.obter_turma_por_nome(sala)
        turma_id = turma["identificador"] if turma else db.criar_turma(sala)

    pessoa = db.obter_pessoa_por_nome_chave(nome_chave)

    if pessoa is None:
        db.criar_pessoa(
            nome_exibicao or nome_chave.replace("_", " ").title(),
            turma_ou_setor=turma_id,
            ra=ra or ""
        )
    else:
        db.atualizar_pessoa(
            pessoa["identificador"],
            nome=nome_exibicao,
            turma_ou_setor=turma_id,
            ra=ra
        )


def obter_sala_pessoa(nome_chave):
    pessoa = db.obter_pessoa_por_nome_chave(nome_chave)
    if not pessoa or not pessoa.get("turma_ou_setor"):
        return ""
    turma = db.obter_turma(pessoa["turma_ou_setor"])
    return turma["nome"] if turma else ""


# ---------------------------------------------------------------------------
# Banco de rostos (fotos em disco — usado pelo DeepFace)
# ---------------------------------------------------------------------------

def listar_pessoas_cadastradas():
    """Retorna lista de nomes-chave (pastas) cadastradas no banco de rostos."""
    if not os.path.exists(DB_PATH):
        return []
    return sorted([
        nome for nome in os.listdir(DB_PATH)
        if os.path.isdir(os.path.join(DB_PATH, nome))
    ])


def listar_pessoas(somente_ativas=True):
    """Retorna os dados das pessoas cadastradas."""
    pessoas = db.listar_pessoas(somente_ativas=somente_ativas)
    for pessoa in pessoas:
        pessoa["sala"] = obter_sala_pessoa(pessoa["nome_chave"])
        pessoa["quantidade_fotos"] = contar_fotos(pessoa["nome_chave"])
    return sorted(pessoas, key=lambda pessoa: pessoa["nome"].lower())


def excluir_pessoa(identificador):
    """Desativa a pessoa e remove suas fotos do banco de rostos."""
    pessoa = db.obter_pessoa(identificador)
    if not pessoa:
        return False

    db.desativar_pessoa(identificador)
    pasta = os.path.join(DB_PATH, pessoa["nome_chave"])
    if os.path.isdir(pasta):
        shutil.rmtree(pasta)
    limpar_cache_embeddings()
    return True


def contar_fotos(nome_chave):
    pasta = os.path.join(DB_PATH, nome_chave)
    if not os.path.exists(pasta):
        return 0
    return len([f for f in os.listdir(pasta) if f.lower().endswith((".jpg", ".jpeg", ".png"))])


def salvar_foto_cadastro(nome_chave, frame):
    """Salva um frame (numpy array do OpenCV) na pasta da pessoa e sincroniza com o banco."""
    import cv2
    pasta = os.path.join(DB_PATH, nome_chave)
    os.makedirs(pasta, exist_ok=True)
    proxima = contar_fotos(nome_chave) + 1
    caminho = os.path.join(pasta, f"{nome_chave}_{proxima}.jpg")
    cv2.imwrite(caminho, frame)

    # garante que a pessoa já exista no banco (mesmo sem metadados ainda)
    pessoa = db.obter_pessoa_por_nome_chave(nome_chave)
    if pessoa is None:
        pessoa_id = db.criar_pessoa(nome_chave.replace("_", " ").title())
    else:
        pessoa_id = pessoa["identificador"]
    db.adicionar_foto_pessoa(pessoa_id, caminho)

    return caminho


def limpar_cache_embeddings():
    """Remove o(s) arquivo(s) .pkl de cache do DeepFace, forçando reindexação."""
    if not os.path.exists(DB_PATH):
        return 0
    removidos = 0
    for arquivo in os.listdir(DB_PATH):
        if arquivo.endswith(".pkl"):
            os.remove(os.path.join(DB_PATH, arquivo))
            removidos += 1
    return removidos


# ---------------------------------------------------------------------------
# Registro de presença (agora via db.sessoes + db.registros)
#
# Cada chamada a registrar_presenca() abre uma sessão avulsa (uma sessão =
# um evento de reconhecimento). Isso mantém a mesma assinatura simples que a
# interface já usa; se no futuro quiser uma sessão única compartilhada por
# toda a "Chamada em Grupo", dá pra trocar para abrir a sessão uma vez no
# início da tela e reutilizar o mesmo sessao_id em cada registro.
# ---------------------------------------------------------------------------

def _obter_ou_criar_pessoa_id(nome_chave):
    pessoa = db.obter_pessoa_por_nome_chave(nome_chave)
    if pessoa:
        return pessoa["identificador"]
    return db.criar_pessoa(nome_chave.replace("_", " ").title())


def _obter_ou_criar_turma_id(nome_sala):
    if not nome_sala:
        return None
    turma = db.obter_turma_por_nome(nome_sala)
    return turma["identificador"] if turma else db.criar_turma(nome_sala)


def registrar_presenca(nome_chave, tipo="Registro", sala=""):
    pessoa_id = _obter_ou_criar_pessoa_id(nome_chave)
    turma_id = _obter_ou_criar_turma_id(sala)

    sessao_id = db.abrir_sessao(tipo_operacao=tipo, turma_ou_setor=turma_id)
    db.registrar_presenca(
        sessao_id=sessao_id,
        pessoa_id=pessoa_id,
        status="Presente",
        presente=True,
        recognition_result=nome_chave
    )


def ja_registrado_recentemente(nome_chave, minutos, sala=None):
    pessoa = db.obter_pessoa_por_nome_chave(nome_chave)
    if pessoa is None:
        return False

    turma_id = None
    if sala:
        turma = db.obter_turma_por_nome(sala)
        turma_id = turma["identificador"] if turma else None

    return db.ja_registrado_recentemente(pessoa["identificador"], minutos, turma_ou_setor=turma_id)


def _mapear_registro_legado(r):
    """Converte o formato de linha do db.listar_registros() para as chaves
    que a interface (app.py) já espera: nome, sala, tipo, data, hora, timestamp."""
    return {
        "nome": r["nome_pessoa"],
        "sala": r.get("nome_turma") or "",
        "tipo": r["tipo_operacao"],
        "data": r["inicio_data"],
        "hora": r["inicio_hora"],
        "timestamp": r["registrado_em"],
    }


def ler_registros():
    return [_mapear_registro_legado(r) for r in db.listar_registros()]


def filtrar_registros(sala=None, data_inicio=None, data_fim=None):
    """
    Filtra registros por sala/turma e/ou intervalo de datas.
    data_inicio / data_fim: objetos datetime.date (opcional).
    """
    turma_id = None
    if sala and sala != "Todas":
        turma = db.obter_turma_por_nome(sala)
        if not turma:
            return []  # sala/turma informada não existe -> nenhum registro possível
        turma_id = turma["identificador"]

    registros = db.listar_registros(turma_ou_setor=turma_id, data_inicio=data_inicio, data_fim=data_fim)
    return [_mapear_registro_legado(r) for r in registros]


def calcular_presencas_faltas(sala):
    """
    Compara pessoas cadastradas na sala/turma com quem tem registro,
    retornando (presentes, ausentes) - listas de nomes.
    """
    turma = db.obter_turma_por_nome(sala)
    if not turma:
        return [], []

    presentes, ausentes = db.calcular_presenca_falta(turma["identificador"])
    return sorted(p["nome"] for p in presentes), sorted(p["nome"] for p in ausentes)


def exportar_relatorio_csv(caminho_destino, sala=None, data_inicio=None, data_fim=None):
    """Exporta os registros filtrados para um novo arquivo CSV."""
    turma_id = None
    if sala and sala != "Todas":
        turma = db.obter_turma_por_nome(sala)
        turma_id = turma["identificador"] if turma else None

    return db.exportar_registros_csv(
        caminho_destino,
        turma_ou_setor=turma_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


# ---------------------------------------------------------------------------
# Importação de CSV externo (ex.: lista de alunos exportada de outro sistema)
# ---------------------------------------------------------------------------

def prever_colunas_csv(caminho_csv, delimitador=","):
    """Lê apenas o cabeçalho do CSV para o usuário mapear as colunas."""
    with open(caminho_csv, "r", encoding="utf-8-sig") as f:
        leitor = csv.reader(f, delimiter=delimitador)
        cabecalho = next(leitor, [])
    return cabecalho


def importar_pessoas_csv(caminho_csv, coluna_nome, coluna_sala=None, coluna_ra=None, delimitador=","):
    """
    Importa pessoas de um CSV externo (ex.: exportação de sistema acadêmico)
    para o banco SQLite. Cria/atualiza apenas os METADADOS (nome, turma, RA).

    IMPORTANTE: a importação não cadastra rosto automaticamente — cada pessoa
    ainda precisa passar pela tela "Cadastrar Pessoa" para tirar as fotos,
    já que não existe (ainda) integração direta de fotos com o sistema da CPS.

    Retorna: (quantidade_importada, lista_de_nomes_sem_foto_cadastrada)
    """
    importados = 0
    sem_foto = []

    with open(caminho_csv, "r", encoding="utf-8-sig") as f:
        leitor = csv.DictReader(f, delimiter=delimitador)

        for linha in leitor:
            nome_exibicao = (linha.get(coluna_nome) or "").strip()
            if not nome_exibicao:
                continue

            nome_chave = nome_exibicao.lower().replace(" ", "_")
            sala = (linha.get(coluna_sala) or "").strip() if coluna_sala else ""
            ra = (linha.get(coluna_ra) or "").strip() if coluna_ra else ""

            definir_pessoa_meta(nome_chave, nome_exibicao=nome_exibicao, sala=sala, ra=ra)
            importados += 1

            if contar_fotos(nome_chave) == 0:
                sem_foto.append(nome_exibicao)

    return importados, sem_foto


# ---------------------------------------------------------------------------
# Reconhecimento facial
# ---------------------------------------------------------------------------

def identificar_pessoa(frame, exigir_rosto=False):
    """
    Roda o DeepFace no frame e retorna o nome-chave identificado (pasta no
    database/) ou None se não reconhecer ninguém.
    """
    try:
        resultados = DeepFace.find(
            img_path=frame,
            db_path=DB_PATH,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=exigir_rosto,
            silent=True
        )

        if len(resultados) > 0 and not resultados[0].empty:
            identidade = resultados[0].iloc[0]["identity"]
            return identidade.split(os.sep)[-2]

    except Exception:
        pass

    return None