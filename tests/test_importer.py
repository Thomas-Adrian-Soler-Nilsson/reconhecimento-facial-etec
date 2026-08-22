from __future__ import annotations

import csv
from pathlib import Path

import importer
from models import Pessoa
from repositories import ler_pessoas, ler_salas, ler_turmas, salvar_pessoas


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_people_import_rejects_a_missing_photo_and_keeps_the_batch_running(tmp_path: Path) -> None:
    csv_path = tmp_path / "people.csv"
    _write_csv(
        csv_path,
        ["identificador", "nome", "categoria", "turma_ou_setor", "caminho_foto"],
        [
            {
                "identificador": "a-1",
                "nome": "Ana",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(tmp_path / "missing.jpg"),
            }
        ],
    )

    summary = importer.import_people_csv(str(csv_path), str(tmp_path / "database"))

    assert summary.imported == 0
    assert summary.updated == 0
    assert summary.rejected == 1
    assert summary.errors == ["Linha 2: foto inexistente"]
    assert ler_pessoas(tmp_path / "database" / "presenca_local") == []


def test_people_import_validates_category_extension_and_stable_identifier(tmp_path: Path) -> None:
    valid_photo = tmp_path / "ana.jpg"
    valid_photo.write_bytes(b"photo")
    unsupported_photo = tmp_path / "ana.txt"
    unsupported_photo.write_text("not an image", encoding="utf-8")
    csv_path = tmp_path / "people.csv"
    _write_csv(
        csv_path,
        ["identificador", "nome", "categoria", "turma_ou_setor", "caminho_foto"],
        [
            {
                "identificador": "a-1",
                "nome": "Ana",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(valid_photo),
            },
            {
                "identificador": "a-2",
                "nome": "Bruno",
                "categoria": "visitante",
                "turma_ou_setor": "1A",
                "caminho_foto": str(valid_photo),
            },
            {
                "identificador": "a-3",
                "nome": "Carla",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(unsupported_photo),
            },
            {
                "identificador": "../a-4",
                "nome": "Diego",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(valid_photo),
            },
        ],
    )

    summary = importer.import_people_csv(str(csv_path), str(tmp_path / "database"))

    assert summary.imported == 1
    assert summary.rejected == 3
    assert summary.errors == [
        "Linha 3: categoria invalida",
        "Linha 4: extensao de foto nao suportada",
        "Linha 5: identificador invalido",
    ]
    assert ler_pessoas(tmp_path / "database" / "presenca_local")[0].identificador == "a-1"
    assert (tmp_path / "database" / "alunos" / "a-1" / "ana.jpg").exists()


def test_people_import_rejects_missing_required_fields_but_imports_other_rows(tmp_path: Path) -> None:
    photo = tmp_path / "ana.jpg"
    photo.write_bytes(b"photo")
    csv_path = tmp_path / "people.csv"
    _write_csv(
        csv_path,
        ["identificador", "nome", "categoria", "turma_ou_setor", "caminho_foto"],
        [
            {
                "identificador": "a-1",
                "nome": "",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(photo),
            },
            {
                "identificador": "a-2",
                "nome": "Beatriz",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(photo),
            },
        ],
    )

    summary = importer.import_people_csv(str(csv_path), str(tmp_path / "database"))

    assert (summary.imported, summary.rejected) == (1, 1)
    assert summary.errors == ["Linha 2: campo obrigatorio ausente"]
    assert [person.identificador for person in ler_pessoas(tmp_path / "database" / "presenca_local")] == ["a-2"]


