import sqlite3

conexao = sqlite3.connect("sistema.db")

tabelas = conexao.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("Tabelas encontradas:")

for tabela in tabelas:
    print("-", tabela[0])

conexao.close()