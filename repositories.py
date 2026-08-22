from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

from models import Pessoa, Registro, Sala, Sessao, Turma


DEFAULT_STORAGE_DIR = Path("database") / "presenca_local"

PESSOAS_ARQUIVO = "pessoas.csv"
TURMAS_ARQUIVO = "turmas.csv"
SALAS_ARQUIVO = "salas.csv"
SESSOES_ARQUIVO = "sessoes.csv"
REGISTROS_ARQUIVO = "registros.csv"

PESSOAS_CABECALHO = [
    "identificador",
    "nome",
    "categoria",
    "turma_ou_setor",
    "ativo",
    "fotos",
]
TURMAS_CABECALHO = ["identificador", "nome", "categoria", "ativo"]
SALAS_CABECALHO = ["identificador", "nome", "capacidade", "ativo"]
SESSOES_CABECALHO = [
    "identificador",
    "tipo_operacao",
    "sala",
    "turma_ou_setor",
    "responsavel_id",
    "inicio_data",
    "inicio_hora",
    "fim_data",
    "fim_hora",
]
REGISTROS_CABECALHO = [
    "identificador",
    "sessao_id",
    "pessoa_id",
    "status",
    "presente",
    "recognition_result",
    "registrado_em",
]


def caminho_pessoas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> Path:
    """Retorna o caminho canônico de pessoas.csv."""

    return Path(base_dir) / PESSOAS_ARQUIVO


def caminho_turmas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> Path:
    """Retorna o caminho canônico de turmas.csv."""

    return Path(base_dir) / TURMAS_ARQUIVO


def caminho_salas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> Path:
    """Retorna o caminho canônico de salas.csv."""

    return Path(base_dir) / SALAS_ARQUIVO


