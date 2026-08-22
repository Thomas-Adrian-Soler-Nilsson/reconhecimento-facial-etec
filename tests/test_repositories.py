from __future__ import annotations

import csv
from pathlib import Path

import repositories
from models import Pessoa, Registro, Sessao
from repositories import (
    PESSOAS_CABECALHO,
    REGISTROS_CABECALHO,
    SESSOES_CABECALHO,
    ler_pessoas,
    ler_registros,
    ler_sessoes,
    salvar_pessoas,
    salvar_registros,
    salvar_sessoes,
)


def _ler_primeira_linha(caminho: Path) -> list[str]:
    return caminho.read_text(encoding="utf-8").splitlines()[0].split(",")


def test_default_storage_isolated_from_legacy_registros_csv_and_creates_header_atomically(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    legado = tmp_path / "registros.csv"
    legado.write_text("legacy,behavior\n", encoding="utf-8")

    replace_calls: list[tuple[Path, Path]] = []
    real_replace = repositories.os.replace

    def tracking_replace(src: str | bytes, dst: str | bytes) -> None:
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(repositories.os, "replace", tracking_replace)

    registros = ler_registros()

    assert registros == []
    assert legado.read_text(encoding="utf-8") == "legacy,behavior\n"

    destino = Path("database") / "presenca_local" / "registros.csv"
    canonical = tmp_path / destino
    assert canonical.exists()
    assert _ler_primeira_linha(canonical) == REGISTROS_CABECALHO
    assert replace_calls and replace_calls[-1][1] == destino


def test_pessoa_round_trip_preserves_required_fields_and_fotos(tmp_path: Path) -> None:
    pessoas = [
        Pessoa(
            identificador="p-1",
            nome="João da Silva",
            categoria="aluno",
            turma_ou_setor="Turma A",
            ativo=True,
            fotos=["pasta/joao-01.jpg", "pasta/joao-02.jpg"],
        ),
        Pessoa(
            identificador="p-2",
            nome="Ana Vitória",
            categoria="funcionário",
            turma_ou_setor="RH",
            ativo=False,
            fotos=[],
        ),
    ]

    salvar_pessoas(pessoas, tmp_path)

    assert ler_pessoas(tmp_path) == pessoas

    csv_path = tmp_path / "pessoas.csv"
    assert _ler_primeira_linha(csv_path) == PESSOAS_CABECALHO
    assert "João da Silva" in csv_path.read_text(encoding="utf-8")


def test_sessao_round_trip_allows_open_session(tmp_path: Path) -> None:
    sessoes = [
        Sessao(
            identificador="s-1",
            tipo_operacao="chamada",
            sala="Sala 101",
            turma_ou_setor="Turma A",
            responsavel_id="p-9",
            inicio_data="2026-08-22",
            inicio_hora="08:00:00",
            fim_data=None,
            fim_hora=None,
        )
    ]

    salvar_sessoes(sessoes, tmp_path)

    assert ler_sessoes(tmp_path) == sessoes

    csv_path = tmp_path / "sessoes.csv"
    assert _ler_primeira_linha(csv_path) == SESSOES_CABECALHO
    assert csv.DictReader(csv_path.open(encoding="utf-8")).__next__()["fim_data"] == ""


def test_registro_round_trip_preserves_recognition_result(tmp_path: Path) -> None:
    registros = [
        Registro(
            identificador="r-1",
            sessao_id="s-1",
            pessoa_id="p-1",
            status="confirmado",
            presente=True,
            recognition_result='{"score": 0.92, "identity": "João da Silva"}',
            registrado_em="2026-08-22T08:01:00",
        )
    ]

    salvar_registros(registros, tmp_path)

    assert ler_registros(tmp_path) == registros

    csv_path = tmp_path / "registros.csv"
    assert "recognition_result" in _ler_primeira_linha(csv_path)