def test_people_import_accumulates_photos_and_requires_confirmation_for_existing_people(
    tmp_path: Path,
) -> None:
    first_photo = tmp_path / "first" / "ana.jpg"
    first_photo.parent.mkdir()
    first_photo.write_bytes(b"first")
    second_photo = tmp_path / "second" / "ana.jpg"
    second_photo.parent.mkdir()
    second_photo.write_bytes(b"second")
    initial_csv = tmp_path / "initial.csv"
    _write_csv(
        initial_csv,
        ["identificador", "nome", "categoria", "turma_ou_setor", "caminho_foto"],
        [
            {
                "identificador": "a-1",
                "nome": "Ana",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(first_photo),
            },
            {
                "identificador": "a-1",
                "nome": "Ana",
                "categoria": "aluno",
                "turma_ou_setor": "1A",
                "caminho_foto": str(second_photo),
            },
        ],
    )

    initial_summary = importer.import_people_csv(str(initial_csv), str(tmp_path / "database"))

    assert initial_summary.imported == 1
    assert initial_summary.updated == 0
    person = ler_pessoas(tmp_path / "database" / "presenca_local")[0]
    assert len(person.fotos) == 2
    assert {item.name for item in (tmp_path / "database" / "alunos" / "a-1").iterdir()} == {
        "ana.jpg",
        "ana-1.jpg",
    }

    update_photo = tmp_path / "update.jpg"
    update_photo.write_bytes(b"update")
    update_csv = tmp_path / "update.csv"
    _write_csv(
        update_csv,
        ["identificador", "nome", "categoria", "turma_ou_setor", "caminho_foto"],
        [
            {
                "identificador": "a-1",
                "nome": "Ana Maria",
                "categoria": "aluno",
                "turma_ou_setor": "2A",
                "caminho_foto": str(update_photo),
            }
        ],
    )

    rejected_summary = importer.import_people_csv(str(update_csv), str(tmp_path / "database"))
    confirmed_summary = importer.import_people_csv(
        str(update_csv), str(tmp_path / "database"), confirm_updates=True
    )

    assert rejected_summary.rejected == 1
    assert rejected_summary.errors == ["Linha 2: atualizacao requer confirmacao"]
    assert confirmed_summary.updated == 1
    updated_person = ler_pessoas(tmp_path / "database" / "presenca_local")[0]
    assert updated_person.nome == "Ana Maria"
    assert updated_person.turma_ou_setor == "2A"
    assert len(updated_person.fotos) == 3


def test_room_and_class_imports_accept_valid_rows_and_reject_invalid_rows(tmp_path: Path) -> None:
    rooms_csv = tmp_path / "rooms.csv"
    _write_csv(
        rooms_csv,
        ["identificador", "nome", "capacidade"],
        [
            {"identificador": "sala-1", "nome": "Laboratorio", "capacidade": "30"},
            {"identificador": "sala-2", "nome": "Sem capacidade", "capacidade": ""},
        ],
    )
    classes_csv = tmp_path / "classes.csv"
    _write_csv(
        classes_csv,
        ["identificador", "nome", "categoria"],
        [
            {"identificador": "turma-1", "nome": "1A", "categoria": "ensino medio"},
            {"identificador": "turma-2", "nome": "", "categoria": "ensino medio"},
        ],
    )

    room_summary = importer.import_rooms_csv(str(rooms_csv), str(tmp_path / "database"))
    class_summary = importer.import_classes_csv(str(classes_csv), str(tmp_path / "database"))

    assert (room_summary.imported, room_summary.rejected) == (1, 1)
    assert (class_summary.imported, class_summary.rejected) == (1, 1)
    assert ler_salas(tmp_path / "database" / "presenca_local")[0].capacidade == 30
    assert ler_turmas(tmp_path / "database" / "presenca_local")[0].nome == "1A"


def test_list_active_employees_excludes_inactive_people_and_students(tmp_path: Path) -> None:
    storage_root = tmp_path / "database" / "presenca_local"
    salvar_pessoas(
        [
            Pessoa("f-1", "Fernanda", "funcionario", "RH", ativo=True),
            Pessoa("f-2", "Fabio", "funcionario", "TI", ativo=False),
            Pessoa("a-1", "Ana", "aluno", "1A", ativo=True),
        ],
        storage_root,
    )

    employees = importer.list_active_employees(str(tmp_path / "database"))

    assert employees == [Pessoa("f-1", "Fernanda", "funcionario", "RH", ativo=True)]
