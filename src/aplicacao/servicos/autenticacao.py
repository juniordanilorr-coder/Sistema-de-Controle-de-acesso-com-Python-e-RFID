"""Serviço de autenticação e autorização dos cartões RFID."""

from src.dominio import Area, CartaoRFID, PerfilAcesso
from src.infraestrutura.persistencia.banco_dados import RepositorioRFID


class ServicoAutenticacao:
    def __init__(self, repositorio=None):
        self.repositorio = repositorio or RepositorioRFID()

    def verificar_cartao(self, uid):
        cartao = self.repositorio.consultar_cartao(uid)

        if cartao is None:
            return {
                "autorizado": False,
                "mensagem": "Cartão não cadastrado",
                "usuario": None,
            }

        if cartao[3] == 0:
            return {
                "autorizado": False,
                "mensagem": "Cartão bloqueado",
                "usuario": cartao[1],
            }

        return {
            "autorizado": True,
            "mensagem": "Acesso autorizado",
            "usuario": cartao[1],
        }

    def verificar_acesso(self, uid, id_area):
        cartao = self.repositorio.consultar_cartao(uid)

        if cartao is None:
            return {
                "autorizado": False,
                "mensagem": "Cartão não cadastrado",
                "usuario": None,
                "area": None,
            }

        if cartao[3] == 0:
            return {
                "autorizado": False,
                "mensagem": "Cartão bloqueado",
                "usuario": cartao[1],
                "area": None,
            }

        area = self.repositorio.consultar_area(id_area)
        if area is None:
            return {
                "autorizado": False,
                "mensagem": "Área não encontrada",
                "usuario": cartao[1],
                "area": None,
            }

        if area[4] == 0:
            return {
                "autorizado": False,
                "mensagem": "Área desativada",
                "usuario": cartao[1],
                "area": area[2],
            }

        dados_perfil = self.repositorio.consultar_perfil_cartao(uid)
        perfil = None
        if dados_perfil is not None:
            id_perfil, nome_perfil, perfil_ativo, areas_permitidas = dados_perfil
            perfil = PerfilAcesso(
                id=id_perfil,
                nome=nome_perfil,
                areas_permitidas=areas_permitidas,
                ativo=bool(perfil_ativo),
            )
        cartao_entidade = CartaoRFID(
            uid=uid.strip().upper(),
            identificacao=cartao[1],
            ativo=bool(cartao[3]),
            perfil=perfil,
        )
        area_entidade = Area(
            id=area[0],
            nome=area[2],
            descricao=area[3] or "",
            ativa=bool(area[4]),
        )
        permitido = cartao_entidade.pode_acessar(area_entidade)
        return {
            "autorizado": permitido,
            "mensagem": (
                "Acesso autorizado"
                if permitido
                else "Cartão sem permissão para esta área"
            ),
            "usuario": cartao[1],
            "area": area[2],
        }


_servico_padrao = ServicoAutenticacao()


def verificar_cartao(uid):
    return _servico_padrao.verificar_cartao(uid)


def verificar_acesso(uid, id_area):
    return _servico_padrao.verificar_acesso(uid, id_area)
