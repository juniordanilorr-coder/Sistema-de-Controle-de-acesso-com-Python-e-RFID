
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parents[3] / "DATA" / "sistema.db"


def conectar():
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    """Cria a estrutura do banco e migra associações antigas com segurança."""
    with conectar() as conexao:
        cursor = conexao.cursor()

        # Preserva a tabela antiga de usuários, caso ainda exista.
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'usuarios'
        """)
        tabela_usuarios_existe = cursor.fetchone() is not None

        if tabela_usuarios_existe:
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas_usuarios = [coluna[1] for coluna in cursor.fetchall()]

            if "uid_rfid" in colunas_usuarios:
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type = 'table' AND name = 'usuarios_legado'
                """)
                if cursor.fetchone() is None:
                    cursor.execute("ALTER TABLE usuarios RENAME TO usuarios_legado")
                else:
                    raise RuntimeError(
                        "A tabela antiga e a tabela usuarios_legado já existem. "
                        "Verifique o banco antes de migrar."
                    )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_usuario TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                data_cadastro TEXT NOT NULL
                    DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # O perfil fica diretamente no cartão: um cartão pode ter zero ou um perfil.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivos_rfid (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_dispositivo TEXT NOT NULL UNIQUE,
                uid_rfid TEXT NOT NULL UNIQUE,
                usuario_id INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                data_cadastro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_area TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfis_acesso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_perfil TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_areas (
                perfil_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,
                PRIMARY KEY (perfil_id, area_id),
                FOREIGN KEY (perfil_id)
                    REFERENCES perfis_acesso(id) ON DELETE CASCADE,
                FOREIGN KEY (area_id)
                    REFERENCES areas(id) ON DELETE CASCADE
            )
        """)

        # Adiciona a coluna na base existente sem recriar nem apagar cartões.
        cursor.execute("PRAGMA table_info(dispositivos_rfid)")
        colunas_dispositivos = [coluna[1] for coluna in cursor.fetchall()]
        if "perfil_id" not in colunas_dispositivos:
            cursor.execute("""
                ALTER TABLE dispositivos_rfid
                ADD COLUMN perfil_id INTEGER
                REFERENCES perfis_acesso(id) ON DELETE SET NULL
            """)

        # Migra a antiga relação muitos-para-muitos.
        # Uma associação antiga é migrada automaticamente. Se um cartão tinha
        # vários perfis, não escolhemos um arbitrariamente: os vínculos antigos
        # são preservados na tabela histórica para decisão do administrador.
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'dispositivo_perfis'
        """)
        tabela_antiga_existe = cursor.fetchone() is not None

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'dispositivo_perfis_historico'
        """)
        historico_existe = cursor.fetchone() is not None

        if tabela_antiga_existe and not historico_existe:
            cursor.execute("""
                SELECT dispositivo_id, perfil_id
                FROM dispositivo_perfis
                ORDER BY dispositivo_id, perfil_id
            """)
            associacoes = cursor.fetchall()
            por_dispositivo = {}
            for id_dispositivo, id_perfil in associacoes:
                por_dispositivo.setdefault(id_dispositivo, set()).add(id_perfil)

            for id_dispositivo, ids_perfis in por_dispositivo.items():
                if len(ids_perfis) == 1:
                    id_perfil = next(iter(ids_perfis))
                    cursor.execute("""
                        UPDATE dispositivos_rfid
                        SET perfil_id = ?
                        WHERE id = ? AND perfil_id IS NULL
                    """, (id_perfil, id_dispositivo))

            cursor.execute("""
                ALTER TABLE dispositivo_perfis
                RENAME TO dispositivo_perfis_historico
            """)

        # Migra os cadastros antigos de usuários sem apagar a tabela de arquivo.
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'usuarios_legado'
        """)
        legado_existe = cursor.fetchone() is not None

        if legado_existe:
            cursor.execute("""
                SELECT id, nome, uid_rfid, ativo, data_cadastro
                FROM usuarios_legado
            """)
            registros = cursor.fetchall()

            for id_antigo, nome, uid, ativo, data in registros:
                codigo_usuario = f"USR-{id_antigo:03d}"
                codigo_dispositivo = f"RFID-{id_antigo:03d}"

                cursor.execute("""
                    INSERT OR IGNORE INTO usuarios
                    (id, codigo_usuario, nome, data_cadastro)
                    VALUES (?, ?, ?, ?)
                """, (id_antigo, codigo_usuario, nome, data))

                cursor.execute("""
                    INSERT OR IGNORE INTO dispositivos_rfid
                    (id, codigo_dispositivo, uid_rfid, usuario_id, ativo, data_cadastro)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    id_antigo, codigo_dispositivo, uid.strip().upper(),
                    id_antigo, ativo, data
                ))

    print("Banco de dados inicializado com sucesso!")


def cadastrar_area(nome, descricao=""):
    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        return False, "O nome da área é obrigatório."

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO areas (codigo_area, nome, descricao)
                VALUES (?, ?, ?)
            """, ("PENDENTE", nome, descricao))

            id_area = cursor.lastrowid
            codigo = f"AREA-{id_area:03d}"

            cursor.execute("""
                UPDATE areas
                SET codigo_area = ?
                WHERE id = ?
            """, (codigo, id_area))

        return True, f"Área cadastrada: {codigo}"

    except sqlite3.IntegrityError:
        return False, "Já existe uma área com esse nome."


