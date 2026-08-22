from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import fields
from pathlib import Path
from typing import Callable, Iterable, TypeVar, get_type_hints

from models import Pessoa, Registro, Sala, Sessao, Turma


PESSOAS_ARQUIVO = "pessoas.csv"
TURMAS_ARQUIVO = "turmas.csv"
SALAS_ARQUIVO = "salas.csv"
SESSOES_ARQUIVO = "sessoes.csv"
REGISTROS_ARQUIVO = "registros.csv"

PESSOAS_CABECALHO = ["id", "nome", "turma_id", "matricula", "ativo"]
TURMAS_CABECALHO = ["id", "nome", "ano_letivo", "descricao"]
SALAS_CABECALHO = ["id", "nome", "capacidade", "local"]
SESSOES_CABECALHO = ["id", "turma_id", "sala_id", "inicio", "fim", "ativa"]
REGISTROS_CABECALHO = ["id", "sessao_id", "pessoa_id", "nome", "registrado_em", "presente"]

T = TypeVar("T")


def caminho_pessoas(base_dir: str | os.PathLike[str] = ".") -> Path:
    """Retorna o caminho canônico de pessoas.csv."""

    return Path(base_dir) / PESSOAS_ARQUIVO


def caminho_turmas(base_dir: str | os.PathLike[str] = ".") -> Path:
    """Retorna o caminho canônico de turmas.csv."""

    return Path(base_dir) / TURMAS_ARQUIVO


def caminho_salas(base_dir: str | os.PathLike[str] = ".") -> Path:
    """Retorna o caminho canônico de salas.csv."""

    return Path(base_dir) / SALAS_ARQUIVO


def caminho_sessoes(base_dir: str | os.PathLike[str] = ".") -> Path:
    """Retorna o caminho canônico de sessoes.csv."""

    return Path(base_dir) / SESSOES_ARQUIVO


def caminho_registros(base_dir: str | os.PathLike[str] = ".") -> Path:
    """Retorna o caminho canônico de registros.csv."""

    return Path(base_dir) / REGISTROS_ARQUIVO


def ler_pessoas(base_dir: str | os.PathLike[str] = ".") -> list[Pessoa]:
    """Lê pessoas.csv e devolve uma lista de Pessoa."""

    return _ler_modelos(base_dir, caminho_pessoas, PESSOAS_CABECALHO, Pessoa)


def salvar_pessoas(pessoas: Iterable[Pessoa], base_dir: str | os.PathLike[str] = ".") -> None:
    """Salva uma sequência de Pessoa em pessoas.csv."""

    _salvar_modelos(base_dir, caminho_pessoas, PESSOAS_CABECALHO, pessoas)


def ler_turmas(base_dir: str | os.PathLike[str] = ".") -> list[Turma]:
    """Lê turmas.csv e devolve uma lista de Turma."""

    return _ler_modelos(base_dir, caminho_turmas, TURMAS_CABECALHO, Turma)


def salvar_turmas(turmas: Iterable[Turma], base_dir: str | os.PathLike[str] = ".") -> None:
    """Salva uma sequência de Turma em turmas.csv."""

    _salvar_modelos(base_dir, caminho_turmas, TURMAS_CABECALHO, turmas)


def ler_salas(base_dir: str | os.PathLike[str] = ".") -> list[Sala]:
    """Lê salas.csv e devolve uma lista de Sala."""

    return _ler_modelos(base_dir, caminho_salas, SALAS_CABECALHO, Sala)


def salvar_salas(salas: Iterable[Sala], base_dir: str | os.PathLike[str] = ".") -> None:
    """Salva uma sequência de Sala em salas.csv."""

    _salvar_modelos(base_dir, caminho_salas, SALAS_CABECALHO, salas)


def ler_sessoes(base_dir: str | os.PathLike[str] = ".") -> list[Sessao]:
    """Lê sessoes.csv e devolve uma lista de Sessao."""

    return _ler_modelos(base_dir, caminho_sessoes, SESSOES_CABECALHO, Sessao)


def salvar_sessoes(sessoes: Iterable[Sessao], base_dir: str | os.PathLike[str] = ".") -> None:
    """Salva uma sequência de Sessao em sessoes.csv."""

    _salvar_modelos(base_dir, caminho_sessoes, SESSOES_CABECALHO, sessoes)


def ler_registros(base_dir: str | os.PathLike[str] = ".") -> list[Registro]:
    """Lê registros.csv e devolve uma lista de Registro."""

    return _ler_modelos(base_dir, caminho_registros, REGISTROS_CABECALHO, Registro)


def salvar_registros(registros: Iterable[Registro], base_dir: str | os.PathLike[str] = ".") -> None:
    """Salva uma sequência de Registro em registros.csv."""

    _salvar_modelos(base_dir, caminho_registros, REGISTROS_CABECALHO, registros)


def _ler_modelos(
    base_dir: str | os.PathLike[str],
    caminho_fn: Callable[[str | os.PathLike[str]], Path],
    cabecalho: list[str],
    modelo: type[T],
) -> list[T]:
    caminho = caminho_fn(base_dir)
    _garantir_csv(caminho, cabecalho)

    with caminho.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames:
            return []
        return [_instanciar_modelo(modelo, linha) for linha in leitor]


def _salvar_modelos(
    base_dir: str | os.PathLike[str],
    caminho_fn: Callable[[str | os.PathLike[str]], Path],
    cabecalho: list[str],
    itens: Iterable[object],
) -> None:
    caminho = caminho_fn(base_dir)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = list(itens)
    _escrever_csv_atomico(caminho, cabecalho, linhas)


def _garantir_csv(caminho: Path, cabecalho: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not caminho.exists() or caminho.stat().st_size == 0:
        with caminho.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(cabecalho)


def _escrever_csv_atomico(caminho: Path, cabecalho: list[str], itens: Iterable[object]) -> None:
    diretorio = caminho.parent
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        encoding="utf-8",
        newline="",
        dir=diretorio,
    ) as temporario:
        escritor = csv.DictWriter(temporario, fieldnames=cabecalho)
        escritor.writeheader()
        for item in itens:
            escritor.writerow(_serializar_item(item, cabecalho))
        nome_temporario = Path(temporario.name)

    os.replace(nome_temporario, caminho)


def _serializar_item(item: object, cabecalho: list[str]) -> dict[str, str]:
    valores = {}
    for campo in cabecalho:
        valor = getattr(item, campo)
        if isinstance(valor, bool):
            valores[campo] = "true" if valor else "false"
        else:
            valores[campo] = str(valor)
    return valores


def _instanciar_modelo(modelo: type[T], linha: dict[str, str]) -> T:
    dados: dict[str, object] = {}
    tipos = get_type_hints(modelo)
    for campo in fields(modelo):
        valor_bruto = linha.get(campo.name, "")
        dados[campo.name] = _converter_valor(tipos.get(campo.name, str), valor_bruto)
    return modelo(**dados)


def _converter_valor(tipo: object, valor_bruto: str) -> object:
    texto = valor_bruto.strip()
    if tipo is bool:
        return texto.lower() in {"1", "true", "sim", "yes", "y"}
    if tipo is int:
        return int(texto) if texto else 0
    return valor_bruto
