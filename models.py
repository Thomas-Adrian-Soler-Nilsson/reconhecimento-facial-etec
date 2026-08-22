from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pessoa:
    """Pessoa cadastrada no sistema de presença."""

    identificador: str
    nome: str
    categoria: str
    turma_ou_setor: str
    ativo: bool = True
    fotos: list[str] = field(default_factory=list)


@dataclass
class Turma:
    """Turma cadastrada para uso no sistema."""

    identificador: str
    nome: str
    categoria: str = ""
    ativo: bool = True


@dataclass
class Sala:
    """Sala cadastrada para uso no sistema."""

    identificador: str
    nome: str
    capacidade: int = 0
    ativo: bool = True


@dataclass
class Sessao:
    """Sessão de presença com início e fim opcionais."""

    identificador: str
    tipo_operacao: str
    sala: str
    turma_ou_setor: str
    responsavel_id: str
    inicio_data: str
    inicio_hora: str
    fim_data: str | None = None
    fim_hora: str | None = None


@dataclass
class Registro:
    """Registro de presença com status, presença e resultado de reconhecimento."""

    identificador: str
    sessao_id: str
    pessoa_id: str
    status: str
    presente: bool
    recognition_result: str
    registrado_em: str
