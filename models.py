from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pessoa:
    """Pessoa cadastrada no sistema de presença."""

    identificador: str
    nome: str
    categoria: str            # ex: "Aluno", "Professor", "Funcionário"
    turma_ou_setor: str       # identificador de uma Turma
    ativo: bool = True
    fotos: list[str] = field(default_factory=list)


@dataclass
class Turma:
    """Turma (ou setor/departamento, no caso de empresas) cadastrada no sistema."""

    identificador: str
    nome: str
    categoria: str = ""
    ativo: bool = True


@dataclass
class Sala:
    """Sala física (ou ambiente) onde sessões de presença acontecem."""

    identificador: str
    nome: str
    capacidade: int = 0
    ativo: bool = True


@dataclass
class Sessao:
    """Sessão de presença (ex: uma aula, uma reunião) com início e fim opcionais."""

    identificador: str
    tipo_operacao: str        # ex: "Chamada em grupo", "Entrada", "Saída"
    sala: str                 # identificador de uma Sala
    turma_ou_setor: str       # identificador de uma Turma
    responsavel_id: str       # identificador da Pessoa responsável (professor/coordenador)
    inicio_data: str
    inicio_hora: str
    fim_data: str | None = None
    fim_hora: str | None = None


@dataclass
class Registro:
    """Registro de presença de uma pessoa dentro de uma sessão específica."""

    identificador: str
    sessao_id: str
    pessoa_id: str
    status: str                  # ex: "Presente", "Ausente", "Atrasado"
    presente: bool
    recognition_result: str      # nome bruto retornado pelo DeepFace (auditoria)
    registrado_em: str           # timestamp ISO