from __future__ import annotations

from pathlib import Path

from models import Pessoa, Registro, Sala, Sessao, Turma
from repositories import (
    PESSOAS_CABECALHO,
    REGISTROS_CABECALHO,
    SALAS_CABECALHO,
    SESSOES_CABECALHO,
    TURMAS_CABECALHO,
    ler_pessoas,
    ler_registros,
    ler_salas,
    ler_sessoes,
    ler_turmas,
    salvar_pessoas,
    salvar_registros,
    salvar_salas,
    salvar_sessoes,
    salvar_turmas,
)


def _ler_linhas(caminho: Path) -> list[list[str]]:
    return [linha.split(",") for linha in caminho.read_text(encoding="utf-8").splitlines()]


def test_missing_files_create_headers(tmp_path: Path) -> None:
    assert ler_pessoas(tmp_path) == []
    assert ler_turmas(tmp_path) == []
    assert ler_salas(tmp_path) == []
    assert ler_sessoes(tmp_path) == []
    assert ler_registros(tmp_path) == []

    assert _ler_linhas(tmp_path / "pessoas.csv")[0] == PESSOAS_CABECALHO
    assert _ler_linhas(tmp_path / "turmas.csv")[0] == TURMAS_CABECALHO
    assert _ler_linhas(tmp_path / "salas.csv")[0] == SALAS_CABECALHO
    assert _ler_linhas(tmp_path / "sessoes.csv")[0] == SESSOES_CABECALHO
    assert _ler_linhas(tmp_path / "registros.csv")[0] == REGISTROS_CABECALHO


def test_round_trip_pessoas_com_acento(tmp_path: Path) -> None:
    pessoas = [
        Pessoa(id="p1", nome="João da Silva", turma_id="t1", matricula="123", ativo=True),
        Pessoa(id="p2", nome="Ana Vitória", turma_id="t2", matricula="456", ativo=False),
    ]

    salvar_pessoas(pessoas, tmp_path)

    assert ler_pessoas(tmp_path) == pessoas
    assert "João da Silva" in (tmp_path / "pessoas.csv").read_text(encoding="utf-8")


def test_round_trip_todas_as_entidades(tmp_path: Path) -> None:
    turmas = [Turma(id="t1", nome="Turma A", ano_letivo="2026", descricao="Primeiro ciclo")]
    salas = [Sala(id="s1", nome="Sala 101", capacidade=30, local="Bloco B")]
    sessoes = [
        Sessao(
            id="ss1",
            turma_id="t1",
            sala_id="s1",
            inicio="2026-08-22T08:00:00",
            fim="2026-08-22T09:00:00",
            ativa=True,
        )
    ]
    registros = [
        Registro(
            id="r1",
            sessao_id="ss1",
            pessoa_id="p1",
            nome="João da Silva",
            registrado_em="2026-08-22T08:01:00",
            presente=True,
        )
    ]

    salvar_turmas(turmas, tmp_path)
    salvar_salas(salas, tmp_path)
    salvar_sessoes(sessoes, tmp_path)
    salvar_registros(registros, tmp_path)

    assert ler_turmas(tmp_path) == turmas
    assert ler_salas(tmp_path) == salas
    assert ler_sessoes(tmp_path) == sessoes
    assert ler_registros(tmp_path) == registros
