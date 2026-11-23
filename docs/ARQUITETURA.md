# Organização do sistema

O projeto foi dividido por responsabilidade para facilitar a evolução orientada a objetos.

- `src/dominio/`: entidades `CartaoRFID`, `PerfilAcesso` e `Area`; o cartão consulta seu perfil para decidir se pode acessar uma área.
- `src/aplicacao/servicos/`: serviço de autenticação e autorização, que coordena as regras do domínio e o repositório.
- `src/infraestrutura/persistencia/`: repositório SQLite usado como objeto pela aplicação; as funções antigas seguem disponíveis para compatibilidade.
- `src/infraestrutura/hardware/`: comunicação serial com o Arduino.
- `src/apresentacao/`: menu de terminal que chama os serviços e operações do banco.

Cada cartão pode ter um perfil de acesso. Um perfil pode ser reutilizado em vários cartões e autorizar várias áreas. O menu não inclui a operação de associar uma nova tag a uma pessoa já cadastrada.
