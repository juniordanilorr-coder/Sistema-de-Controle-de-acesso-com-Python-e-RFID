# Sistema de Controle de Acesso RFID

Projeto acadêmico desenvolvido no curso de Técnico em Automação Industrial, utilizando Arduino, Python e banco de dados SQLite.

O sistema cadastra cartões RFID com perfis de acesso e controla quais áreas cada cartão pode acessar.

## Objetivo do projeto

Desenvolver um sistema de identificação e controle de acesso que integre hardware e software, utilizando um leitor RFID conectado a um Arduino e uma aplicação desktop desenvolvida em Python.

O projeto tem como cenário inicial uma simulação de controle de acesso ao um parque, podendo ser adaptado para outros ambientes.

## Tecnologias utilizadas

- **Python:** desenvolvimento da aplicação e gerenciamento das operações.
- **Arduino:** comunicação com o leitor RFID e aquisição das identificações.
- **MFRC522:** módulo responsável pela leitura dos cartões e tags RFID.
- **SQLite:** armazenamento de cartões, perfis de acesso e áreas.
- **Git e GitHub:** versionamento e gerenciamento do código-fonte.
- **Visual Studio Code:** ambiente de desenvolvimento.

## Componentes de hardware

- Arduino Uno.
- Módulo leitor RFID-RC522.
- Cartões RFID.
- Tags RFID tipo chaveiro.
- Cabos de conexão.

## Funcionalidades implementadas

- Cadastro de cartões com uma identificação própria.
- Cadastro individual de cartões, cada um com seu próprio perfil de acesso.
- Identificação de cartões e tags cadastrados.
- Autenticação e verificação de autorização.
- Listagem dos cartões cadastrados.
- Alteração da identificação do cartão.
- Bloqueio e reativação individual de cartões ou tags.
- Exclusão de cartões cadastrados.
- Controle da leitura RFID por comandos enviados pelo Python ao Arduino.

## Estrutura do banco de dados

O sistema utiliza SQLite para armazenar identificações, cartões RFID, perfis de acesso e áreas autorizadas. A autorização considera o UID e o perfil associado ao cartão.

Cada dispositivo possui uma UID única, status e perfil de acesso próprios. Um perfil pode liberar várias áreas, e a autorização é avaliada pelo cartão apresentado. O menu não oferece mais a associação de uma nova tag a um usuário existente.

## Comunicação entre Arduino e Python

A comunicação ocorre pela porta serial, utilizando velocidade de 9600 baud.

O Python envia comandos ao Arduino para controlar a leitura:

- `L`: libera a leitura de uma tag RFID.
- `P`: pausa a leitura RFID.

Quando uma tag é identificada, o Arduino envia sua UID ao Python, que realiza a consulta no banco de dados e executa a operação correspondente.

## Organização das pastas

```text
├── DATA/                        # Banco SQLite local já existente
├── docs/                         # Documentação do projeto
├── src/
│   ├── dominio/                  # Cartão, perfil de acesso e área
│   ├── aplicacao/servicos/       # Regras de autenticação e autorização
│   ├── infraestrutura/
│   │   ├── hardware/             # Comunicação com o leitor RFID
│   │   └── persistencia/         # Repositório SQLite
│   └── apresentacao/             # Menu de terminal
├── main.py                       # Ponto de entrada
└── README.md
```

Os arquivos de compatibilidade na raiz encaminham imports antigos para os módulos em `src/`. A base ativa continua em `DATA/sistema.db`; `sistema copy.db` e os arquivos `*backup.py` foram mantidos sem alterações.

## Como executar o projeto

### 1. Requisitos

- Python instalado.
- Arduino IDE instalado.
- Bibliotecas `pyserial` e `MFRC522`.
- Arduino Uno e módulo RFID-RC522.

### 2. Instalar a dependência Python

No terminal:

```bash
pip install pyserial
```

### 3. Preparar o Arduino

Carregue o código do leitor RFID na placa Arduino utilizando a Arduino IDE.

### 4. Configurar a porta serial

No arquivo `main.py`, configure a porta COM correspondente ao Arduino:

```python
PORTA = "COM11"
```

Altere o valor conforme a porta utilizada no computador.

### 5. Inicializar o banco de dados

Na pasta do projeto, execute:

```bash
python -m src.infraestrutura.persistencia.banco_dados
```

### 6. Executar o sistema

```bash
python main.py
```

## Desenvolvimento futuro

- Desenvolvimento de uma interface gráfica para gerenciamento do sistema.
- Implementação de histórico de acessos.
- Ampliação das funcionalidades de gerenciamento.
- Melhorias na apresentação e visualização das informações.

## Status do projeto

Em desenvolvimento.

Projeto acadêmico desenvolvido como atividade prática do curso de Técnico em Automação Industrial.

