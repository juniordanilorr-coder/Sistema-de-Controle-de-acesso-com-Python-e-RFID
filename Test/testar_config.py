
from banco_dados import (
    cadastrar_area,
    listar_areas,
    cadastrar_perfil,
    listar_perfis,
    definir_area_perfil,
    listar_areas_perfil
)


def garantir_area(nome):
    areas = listar_areas()

    existente = next(
        (area for area in areas if area[2].lower() == nome.lower()),
        None
    )

    if existente:
        return existente[0]

    sucesso, mensagem = cadastrar_area(
        nome, "Ambiente de demonstração"
    )

    print(mensagem)

    if sucesso:
        return next(
            area[0] for area in listar_areas()
            if area[2].lower() == nome.lower()
        )

    raise RuntimeError(mensagem)


def garantir_perfil(nome):
    perfis = listar_perfis()

    existente = next(
        (perfil for perfil in perfis if perfil[2].lower() == nome.lower()),
        None
    )

    if existente:
        return existente[0]

    sucesso, mensagem = cadastrar_perfil(
        nome, "Perfil de demonstração"
    )

    print(mensagem)

    if sucesso:
        return next(
            perfil[0] for perfil in listar_perfis()
            if perfil[2].lower() == nome.lower()
        )

    raise RuntimeError(mensagem)


# Cadastrar ou recuperar áreas
nomes_areas = [
    "Entrada principal",
    "Escritórios",
    "Manutenção",
    "Sala elétrica",
    "Casa de máquinas",
    "Almoxarifado"
]

areas = {
    nome: garantir_area(nome)
    for nome in nomes_areas
}


# Cadastrar ou recuperar perfis
administrativo = garantir_perfil("Administrativo")
manutencao = garantir_perfil("Manutenção elétrica")


# Configurar permissões
permissoes = {
    administrativo: [
        "Entrada principal",
        "Escritórios"
    ],
    manutencao: [
        "Entrada principal",
        "Manutenção",
        "Sala elétrica",
        "Casa de máquinas"
    ]
}

for id_perfil, nomes in permissoes.items():
    for nome_area in nomes:
        sucesso, mensagem = definir_area_perfil(
            id_perfil,
            areas[nome_area]
        )
        print(mensagem)


# Mostrar resultado
print("\n===== ÁREAS CADASTRADAS =====")

for area in listar_areas():
    print(area[1], "-", area[2])


print("\n===== PERFIS E PERMISSÕES =====")

for perfil in listar_perfis():
    print(f"\n{perfil[2]}:")

    for area in listar_areas_perfil(perfil[0]):
        print(" -", area[2])

print("\nConfiguração concluída!")
