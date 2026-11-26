# Sistema de Controle de Acesso RFID

Projeto acadêmico de Automação Industrial que integra Arduino, leitor RFID e uma aplicação desktop em Python. O sistema identifica cartões e verifica se o usuário pode acessar a área escolhida, conforme o perfil associado ao cartão.

## Objetivo

Desenvolver um sistema de controle de acesso com permissões configuráveis por perfil e área, aplicando conceitos de programação orientada a objetos e organização em camadas.

## Tecnologias e componentes

- Python e Tkinter/ttk para a aplicação e interface gráfica.
- Arduino Uno e leitor RFID-RC522 para ler os cartões.
- Comunicação serial a 9600 baud entre Arduino e Python.
- SQLite para armazenar usuários, cartões, perfis e áreas.

## Funcionalidades

- Cadastrar usuário com nome e cartão RFID.
- Editar o nome do usuário associado ao cartão selecionado.
- Alterar o perfil do cartão selecionado; cada cartão pode ter seu próprio perfil.
- Criar e editar perfis, escolhendo as áreas permitidas por caixas de seleção.
- Verificar acesso ao escolher uma área e aproximar o cartão do leitor.
- Bloquear ou reativar um cartão.
- Excluir somente o cartão selecionado ou excluir o usuário e todos os cartões associados a ele.

## Organização do projeto

```text
├── DATA/                               # Banco SQLite local
├── docs/                               # Documentação de arquitetura
├── src/
│   ├── dominio/                        # Cartão, perfil de acesso e área
│   ├── aplicacao/servicos/             # Autenticação e autorização
│   ├── infraestrutura/
│   │   ├── hardware/                   # Comunicação com o leitor RFID
│   │   └── persistencia/               # Repositório SQLite
│   └── apresentacao/                   # Interface gráfica e menu
├── main.py                             # Inicialização da interface
└── README.md
```

A aplicação usa `DATA/sistema.db` e cria as tabelas necessárias ao iniciar.

## Como executar

### Requisitos

- Python 3 com Tkinter.
- Arduino IDE, Arduino Uno e leitor RFID-RC522.
- Firmware do Arduino configurado para a comunicação serial esperada pela aplicação.

Instale a dependência Python:

```bash
pip install pyserial
```

Inicie a interface na pasta do projeto:

```bash
python main.py
```

Na janela, informe a porta serial do Arduino. O valor inicial é `COM11`; ajuste conforme a porta exibida no computador. A velocidade é 9600 baud.

## Fluxo básico

1. Na aba **Perfis e áreas**, cadastre áreas. Use **Novo perfil** para criar ou selecione um perfil para modificar suas permissões; **Excluir perfil** remove o perfil selecionado.
2. Na aba **Usuários e cartões**, cadastre o usuário e leia ou informe a UID do cartão.
3. Selecione o cadastro para alterar o nome do usuário ou o perfil daquele cartão.
4. Use **Excluir cartão** para remover apenas o cartão selecionado ou **Excluir usuário** para remover a pessoa e todos os cartões associados. As exclusões pedem confirmação.
5. Na aba **Controle de acesso**, escolha a área e clique em **Ler cartão e verificar**.

## Estado do projeto

Em desenvolvimento. O sistema já oferece gerenciamento de usuários, cartões, perfis e áreas pela interface gráfica. Histórico de acessos e outras melhorias podem ser desenvolvidos em etapas futuras.

Projeto acadêmico do curso Técnico em Automação Industrial.
