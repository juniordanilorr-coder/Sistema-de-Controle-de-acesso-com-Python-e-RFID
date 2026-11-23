"""Entidade de uma área controlada pelo sistema."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Area:
    id: int
    nome: str
    descricao: str = ""
    ativa: bool = True
