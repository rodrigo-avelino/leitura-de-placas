from src.config.db import criarTabela
# aqui criamos o banco de dados (arquivo SQLite) e as tabelas se ainda não existirem
if __name__ == "__main__":
    criarTabela()
    print("banco criado")