def listar_areas():
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT id, codigo_area, nome, descricao, ativo
            FROM areas
            ORDER BY id
        """)
        return cursor.fetchall()


def cadastrar_perfil(nome, descricao=""):
    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        return False, "O nome do perfil é obrigatório."

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO perfis_acesso
                    (codigo_perfil, nome, descricao)
                VALUES (?, ?, ?)
            """, ("PENDENTE", nome, descricao))

            id_perfil = cursor.lastrowid
            codigo = f"PERFIL-{id_perfil:03d}"

            cursor.execute("""
                UPDATE perfis_acesso
                SET codigo_perfil = ?
                WHERE id = ?
            """, (codigo, id_perfil))

        return True, f"Perfil cadastrado: {codigo}"

    except sqlite3.IntegrityError:
        return False, "Já existe um perfil com esse nome."


def listar_perfis():
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT id, codigo_perfil, nome, descricao, ativo
            FROM perfis_acesso
            ORDER BY id
        """)
        return cursor.fetchall()


def editar_perfil(id_perfil, nome, descricao=""):
    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        return False, "O nome do perfil é obrigatório."

    try:
        with conectar() as conexao:
            cursor = conexao.execute("""
                UPDATE perfis_acesso
                SET nome = ?, descricao = ?
                WHERE id = ?
            """, (nome, descricao, id_perfil))

            if cursor.rowcount == 0:
                return False, "Perfil não encontrado."

        return True, "Perfil atualizado com sucesso."

    except sqlite3.IntegrityError:
        return False, "Já existe um perfil com esse nome."


def excluir_perfil(id_perfil):
    """Exclui um perfil e remove sua associação dos cartões."""
    with conectar() as conexao:
        cursor = conexao.execute(
            "DELETE FROM perfis_acesso WHERE id = ?",
            (id_perfil,),
        )
        return cursor.rowcount > 0


def alterar_status_perfil(id_perfil, ativo):
    if ativo not in (0, 1):
        return False, "Status inválido."

    with conectar() as conexao:
        cursor = conexao.execute("""
            UPDATE perfis_acesso
            SET ativo = ?
            WHERE id = ?
        """, (ativo, id_perfil))

        if cursor.rowcount == 0:
            return False, "Perfil não encontrado."

    status = "ativado" if ativo == 1 else "desativado"
    return True, f"Perfil {status} com sucesso."


def atualizar_areas_perfil(id_perfil, ids_areas):
    """Substitui todas as áreas de um perfil em uma única transação."""
    try:
        ids_areas = {int(id_area) for id_area in ids_areas}
    except (TypeError, ValueError):
        return False, "A lista de áreas contém um identificador inválido."

    with conectar() as conexao:
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM perfis_acesso WHERE id = ?", (id_perfil,))
        if cursor.fetchone() is None:
            return False, "Perfil não encontrado."

        if ids_areas:
            placeholders = ",".join("?" for _ in ids_areas)
            cursor.execute(
                f"SELECT id FROM areas WHERE id IN ({placeholders})",
                tuple(ids_areas)
            )
            ids_existentes = {registro[0] for registro in cursor.fetchall()}
            if ids_existentes != ids_areas:
                return False, "Uma ou mais áreas não foram encontradas."

        cursor.execute(
            "DELETE FROM perfil_areas WHERE perfil_id = ?",
            (id_perfil,)
        )

        if ids_areas:
            cursor.executemany(
                "INSERT INTO perfil_areas (perfil_id, area_id) VALUES (?, ?)",
                [(id_perfil, id_area) for id_area in sorted(ids_areas)]
            )

    return True, f"Permissões atualizadas: {len(ids_areas)} área(s) configurada(s)."


def definir_area_perfil(id_perfil, id_area, permitir=True):
    """Compatibilidade com operações antigas de uma única área."""
    atuais = {area[0] for area in listar_areas_perfil(id_perfil)}
    if permitir:
        atuais.add(id_area)
    else:
        atuais.discard(id_area)
    return atualizar_areas_perfil(id_perfil, atuais)


def listar_areas_perfil(id_perfil):
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT a.id, a.codigo_area, a.nome, a.ativo
            FROM areas a
            JOIN perfil_areas pa ON pa.area_id = a.id
            WHERE pa.perfil_id = ?
            ORDER BY a.nome
        """, (id_perfil,))

        return cursor.fetchall()


