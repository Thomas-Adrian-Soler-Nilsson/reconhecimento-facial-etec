"""
core.py
Módulo compartilhado: configuração, banco de rostos, registro de presença
e reconhecimento facial. Usado pela interface gráfica (app.py).
"""

import os
import csv
import json
from datetime import datetime

from deepface import DeepFace

DB_PATH = "database"
LOG_PATH = "registros.csv"
CONFIG_PATH = "config.json"

MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "mtcnn"

CONFIG_PADRAO = {
    "nome_organizacao": "Minha Instituição",
    "tipo_organizacao": "Escola",   # "Escola" ou "Empresa"
    "termo_pessoa": "Aluno/Funcionário",
    "minutos_entre_registros": 5
}


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        salvar_config(CONFIG_PADRAO)
        return dict(CONFIG_PADRAO)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # garante que chaves novas existam mesmo em config antigo
    for chave, valor in CONFIG_PADRAO.items():
        config.setdefault(chave, valor)

    return config


def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Banco de pessoas cadastradas
# ---------------------------------------------------------------------------

def listar_pessoas_cadastradas():
    """Retorna lista de nomes (pastas) cadastradas no banco de rostos."""
    if not os.path.exists(DB_PATH):
        return []
    return sorted([
        nome for nome in os.listdir(DB_PATH)
        if os.path.isdir(os.path.join(DB_PATH, nome))
    ])


def contar_fotos(nome):
    pasta = os.path.join(DB_PATH, nome)
    if not os.path.exists(pasta):
        return 0
    return len([f for f in os.listdir(pasta) if f.lower().endswith((".jpg", ".jpeg", ".png"))])


def salvar_foto_cadastro(nome, frame):
    """Salva um frame (numpy array do OpenCV) na pasta da pessoa."""
    import cv2
    pasta = os.path.join(DB_PATH, nome)
    os.makedirs(pasta, exist_ok=True)
    proxima = contar_fotos(nome) + 1
    caminho = os.path.join(pasta, f"{nome}_{proxima}.jpg")
    cv2.imwrite(caminho, frame)
    return caminho


def limpar_cache_embeddings():
    """Remove o(s) arquivo(s) .pkl de cache do DeepFace, forçando reindexação."""
    if not os.path.exists(DB_PATH):
        return
    removidos = 0
    for arquivo in os.listdir(DB_PATH):
        if arquivo.endswith(".pkl"):
            os.remove(os.path.join(DB_PATH, arquivo))
            removidos += 1
    return removidos


# ---------------------------------------------------------------------------
# Registro de presença (CSV)
# ---------------------------------------------------------------------------

def garantir_csv():
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nome", "tipo", "data", "hora", "timestamp"])


def ler_registros():
    garantir_csv()
    with open(LOG_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ja_registrado_recentemente(nome, minutos):
    registros = ler_registros()
    agora = datetime.now()
    for linha in reversed(registros):
        if linha["nome"] == nome:
            registrado_em = datetime.fromisoformat(linha["timestamp"])
            diferenca_min = (agora - registrado_em).total_seconds() / 60
            return diferenca_min < minutos
    return False


def registrar_presenca(nome, tipo="Registro"):
    garantir_csv()
    agora = datetime.now()
    with open(LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            nome,
            tipo,
            agora.strftime("%d/%m/%Y"),
            agora.strftime("%H:%M:%S"),
            agora.isoformat()
        ])


# ---------------------------------------------------------------------------
# Reconhecimento facial
# ---------------------------------------------------------------------------

def identificar_pessoa(frame, exigir_rosto=False):
    """
    Roda o DeepFace no frame e retorna o nome identificado (pasta no database)
    ou None se não reconhecer ninguém.
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