def caminho_sessoes(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> Path:
    """Retorna o caminho canônico de sessoes.csv."""

    return Path(base_dir) / SESSOES_ARQUIVO


def caminho_registros(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> Path:
    """Retorna o caminho canônico de registros.csv."""

    return Path(base_dir) / REGISTROS_ARQUIVO


def ler_pessoas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> list[Pessoa]:
    """Lê pessoas.csv e devolve uma lista de Pessoa."""

    return _ler_csv(caminho_pessoas(base_dir), PESSOAS_CABECALHO, _pessoa_from_row)


def salvar_pessoas(pessoas: list[Pessoa], base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> None:
    """Salva pessoas em pessoas.csv."""

    _salvar_csv(caminho_pessoas(base_dir), PESSOAS_CABECALHO, (_pessoa_to_row(p) for p in pessoas))


def ler_turmas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> list[Turma]:
    """Lê turmas.csv e devolve uma lista de Turma."""

    return _ler_csv(caminho_turmas(base_dir), TURMAS_CABECALHO, _turma_from_row)


def salvar_turmas(turmas: list[Turma], base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> None:
    """Salva turmas em turmas.csv."""

    _salvar_csv(caminho_turmas(base_dir), TURMAS_CABECALHO, (_turma_to_row(t) for t in turmas))


def ler_salas(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> list[Sala]:
    """Lê salas.csv e devolve uma lista de Sala."""

    return _ler_csv(caminho_salas(base_dir), SALAS_CABECALHO, _sala_from_row)


def salvar_salas(salas: list[Sala], base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> None:
    """Salva salas em salas.csv."""

    _salvar_csv(caminho_salas(base_dir), SALAS_CABECALHO, (_sala_to_row(s) for s in salas))


def ler_sessoes(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> list[Sessao]:
    """Lê sessoes.csv e devolve uma lista de Sessao."""

    return _ler_csv(caminho_sessoes(base_dir), SESSOES_CABECALHO, _sessao_from_row)


def salvar_sessoes(sessoes: list[Sessao], base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> None:
    """Salva sessoes em sessoes.csv."""

    _salvar_csv(caminho_sessoes(base_dir), SESSOES_CABECALHO, (_sessao_to_row(s) for s in sessoes))


def ler_registros(base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> list[Registro]:
    """Lê registros.csv e devolve uma lista de Registro."""

    return _ler_csv(caminho_registros(base_dir), REGISTROS_CABECALHO, _registro_from_row)


def salvar_registros(registros: list[Registro], base_dir: str | os.PathLike[str] = DEFAULT_STORAGE_DIR) -> None:
    """Salva registros em registros.csv."""

    _salvar_csv(
        caminho_registros(base_dir),
        REGISTROS_CABECALHO,
        (_registro_to_row(r) for r in registros),
    )


def _ler_csv(
    caminho: Path,
    cabecalho: list[str],
    parser,
) -> list:
    _garantir_csv_atomico(caminho, cabecalho)
    with caminho.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [parser(linha) for linha in leitor]


def _salvar_csv(
    caminho: Path,
    cabecalho: list[str],
    linhas,
) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        encoding="utf-8",
        newline="",
        dir=caminho.parent,
        prefix=f".{caminho.stem}.",
        suffix=".tmp",
    ) as temporario:
        escritor = csv.DictWriter(temporario, fieldnames=cabecalho)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow(linha)
        nome_temporario = Path(temporario.name)

    os.replace(nome_temporario, caminho)


def _garantir_csv_atomico(caminho: Path, cabecalho: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists() and caminho.stat().st_size > 0:
        return
    _salvar_csv(caminho, cabecalho, ())


def _pessoa_to_row(pessoa: Pessoa) -> dict[str, str]:
    return {
        "identificador": pessoa.identificador,
        "nome": pessoa.nome,
        "categoria": pessoa.categoria,
        "turma_ou_setor": pessoa.turma_ou_setor,
        "ativo": _bool_para_csv(pessoa.ativo),
        "fotos": _json_para_csv(pessoa.fotos),
    }


def _pessoa_from_row(linha: dict[str, str]) -> Pessoa:
    return Pessoa(
        identificador=linha["identificador"],
        nome=linha["nome"],
        categoria=linha["categoria"],
        turma_ou_setor=linha["turma_ou_setor"],
        ativo=_csv_para_bool(linha["ativo"]),
        fotos=_csv_para_json_lista(linha["fotos"]),
    )


def _turma_to_row(turma: Turma) -> dict[str, str]:
    return {
        "identificador": turma.identificador,
        "nome": turma.nome,
        "categoria": turma.categoria,
        "ativo": _bool_para_csv(turma.ativo),
    }


def _turma_from_row(linha: dict[str, str]) -> Turma:
    return Turma(
        identificador=linha["identificador"],
        nome=linha["nome"],
        categoria=linha["categoria"],
        ativo=_csv_para_bool(linha["ativo"]),
    )


def _sala_to_row(sala: Sala) -> dict[str, str]:
    return {
        "identificador": sala.identificador,
        "nome": sala.nome,
        "capacidade": str(sala.capacidade),
        "ativo": _bool_para_csv(sala.ativo),
    }


def _sala_from_row(linha: dict[str, str]) -> Sala:
    return Sala(
        identificador=linha["identificador"],
        nome=linha["nome"],
        capacidade=int(linha["capacidade"] or 0),
        ativo=_csv_para_bool(linha["ativo"]),
    )


def _sessao_to_row(sessao: Sessao) -> dict[str, str]:
    return {
        "identificador": sessao.identificador,
        "tipo_operacao": sessao.tipo_operacao,
        "sala": sessao.sala,
        "turma_ou_setor": sessao.turma_ou_setor,
        "responsavel_id": sessao.responsavel_id,
        "inicio_data": sessao.inicio_data,
        "inicio_hora": sessao.inicio_hora,
        "fim_data": sessao.fim_data or "",
        "fim_hora": sessao.fim_hora or "",
    }


def _sessao_from_row(linha: dict[str, str]) -> Sessao:
    fim_data = linha["fim_data"].strip() or None
    fim_hora = linha["fim_hora"].strip() or None
    return Sessao(
        identificador=linha["identificador"],
        tipo_operacao=linha["tipo_operacao"],
        sala=linha["sala"],
        turma_ou_setor=linha["turma_ou_setor"],
        responsavel_id=linha["responsavel_id"],
        inicio_data=linha["inicio_data"],
        inicio_hora=linha["inicio_hora"],
        fim_data=fim_data,
        fim_hora=fim_hora,
    )


def _registro_to_row(registro: Registro) -> dict[str, str]:
    return {
        "identificador": registro.identificador,
        "sessao_id": registro.sessao_id,
        "pessoa_id": registro.pessoa_id,
        "status": registro.status,
        "presente": _bool_para_csv(registro.presente),
        "recognition_result": registro.recognition_result,
        "registrado_em": registro.registrado_em,
    }


def _registro_from_row(linha: dict[str, str]) -> Registro:
    return Registro(
        identificador=linha["identificador"],
        sessao_id=linha["sessao_id"],
        pessoa_id=linha["pessoa_id"],
        status=linha["status"],
        presente=_csv_para_bool(linha["presente"]),
        recognition_result=linha["recognition_result"],
        registrado_em=linha["registrado_em"],
    )


def _bool_para_csv(valor: bool) -> str:
    return "true" if valor else "false"


def _csv_para_bool(valor: str) -> bool:
    return valor.strip().lower() in {"1", "true", "sim", "yes", "y"}


def _json_para_csv(valor: list[str]) -> str:
    return json.dumps(valor, ensure_ascii=False)


def _csv_para_json_lista(valor: str) -> list[str]:
    texto = valor.strip()
    if not texto:
        return []
    resultado = json.loads(texto)
    return [str(item) for item in resultado]
