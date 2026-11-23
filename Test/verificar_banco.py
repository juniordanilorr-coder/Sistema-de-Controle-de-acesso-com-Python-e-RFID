import sqlite3

for arquivo in ["sistema.db", "sistema_backup.db"]:
    print(f"\n--- {arquivo} ---")

    conexao = sqlite3.connect(arquivo)
    tabelas = conexao.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    print("Tabelas:", tabelas)

    for (tabela,) in tabelas:
        if tabela in ("usuarios", "usuarios_legado", "dispositivos_rfid"):
            quantidade = conexao.execute(
                f'SELECT COUNT(*) FROM "{tabela}"'
            ).fetchone()[0]
            print(f"{tabela}: {quantidade} registros")

    conexao.close()