def definir_perfil_dispositivo(uid_rfid, id_perfil):
    """Define ou substitui o único perfil de acesso de um cartão RFID."""
    uid_rfid = uid_rfid.strip().upper()
    if not uid_rfid:
        return False, "UID inválida."

    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id FROM dispositivos_rfid WHERE uid_rfid = ?",
            (uid_rfid,)
        )
        dispositivo = cursor.fetchone()
        if dispositivo is None:
            return False, "Cartão não encontrado."

        cursor.execute(
            "SELECT id FROM perfis_acesso WHERE id = ? AND ativo = 1",
            (id_perfil,)
        )
        if cursor.fetchone() is None:
            return False, "Perfil inexistente ou inativo."

        cursor.execute(
            "UPDATE dispositivos_rfid SET perfil_id = ? WHERE id = ?",
            (id_perfil, dispositivo[0])
        )

    return True, "Perfil definido para o cartão com sucesso."


def listar_perfil_dispositivo(uid_rfid):
    """Retorna o único perfil atual do cartão ou None."""
    uid_rfid = uid_rfid.strip().upper()
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT p.id, p.codigo_perfil, p.nome, p.ativo
            FROM dispositivos_rfid d
            LEFT JOIN perfis_acesso p ON p.id = d.perfil_id
            WHERE d.uid_rfid = ?
        """, (uid_rfid,))
        resultado = cursor.fetchone()
        if resultado is None or resultado[0] is None:
            return None
        return resultado


def listar_perfis_legado_dispositivo(uid_rfid):
    """Mostra vínculos antigos preservados durante a migração."""
    uid_rfid = uid_rfid.strip().upper()
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'dispositivo_perfis_historico'
        """)
        if cursor.fetchone() is None:
            return []

        cursor.execute("""
            SELECT DISTINCT p.id, p.codigo_perfil, p.nome, p.ativo
            FROM dispositivos_rfid d
            JOIN dispositivo_perfis_historico antigo
                ON antigo.dispositivo_id = d.id
            JOIN perfis_acesso p ON p.id = antigo.perfil_id
            WHERE d.uid_rfid = ?
            ORDER BY p.id
        """, (uid_rfid,))
        return cursor.fetchall()


def remover_perfil_dispositivo(uid_rfid):
    """Remove o perfil único do cartão, sem excluir o cartão."""
    uid_rfid = uid_rfid.strip().upper()
    with conectar() as conexao:
        cursor = conexao.execute("""
            UPDATE dispositivos_rfid
            SET perfil_id = NULL
            WHERE uid_rfid = ? AND perfil_id IS NOT NULL
        """, (uid_rfid,))
        return cursor.rowcount > 0


def consultar_area(id_area):
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT id, codigo_area, nome, descricao, ativo
            FROM areas
            WHERE id = ?
        """, (id_area,))

        return cursor.fetchone()


def dispositivo_tem_permissao(uid_rfid, id_area):
    uid_rfid = uid_rfid.strip().upper()

    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM dispositivos_rfid d
                JOIN perfis_acesso p ON p.id = d.perfil_id
                JOIN perfil_areas pa ON pa.perfil_id = p.id
                WHERE d.uid_rfid = ?
                  AND pa.area_id = ?
                  AND d.ativo = 1
                  AND p.ativo = 1
            )
        """, (uid_rfid, id_area))

        return bool(cursor.fetchone()[0])


