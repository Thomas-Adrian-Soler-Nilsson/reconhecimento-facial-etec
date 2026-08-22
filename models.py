from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Pessoa:
    """Pessoa cadastrada para uso no sistema de presença."""

    id: str
    nome: str
    turma_id: str
    matricula: str
    ativo: bool = True


@dataclass
class Turma:
    """Turma ou grupo de referência para vincular pessoas e sessões."""

    id: str
    nome: str
    ano_letivo: str
    descricao: str = ""


@dataclass
class Sala:
    """Sala física usada nas sessões de presença."""

    id: str
    nome: str
    capacidade: int
    local: str = ""


@dataclass
class Sessao:
    """Sessão de chamada, associada a uma turma e uma sala."""

    id: str
    turma_id: str
    sala_id: str
    inicio: str
    fim: str
    ativa: bool = True


@dataclass
class Registro:
    """Registro individual de presença de uma pessoa em uma sessão."""

    id: str
    sessao_id: str
    pessoa_id: str
    nome: str
    registrado_em: str
    presente: bool = True
