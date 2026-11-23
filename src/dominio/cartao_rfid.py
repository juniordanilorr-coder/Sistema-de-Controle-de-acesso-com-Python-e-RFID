"""Entidade do cartão; as permissões são verificadas pelo perfil do cartão."""

from dataclasses import dataclass
from typing import Optional

from .area import Area
from .perfil_acesso import PerfilAcesso


@dataclass(frozen=True)
class CartaoRFID:
    uid: str
    identificacao: str = ""
    ativo: bool = True
    perfil: Optional[PerfilAcesso] = None

    def pode_acessar(self, area: Area) -> bool:
        return (
            self.ativo
            and area.ativa
            and self.perfil is not None
            and self.perfil.permite_area(area.id)
        )
