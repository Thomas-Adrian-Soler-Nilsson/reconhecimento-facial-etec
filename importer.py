"""CSV import services for the local attendance database."""

from __future__ import annotations

import csv
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from models import Pessoa, Sala, Turma
from repositories import (
    ler_pessoas,
    ler_salas,
    ler_turmas,
    salvar_pessoas,
    salvar_salas,
    salvar_turmas,
)


_SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PEOPLE_COLUMNS = [
    "identificador",
    "nome",
    "categoria",
    "turma_ou_setor",
    "caminho_foto",
]


@dataclass
class ImportSummary:
    imported: int = 0
    updated: int = 0
    rejected: int = 0
    errors: list[str] = field(default_factory=list)


def import_people_csv(path: str, database_root: str, confirm_updates: bool = False) -> ImportSummary:
    """Import people and their photos from UTF-8 CSV data."""

    summary = ImportSummary()
    csv_path = Path(path)
    root = Path(database_root)
    storage_root = root / "presenca_local"
    people = ler_pessoas(storage_root)
    people_by_id = {person.identificador: person for person in people}
    imported_ids: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in _PEOPLE_COLUMNS):
            raise ValueError("CSV de pessoas sem colunas obrigatorias")

        for line_number, row in enumerate(reader, start=2):
            values = {column: (row.get(column) or "").strip() for column in _PEOPLE_COLUMNS}
            error = _validate_person(values, csv_path.parent)
            if error:
                summary.rejected += 1
                summary.errors.append(f"Linha {line_number}: {error}")
                continue

            identifier = values["identificador"]
            existing = people_by_id.get(identifier)
            if existing and identifier not in imported_ids and not confirm_updates:
                summary.rejected += 1
                summary.errors.append(f"Linha {line_number}: atualizacao requer confirmacao")
                continue

            source_photo = _source_photo(values["caminho_foto"], csv_path.parent)
            destination = _copy_photo(source_photo, root, values["categoria"], identifier)
            photo_reference = destination.relative_to(root).as_posix()

            if existing is None:
                existing = Pessoa(
                    identificador=identifier,
                    nome=values["nome"],
                    categoria=values["categoria"],
                    turma_ou_setor=values["turma_ou_setor"],
                    fotos=[],
                )
                people.append(existing)
                people_by_id[identifier] = existing
                imported_ids.add(identifier)
                summary.imported += 1
            else:
                if identifier not in imported_ids:
                    existing.nome = values["nome"]
                    existing.categoria = values["categoria"]
                    existing.turma_ou_setor = values["turma_ou_setor"]
                    summary.updated += 1
                imported_ids.add(identifier)

            existing.fotos.append(photo_reference)

    salvar_pessoas(people, storage_root)
    return summary


def _validate_person(values: dict[str, str], csv_directory: Path) -> str | None:
    if any(not values[column] for column in _PEOPLE_COLUMNS):
        return "campo obrigatorio ausente"
    if not _IDENTIFIER_PATTERN.fullmatch(values["identificador"]):
        return "identificador invalido"
    if values["categoria"] not in {"aluno", "funcionario"}:
        return "categoria invalida"
    source_photo = _source_photo(values["caminho_foto"], csv_directory)
    if not source_photo.is_file():
        return "foto inexistente"
    if source_photo.suffix.lower() not in _SUPPORTED_IMAGE_EXTENSIONS:
        return "extensao de foto nao suportada"
    return None


def _source_photo(value: str, csv_directory: Path) -> Path:
    photo_path = Path(value)
    return photo_path if photo_path.is_absolute() else csv_directory / photo_path


def _copy_photo(source: Path, database_root: Path, category: str, identifier: str) -> Path:
    directory_name = "alunos" if category == "aluno" else "funcionarios"
    destination_dir = database_root / directory_name / identifier
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    suffix = 1
    while destination.exists():
        destination = destination_dir / f"{source.stem}-{suffix}{source.suffix}"
        suffix += 1
    shutil.copy2(source, destination)
    return destination


def import_rooms_csv(path: str, database_root: str, confirm_updates: bool = False) -> ImportSummary:
    """Import rooms from a UTF-8 CSV using the repository storage model."""

    return _import_simple_csv(
        path,
        database_root,
        ["identificador", "nome", "capacidade"],
        ler_salas,
        salvar_salas,
        lambda values: Sala(values["identificador"], values["nome"], int(values["capacidade"])),
        _validate_room,
        lambda room, values: _update_room(room, values),
        confirm_updates,
    )


def import_classes_csv(path: str, database_root: str, confirm_updates: bool = False) -> ImportSummary:
    """Import classes from a UTF-8 CSV using the repository storage model."""

    return _import_simple_csv(
        path,
        database_root,
        ["identificador", "nome", "categoria"],
        ler_turmas,
        salvar_turmas,
        lambda values: Turma(values["identificador"], values["nome"], values["categoria"]),
        _validate_required_record,
        lambda classroom, values: _update_classroom(classroom, values),
        confirm_updates,
    )


def list_active_employees(database_root: str) -> list[Pessoa]:
    """Return active employees for responsible-person selection."""

    storage_root = Path(database_root) / "presenca_local"
    return [person for person in ler_pessoas(storage_root) if person.ativo and person.categoria == "funcionario"]


def _import_simple_csv(
    path: str,
    database_root: str,
    columns: list[str],
    loader,
    saver,
    create_record,
    validate_record,
    update_record,
    confirm_updates: bool,
) -> ImportSummary:
    summary = ImportSummary()
    storage_root = Path(database_root) / "presenca_local"
    records = loader(storage_root)
    records_by_id = {record.identificador: record for record in records}
    imported_ids: set[str] = set()

    with Path(path).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in columns):
            raise ValueError("CSV sem colunas obrigatorias")

        for line_number, row in enumerate(reader, start=2):
            values = {column: (row.get(column) or "").strip() for column in columns}
            error = validate_record(values)
            if error:
                summary.rejected += 1
                summary.errors.append(f"Linha {line_number}: {error}")
                continue

            identifier = values["identificador"]
            existing = records_by_id.get(identifier)
            if existing is not None:
                if identifier in imported_ids:
                    summary.rejected += 1
                    summary.errors.append(f"Linha {line_number}: identificador duplicado")
                elif not confirm_updates:
                    summary.rejected += 1
                    summary.errors.append(f"Linha {line_number}: atualizacao requer confirmacao")
                else:
                    update_record(existing, values)
                    summary.updated += 1
                continue

            record = create_record(values)
            records.append(record)
            records_by_id[identifier] = record
            imported_ids.add(identifier)
            summary.imported += 1

    saver(records, storage_root)
    return summary


def _validate_required_record(values: dict[str, str]) -> str | None:
    if any(not value for value in values.values()):
        return "campo obrigatorio ausente"
    if not _IDENTIFIER_PATTERN.fullmatch(values["identificador"]):
        return "identificador invalido"
    return None


def _validate_room(values: dict[str, str]) -> str | None:
    error = _validate_required_record(values)
    if error:
        return error
    try:
        capacity = int(values["capacidade"])
    except ValueError:
        return "capacidade invalida"
    if capacity < 0:
        return "capacidade invalida"
    return None


def _update_room(room: Sala, values: dict[str, str]) -> None:
    room.nome = values["nome"]
    room.capacidade = int(values["capacidade"])


def _update_classroom(classroom: Turma, values: dict[str, str]) -> None:
    classroom.nome = values["nome"]
    classroom.categoria = values["categoria"]
