
from banco_dados import listar_areas
from autentificacao import verificar_acesso

areas = listar_areas()

print("\n===== AMBIENTES DISPONÍVEIS =====")

for area in areas:
    id_area, codigo, nome, descricao, ativo = area
    status = "Ativa" if ativo == 1 else "Inativa"

    print(f"{id_area} - {nome} ({status})")

uid = input("\nDigite a UID do cartão: ").strip().upper()

try:
    id_area = int(input("Selecione o ID da área: "))
except ValueError:
    print("ID inválido.")
    raise SystemExit

resultado = verificar_acesso(uid, id_area)

print("\n===== RESULTADO DA AUTENTICAÇÃO =====")
print(f"Usuário: {resultado['usuario']}")
print(f"Área: {resultado['area']}")
print(f"Resultado: {resultado['mensagem']}")