def _criar_dispositivo(cursor, uid_rfid, id_usuario):
    cursor.execute("""
        INSERT INTO dispositivos_rfid
            (codigo_dispositivo, uid_rfid, usuario_id)
        VALUES (?, ?, ?)
    """, (f"PENDENTE-{uid_rfid}", uid_rfid, id_usuario))

    id_dispositivo = cursor.lastrowid
    codigo = f"RFID-{id_dispositivo:03d}"

    cursor.execute("""
        UPDATE dispositivos_rfid
        SET codigo_dispositivo = ?
        WHERE id = ?
    """, (codigo, id_dispositivo))

    return codigo

    
def cadastrar_usuario(nome, uid_rfid):
    nome = nome.strip()
    uid_rfid = uid_rfid.strip().upper()

    if not nome or not uid_rfid:
        return False, "Nome e UID são obrigatórios."

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO usuarios (codigo_usuario, nome)
                VALUES (?, ?)
            """, (f"PENDENTE-{uid_rfid}", nome))

            id_usuario = cursor.lastrowid

            codigo_usuario = f"USR-{id_usuario:03d}"

            cursor.execute("""
                UPDATE usuarios
                SET codigo_usuario = ?
                WHERE id = ?
            """, (codigo_usuario, id_usuario))

            _criar_dispositivo(cursor, uid_rfid, id_usuario)

        return True, "Cartão cadastrado com sucesso."

    except sqlite3.IntegrityError:
        return False, "Esta UID já está cadastrada."
    
def adicionar_cartao_usuario(uid_rfid, id_usuario):
    uid_rfid = uid_rfid.strip().upper()

    if not uid_rfid:
        return False, "UID inválida."

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT id FROM usuarios WHERE id = ?",
                (id_usuario,)
            )

            if cursor.fetchone() is None:
                return False, "Usuário não encontrado."

            codigo = _criar_dispositivo(
                cursor, uid_rfid, id_usuario
            )

        return True, f"Tag associada com sucesso. Código: {codigo}"

    except sqlite3.IntegrityError:
        return False, "Esta UID já está cadastrada."


def consultar_usuario(uid_rfid):
    uid_rfid = uid_rfid.strip().upper()

    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT u.id, u.nome, d.uid_rfid,
                   d.ativo, d.data_cadastro
            FROM usuarios u
            JOIN dispositivos_rfid d
                ON d.usuario_id = u.id
            WHERE d.uid_rfid = ?
        """, (uid_rfid,))

        return cursor.fetchone()


def alterar_status(uid_rfid, ativo):
    if ativo not in (0, 1):
        return False

    with conectar() as conexao:
        cursor = conexao.execute("""
            UPDATE dispositivos_rfid
            SET ativo = ?
            WHERE uid_rfid = ?
        """, (ativo, uid_rfid.strip().upper()))

        return cursor.rowcount > 0


def listar_cartoes():
    """Lista cartões com identificação e status próprios."""
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT d.id, u.nome, d.uid_rfid, d.ativo, d.data_cadastro
            FROM dispositivos_rfid d
            JOIN usuarios u ON u.id = d.usuario_id
            ORDER BY d.id
        """)
        return cursor.fetchall()


def listar_usuarios():
    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT u.id, u.nome, d.uid_rfid,
                   d.ativo, d.data_cadastro
            FROM usuarios u
            JOIN dispositivos_rfid d
                ON d.usuario_id = u.id
            ORDER BY u.id, d.id
        """)

        return cursor.fetchall()


def renomear_usuario(uid_rfid, novo_nome):
    novo_nome = novo_nome.strip()

    if not novo_nome:
        return False

    with conectar() as conexao:
        cursor = conexao.execute("""
            UPDATE usuarios
            SET nome = ?
            WHERE id = (
                SELECT usuario_id
                FROM dispositivos_rfid
                WHERE uid_rfid = ?
            )
        """, (novo_nome, uid_rfid.strip().upper()))

        return cursor.rowcount > 0


def contar_cartoes_usuario(id_usuario):
    with conectar() as conexao:
        cursor = conexao.execute(
            "SELECT COUNT(*) FROM dispositivos_rfid WHERE usuario_id = ?",
            (id_usuario,),
        )
        return cursor.fetchone()[0]


def excluir_usuario_por_id(id_usuario):
    """Exclui a pessoa e todos os cartões associados a ela."""
    with conectar() as conexao:
        cursor = conexao.execute(
            "DELETE FROM usuarios WHERE id = ?",
            (id_usuario,),
        )
        return cursor.rowcount > 0


