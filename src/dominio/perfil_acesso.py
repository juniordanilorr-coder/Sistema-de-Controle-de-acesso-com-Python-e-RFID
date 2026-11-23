"""Perfil que define as áreas permitidas para um cartão."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PerfilAcesso:
    id: int
    nome: str
    areas_permitidas: frozenset[int] = field(default_factory=frozenset)
    ativo: bool = True

    def permite_area(self, id_area: int) -> bool:
        return self.ativo and id_area in self.areas_permitidas
