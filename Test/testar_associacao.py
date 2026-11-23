
from banco_dados import (
    listar_usuarios,
    listar_perfis,
    associar_perfil_dispositivo,
    listar_perfis_dispositivo
)

print("\n===== CARTÕES CADASTRADOS =====")

cartoes = listar_usuarios()

if not cartoes:
    print("Nenhum cartão cadastrado.")
    raise SystemExit

for id_usuario, nome, uid, ativo, data in cartoes:
    status = "Ativo" if ativo == 1 else "Bloqueado"

    print(f"Pessoa: {nome} | UID: {uid} | Status: {status}")


print("\n===== PERFIS DISPONÍVEIS =====")

perfis = listar_perfis()

if not perfis:
    print("Nenhum perfil cadastrado.")
    raise SystemExit

for id_perfil, codigo, nome, descricao, ativo in perfis:
    status = "Ativo" if ativo == 1 else "Inativo"
    print(f"ID: {id_perfil} | {nome} | {status}")


uid = input("\nDigite a UID do cartão: ").strip().upper()

if not any(cartao[2] == uid for cartao in cartoes):
    print("Cartão não encontrado.")
    raise SystemExit

try:
    id_perfil = int(input("Digite o ID do perfil: "))
except ValueError:
    print("ID inválido.")
    raise SystemExit

sucesso, mensagem = associar_perfil_dispositivo(
    uid, id_perfil
)

print("\nResultado:", mensagem)

if sucesso:
    print("\n===== PERFIS DO CARTÃO =====")

    for perfil in listar_perfis_dispositivo(uid):
        print(f"- {perfil[2]} ({perfil[1]})")