def excluir_usuario(uid_rfid):
    uid_rfid = uid_rfid.strip().upper()

    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT usuario_id
            FROM dispositivos_rfid
            WHERE uid_rfid = ?
        """, (uid_rfid,))

        resultado = cursor.fetchone()

        if resultado is None:
            return False

        id_usuario = resultado[0]

        # Remove apenas o cartão ou a tag informada.
        conexao.execute("""
            DELETE FROM dispositivos_rfid
            WHERE uid_rfid = ?
        """, (uid_rfid,))

        # Remove a pessoa somente se não houver outros dispositivos.
        conexao.execute("""
            DELETE FROM usuarios
            WHERE id = ?
            AND NOT EXISTS (
                SELECT 1
                FROM dispositivos_rfid
                WHERE usuario_id = ?
            )
        """, (id_usuario, id_usuario))

        return True


if __name__ == "__main__":
    criar_tabelas()


class RepositorioRFID:
    """Objeto de acesso a dados para a aplicação."""

    conectar = staticmethod(conectar)
    criar_tabelas = staticmethod(criar_tabelas)
    cadastrar_area = staticmethod(cadastrar_area)
    listar_areas = staticmethod(listar_areas)
    cadastrar_perfil = staticmethod(cadastrar_perfil)
    listar_perfis = staticmethod(listar_perfis)
    editar_perfil = staticmethod(editar_perfil)
    alterar_status_perfil = staticmethod(alterar_status_perfil)
    excluir_perfil = staticmethod(excluir_perfil)
    atualizar_areas_perfil = staticmethod(atualizar_areas_perfil)
    definir_area_perfil = staticmethod(definir_area_perfil)
    listar_areas_perfil = staticmethod(listar_areas_perfil)
    definir_perfil_dispositivo = staticmethod(definir_perfil_dispositivo)
    listar_perfil_dispositivo = staticmethod(listar_perfil_dispositivo)
    listar_perfis_legado_dispositivo = staticmethod(listar_perfis_legado_dispositivo)
    remover_perfil_dispositivo = staticmethod(remover_perfil_dispositivo)
    dispositivo_tem_permissao = staticmethod(dispositivo_tem_permissao)
    cadastrar_usuario = staticmethod(cadastrar_usuario)
    adicionar_cartao_usuario = staticmethod(adicionar_cartao_usuario)
    consultar_usuario = staticmethod(consultar_usuario)
    alterar_status = staticmethod(alterar_status)
    listar_cartoes = staticmethod(listar_cartoes)
    listar_usuarios = staticmethod(listar_usuarios)
    renomear_usuario = staticmethod(renomear_usuario)
    excluir_usuario = staticmethod(excluir_usuario)
    contar_cartoes_usuario = staticmethod(contar_cartoes_usuario)
    excluir_usuario_por_id = staticmethod(excluir_usuario_por_id)


    def cadastrar_cartao(self, identificacao, uid_rfid):
        return self.cadastrar_usuario(identificacao, uid_rfid)

    def renomear_identificacao_cartao(self, uid_rfid, identificacao):
        return self.renomear_usuario(uid_rfid, identificacao)

    def alterar_status_cartao(self, uid_rfid, ativo):
        return self.alterar_status(uid_rfid, ativo)

    def excluir_cartao(self, uid_rfid):
        return self.excluir_usuario(uid_rfid)


    def consultar_cartao(self, uid_rfid):
        return consultar_usuario(uid_rfid)

    def consultar_perfil_cartao(self, uid_rfid):
        uid_rfid = uid_rfid.strip().upper()
        with conectar() as conexao:
            cursor = conexao.execute("""
                SELECT p.id, p.nome, p.ativo, pa.area_id
                FROM dispositivos_rfid d
                LEFT JOIN perfis_acesso p ON p.id = d.perfil_id
                LEFT JOIN perfil_areas pa ON pa.perfil_id = p.id
                WHERE d.uid_rfid = ?
                ORDER BY pa.area_id
            """, (uid_rfid,))
            registros = cursor.fetchall()
        if not registros or registros[0][0] is None:
            return None
        id_perfil, nome, ativo, _ = registros[0]
        areas = frozenset(registro[3] for registro in registros if registro[3] is not None)
        return id_perfil, nome, ativo, areas

    def consultar_area(self, id_area):
        return consultar_area(id_area)

    def cartao_tem_permissao(self, uid_rfid, id_area):
        return dispositivo_tem_permissao(uid_rfid, id_area)
