
import time
import serial


from src.infraestrutura.persistencia.banco_dados import RepositorioRFID

from src.aplicacao.servicos.autenticacao import ServicoAutenticacao
from src.infraestrutura.hardware.leitor_rfid import LeitorRFID

PORTA = "COM11"
VELOCIDADE = 9600




class MenuSistema:
    def __init__(self, porta=PORTA, velocidade=VELOCIDADE):
        self.porta = porta
        self.velocidade = velocidade
        self.repositorio = RepositorioRFID()
        self.autenticador = ServicoAutenticacao(self.repositorio)

    def executar(self):
        print("Programa iniciado")
        self.repositorio.criar_tabelas()
        self.iniciar_sistema()

    def ler_uid(self, arduino):
        return LeitorRFID.ler_uid(arduino)


    def cadastrar_com_rfid(self, arduino):
        nome = input("Identificação do cartão (ex.: administrativo, eletricista): ").strip()

        if not nome:
            print("A identificação não pode ficar vazia.")
            return

        uid = self.ler_uid(arduino)
        sucesso, mensagem = self.repositorio.cadastrar_cartao(nome, uid)

        print(mensagem)


    def verificar_com_rfid(self, arduino):
        uid = self.ler_uid(arduino)
        resultado = self.autenticador.verificar_cartao(uid)

        print(f"\nUID: {uid}")
        print(f"Identificação: {resultado['usuario'] or 'Não cadastrado'}")
        print(f"Resultado: {resultado['mensagem']}")

    def verificar_acesso_com_rfid(self, arduino):
        areas = [
            area for area in self.repositorio.listar_areas()
            if area[4] == 1
        ]

        if not areas:
            print("Nenhuma área ativa cadastrada.")
            return

        print("\n===== SELECIONE O AMBIENTE =====")

        for area in areas:
            id_area, codigo, nome, descricao, ativo = area
            print(f"{id_area} - {nome}")

        try:
            id_area = int(input("\nEscolha a área: ").strip())
        except ValueError:
            print("ID inválido.")
            return

        area_selecionada = next(
            (area for area in areas if area[0] == id_area),
            None
        )

        if area_selecionada is None:
            print("Área inválida ou inativa.")
            return

        # Aguarda a leitura do cartão RFID
        uid = self.ler_uid(arduino)

        # Verifica as permissões do cartão para a área
        resultado = self.autenticador.verificar_acesso(uid, id_area)

        print("\n===== RESULTADO DO CONTROLE DE ACESSO =====")
        print(f"UID: {uid}")
        print(f"Identificação: {resultado['usuario'] or 'Não identificado'}")
        print(f"Área: {area_selecionada[2]}")
        print(f"Resultado: {resultado['mensagem']}")

    def gerenciar_perfil_cartao(self):
        uid = input("\nDigite a UID do cartão: ").strip().upper()
        if self.repositorio.consultar_usuario(uid) is None:
            print("Cartão não encontrado.")
            return

        perfil_atual = self.repositorio.listar_perfil_dispositivo(uid)

        if perfil_atual:
            print(
                f"\nPerfil atual: {perfil_atual[0]} - {perfil_atual[2]} "
                f"({'Ativo' if perfil_atual[3] == 1 else 'Inativo'})"
            )
        else:
            print("\nEste cartão ainda não possui um perfil definido.")
            perfis_antigos = self.repositorio.listar_perfis_legado_dispositivo(uid)
            if perfis_antigos:
                print("Vínculos antigos preservados (escolha apenas um perfil):")
                for perfil in perfis_antigos:
                    print(f"{perfil[0]} - {perfil[2]}")

        print("\n===== PERFIS ATIVOS DISPONÍVEIS =====")
        perfis = [perfil for perfil in self.repositorio.listar_perfis() if perfil[4] == 1]
        if not perfis:
            print("Nenhum perfil ativo cadastrado.")
            return

        for perfil in perfis:
            print(f"{perfil[0]} - {perfil[2]}")

        print("0 - Remover o perfil atual")
        try:
            escolha = int(input("\nInforme o ID do perfil desejado: ").strip())
        except ValueError:
            print("ID inválido.")
            return

        if escolha == 0:
            if self.repositorio.remover_perfil_dispositivo(uid):
                print("Perfil removido do cartão.")
            else:
                print("Nenhum perfil estava associado ou cartão não encontrado.")
            return

        if not any(perfil[0] == escolha for perfil in perfis):
            print("Perfil inexistente ou inativo.")
            return

        sucesso, mensagem = self.repositorio.definir_perfil_dispositivo(uid, escolha)
        print(mensagem)


    def mostrar_perfis(self):
        perfis = self.repositorio.listar_perfis()

        print("\n===== PERFIS DE ACESSO =====")

        if not perfis:
            print("Nenhum perfil cadastrado.")
            return

        for perfil in perfis:
            id_perfil, codigo, nome, descricao, ativo = perfil
            status = "Ativo" if ativo == 1 else "Inativo"
            print(f"\nID: {id_perfil} | Código: {codigo}")
            print(f"Identificação: {nome}")
            print(f"Descrição: {descricao or 'Não informada'}")
            print(f"Status: {status}")

            areas = self.repositorio.listar_areas_perfil(id_perfil)
            nomes_areas = [area[2] for area in areas]
            print("Áreas permitidas:", ", ".join(nomes_areas) if nomes_areas else "Nenhuma")


    def cadastrar_perfil_menu(self):
        print("\n===== CADASTRAR PERFIL =====")
        nome = input("Nome do perfil: ").strip()
        descricao = input("Descrição: ").strip()

        sucesso, mensagem = self.repositorio.cadastrar_perfil(nome, descricao)
        print(mensagem)


    def selecionar_perfil(self):
        perfis = self.repositorio.listar_perfis()

        if not perfis:
            print("Nenhum perfil cadastrado.")
            return None

        print("\n===== PERFIS CADASTRADOS =====")
        for perfil in perfis:
            id_perfil, codigo, nome, descricao, ativo = perfil
            status = "Ativo" if ativo == 1 else "Inativo"
            print(f"{id_perfil} - {nome} ({status})")

        try:
            id_perfil = int(input("Informe o ID do perfil: ").strip())
        except ValueError:
            print("ID inválido.")
            return None

        perfil_selecionado = next(
            (perfil for perfil in perfis if perfil[0] == id_perfil),
            None
        )

        if perfil_selecionado is None:
            print("Perfil não encontrado.")
            return None

        return perfil_selecionado


    def editar_perfil_menu(self):
        perfil = self.selecionar_perfil()
        if perfil is None:
            return

        id_perfil, codigo, nome_atual, descricao_atual, ativo = perfil
        print("\nDeixe um campo vazio para manter o valor atual.")
        novo_nome = input(f"Nome [{nome_atual}]: ").strip() or nome_atual
        nova_descricao = input(
            f"Descrição [{descricao_atual or 'Não informada'}]: "
        ).strip() or (descricao_atual or "")

        sucesso, mensagem = self.repositorio.editar_perfil(
            id_perfil, novo_nome, nova_descricao
        )
        print(mensagem)


    def alterar_status_perfil_menu(self):
        perfil = self.selecionar_perfil()
        if perfil is None:
            return

        id_perfil, codigo, nome, descricao, ativo = perfil
        novo_status = 0 if ativo == 1 else 1
        acao = "desativar" if ativo == 1 else "ativar"

        confirmacao = input(
            f"Confirma {acao} o perfil '{nome}'? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("Operação cancelada.")
            return

        sucesso, mensagem = self.repositorio.alterar_status_perfil(id_perfil, novo_status)
        print(mensagem)


    def configurar_areas_perfil_menu(self):
        perfil = self.selecionar_perfil()
        if perfil is None:
            return

        id_perfil, codigo, nome, descricao, ativo = perfil
        areas = self.repositorio.listar_areas()

        if not areas:
            print("Nenhuma área cadastrada.")
            return

        atuais = {area[0] for area in self.repositorio.listar_areas_perfil(id_perfil)}
        print(f"\n===== PERMISSÕES DO PERFIL: {nome} =====")
        print("Marque as áreas desejadas informando os IDs separados por vírgula.")
        print("Exemplo: 1, 3, 4, 5")

        for area in areas:
            id_area, codigo_area, nome_area, descricao_area, area_ativa = area
            marcado = "[X]" if id_area in atuais else "[ ]"
            status_area = "ativa" if area_ativa == 1 else "inativa"
            print(f"{marcado} {id_area} - {nome_area} ({status_area})")

        entrada = input(
            "\nIDs das áreas permitidas (ENTER para nenhuma; C para cancelar): "
        ).strip()
        if entrada.lower() == "c":
            print("Configuração cancelada.")
            return

        try:
            ids_selecionados = (
                set() if not entrada else
                {int(item.strip()) for item in entrada.split(",") if item.strip()}
            )
        except ValueError:
            print("Entrada inválida. Use apenas IDs separados por vírgula.")
            return

        ids_existentes = {area[0] for area in areas}
        if not ids_selecionados.issubset(ids_existentes):
            print("Um ou mais IDs informados não correspondem a áreas cadastradas.")
            return

        sucesso, mensagem = self.repositorio.atualizar_areas_perfil(id_perfil, ids_selecionados)
        print(mensagem)


    def gerenciar_perfis(self):
        while True:
            print("\n===== GERENCIAR PERFIS DE ACESSO =====")
            print("1 - Cadastrar perfil")
            print("2 - Listar perfis e permissões")
            print("3 - Editar perfil")
            print("4 - Configurar áreas permitidas")
            print("5 - Ativar ou desativar perfil")
            print("0 - Voltar ao menu principal")

            opcao = input("Escolha uma opção: ").strip()

            if opcao == "1":
                self.cadastrar_perfil_menu()
            elif opcao == "2":
                self.mostrar_perfis()
            elif opcao == "3":
                self.editar_perfil_menu()
            elif opcao == "4":
                self.configurar_areas_perfil_menu()
            elif opcao == "5":
                self.alterar_status_perfil_menu()
            elif opcao == "0":
                break
            else:
                print("Opção inválida.")


    def mostrar_cartoes(self):
        cartoes = self.repositorio.listar_cartoes()

        print("\n===== CARTÕES CADASTRADOS =====")

        if not cartoes:
            print("Nenhum cartão cadastrado.")
            return

        for cartao in cartoes:
            id_cartao, identificacao, uid, ativo, data = cartao
            status = "Ativo" if ativo == 1 else "Bloqueado"

            print(f"\nID: {id_cartao}")
            print(f"Identificação: {identificacao}")
            print(f"UID: {uid}")
            print(f"Status: {status}")
            print(f"Cadastro: {data}")

    def alterar_identificacao(self):
        uid = input("Digite a UID do cartão: ").strip().upper()
        novo_nome = input("Nova identificação: ").strip()

        if self.repositorio.renomear_identificacao_cartao(uid, novo_nome):
            print("Identificação atualizada com sucesso.")
        else:
            print("UID não encontrada ou identificação inválida.")

    def mudar_status(self):
        uid = input("Digite a UID do cartão: ").strip().upper()

        print("1 - Bloquear")
        print("2 - Reativar")
        opcao = input("Escolha: ").strip()

        if opcao not in ("1", "2"):
            print("Opção inválida.")
            return

        ativo = 0 if opcao == "1" else 1

        if self.repositorio.alterar_status_cartao(uid, ativo):
            print("Status atualizado com sucesso.")
        else:
            print("UID não encontrada.")

    def remover_cartao(self):
        uid = input("Digite a UID que deseja excluir: ").strip().upper()

        confirmacao = input(
            f"Confirma a exclusão do cadastro {uid}? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("Exclusão cancelada.")
            return

        if self.repositorio.excluir_cartao(uid):
            print("Cadastro excluído com sucesso.")
        else:
            print("UID não encontrada.")

    def iniciar_sistema(self):
        print("Entrou na função iniciar_sistema")

        try:
            with serial.Serial(self.porta, self.velocidade, timeout=1) as arduino:
                time.sleep(2)
                arduino.write(b'P')
                arduino.reset_input_buffer()

                while True:
                    print("\n===== SISTEMA RFID =====")
                    print("1 - Cadastrar cartão RFID")
                    print("2 - Verificar cartão")
                    print("3 - Listar cartões")
                    print("4 - Alterar identificação do cartão")
                    print("5 - Bloquear ou reativar cartão")
                    print("6 - Excluir cartão")
                    print("7 - Verificar acesso por área")
                    print("8 - Definir ou alterar perfil do cartão")
                    print("9 - Gerenciar perfis de acesso")
                    print("0 - Encerrar")

                    opcao = input("Escolha uma opção: ").strip()

                    if opcao == "1":
                        self.cadastrar_com_rfid(arduino)
                    elif opcao == "2":
                        self.verificar_com_rfid(arduino)
                    elif opcao == "3":
                        self.mostrar_cartoes()
                    elif opcao == "4":
                        self.alterar_identificacao()
                    elif opcao == "5":
                        self.mudar_status()
                    elif opcao == "6":
                        self.remover_cartao()
                    elif opcao == "7":
                        self.verificar_acesso_com_rfid(arduino)
                    elif opcao == "8":
                        self.gerenciar_perfil_cartao()
                    elif opcao == "9":
                        self.gerenciar_perfis()
                    elif opcao == "0":
                        print("Sistema encerrado.")
                        break
                    else:
                        print("Opção inválida.")

        except serial.SerialException as erro:
            print(f"Erro de comunicação: {erro}")
            print("Verifique a porta COM e feche o Monitor Serial.")

        except KeyboardInterrupt:
            print("\nSistema encerrado.")
