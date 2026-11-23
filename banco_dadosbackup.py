
import sqlite3

CAMINHO_BANCO = "sistema.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    with conectar() as conexao:
        cursor = conexao.cursor()

        # Verifica se existe a tabela antiga.
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'usuarios'
        """)
        tabela_existe = cursor.fetchone() is not None

        if tabela_existe:
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]

            # Guarda a tabela antiga antes da migração.
            if "uid_rfid" in colunas:
                cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'usuarios_legado'
                """)
                legado_existe = cursor.fetchone() is not None

                if not legado_existe:
                    cursor.execute("""
                        ALTER TABLE usuarios
                        RENAME TO usuarios_legado
                    """)
                else:
                    raise RuntimeError(
                        "A tabela antiga e a tabela de arquivo "
                        "já existem. Verifique o banco antes de migrar."
                    )

        # Tabela de pessoas.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_usuario TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                data_cadastro TEXT NOT NULL
                DEFAULT (datetime('now', 'localtime'))            )
        """)

        # Tabela de cartões e tags RFID.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivos_rfid (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_dispositivo TEXT NOT NULL UNIQUE,
                uid_rfid TEXT NOT NULL UNIQUE,
                usuario_id INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                data_cadastro TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
                    ON DELETE CASCADE
            )
        """)


        # Áreas ou ambientes controlados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_area TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Perfis de acesso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfis_acesso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_perfil TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Áreas autorizadas para cada perfil
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_areas (
                perfil_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,

                PRIMARY KEY (perfil_id, area_id),

                FOREIGN KEY (perfil_id)
                    REFERENCES perfis_acesso(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (area_id)
                    REFERENCES areas(id)
                    ON DELETE CASCADE
            )
        """)

        # Perfis associados a cada cartão RFID
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivo_perfis (
                dispositivo_id INTEGER NOT NULL,
                perfil_id INTEGER NOT NULL,

                PRIMARY KEY (dispositivo_id, perfil_id),

                FOREIGN KEY (dispositivo_id)
                    REFERENCES dispositivos_rfid(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (perfil_id)
                    REFERENCES perfis_acesso(id)
                    ON DELETE CASCADE
            )
        """)

        # Áreas ou ambientes controlados.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_area TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Perfis de acesso.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfis_acesso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_perfil TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Áreas autorizadas para cada perfil.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_areas (
                perfil_id INTEGER NOT NULL,
                area_id INTEGER NOT NULL,

                PRIMARY KEY (perfil_id, area_id),

                FOREIGN KEY (perfil_id)
                    REFERENCES perfis_acesso(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (area_id)
                    REFERENCES areas(id)
                    ON DELETE CASCADE
            )
        """)

        # Perfis associados a cada cartão ou tag RFID.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivo_perfis (
                dispositivo_id INTEGER NOT NULL,
                perfil_id INTEGER NOT NULL,

                PRIMARY KEY (dispositivo_id, perfil_id),

                FOREIGN KEY (dispositivo_id)
                    REFERENCES dispositivos_rfid(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (perfil_id)
                    REFERENCES perfis_acesso(id)
                    ON DELETE CASCADE
            )
        """)

        # Migra os cadastros antigos sem apagar a tabela de arquivo.
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'usuarios_legado'
        """)
        legado_existe = cursor.fetchone() is not None

        if legado_existe:
            cursor.execute("""
                SELECT id, nome, uid_rfid, ativo, data_cadastro
                FROM usuarios_legado
            """)
            registros = cursor.fetchall()

            for registro in registros:
                id_antigo, nome, uid, ativo, data = registro

                codigo_usuario = f"USR-{id_antigo:03d}"
                codigo_dispositivo = f"RFID-{id_antigo:03d}"

                cursor.execute("""
                    INSERT OR IGNORE INTO usuarios
                    (id, codigo_usuario, nome, data_cadastro)
                    VALUES (?, ?, ?, ?)
                """, (id_antigo, codigo_usuario, nome, data))

                cursor.execute("""
                    INSERT OR IGNORE INTO dispositivos_rfid
                    (id, codigo_dispositivo, uid_rfid,
                     usuario_id, ativo, data_cadastro)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    id_antigo,
                    codigo_dispositivo,
                    uid.strip().upper(),
                    id_antigo,
                    ativo,
                    data
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


def definir_area_perfil(id_perfil, id_area, permitir=True):
    with conectar() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id FROM perfis_acesso WHERE id = ?
        """, (id_perfil,))

        if cursor.fetchone() is None:
            return False, "Perfil não encontrado."

        cursor.execute("""
            SELECT id FROM areas WHERE id = ?
        """, (id_area,))

        if cursor.fetchone() is None:
            return False, "Área não encontrada."

        if permitir:
            cursor.execute("""
                INSERT OR IGNORE INTO perfil_areas
                    (perfil_id, area_id)
                VALUES (?, ?)
            """, (id_perfil, id_area))

            if cursor.rowcount == 0:
                return True, "Essa permissão já estava configurada."

            return True, "Permissão adicionada com sucesso."

        cursor.execute("""
            DELETE FROM perfil_areas
            WHERE perfil_id = ? AND area_id = ?
        """, (id_perfil, id_area))

        return True, "Permissão removida com sucesso."


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


def associar_perfil_dispositivo(uid_rfid, id_perfil):
    uid_rfid = uid_rfid.strip().upper()

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                SELECT id FROM dispositivos_rfid
                WHERE uid_rfid = ?
            """, (uid_rfid,))

            dispositivo = cursor.fetchone()

            if dispositivo is None:
                return False, "Cartão não encontrado."

            cursor.execute("""
                SELECT id FROM perfis_acesso
                WHERE id = ? AND ativo = 1
            """, (id_perfil,))

            if cursor.fetchone() is None:
                return False, "Perfil inexistente ou inativo."

            cursor.execute("""
                INSERT OR IGNORE INTO dispositivo_perfis
                    (dispositivo_id, perfil_id)
                VALUES (?, ?)
            """, (dispositivo[0], id_perfil))

            if cursor.rowcount == 0:
                return True, "Esse perfil já está associado ao cartão."

        return True, "Perfil associado ao cartão com sucesso."

    except sqlite3.IntegrityError:
        return False, "Não foi possível associar o perfil."


def listar_perfis_dispositivo(uid_rfid):
    uid_rfid = uid_rfid.strip().upper()

    with conectar() as conexao:
        cursor = conexao.execute("""
            SELECT p.id, p.codigo_perfil, p.nome, p.ativo
            FROM perfis_acesso p
            JOIN dispositivo_perfis dp
                ON dp.perfil_id = p.id
            JOIN dispositivos_rfid d
                ON d.id = dp.dispositivo_id
            WHERE d.uid_rfid = ?
            ORDER BY p.nome
        """, (uid_rfid,))

        return cursor.fetchall()


def remover_perfil_dispositivo(uid_rfid, id_perfil):
    uid_rfid = uid_rfid.strip().upper()

    with conectar() as conexao:
        cursor = conexao.execute("""
            DELETE FROM dispositivo_perfis
            WHERE dispositivo_id = (
                SELECT id FROM dispositivos_rfid
                WHERE uid_rfid = ?
            )
            AND perfil_id = ?
        """, (uid_rfid, id_perfil))

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
                JOIN dispositivo_perfis dp
                    ON dp.dispositivo_id = d.id
                JOIN perfis_acesso p
                    ON p.id = dp.perfil_id
                JOIN perfil_areas pa
                    ON pa.perfil_id = p.id
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

        return True, "Usuário cadastrado com sucesso."

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
