import sqlite3

DATABASE_PATH = 'data/financeiro.db'
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Listar tabelas
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tabelas = cursor.fetchall()
print('📋 Tabelas criadas:')
for tabela in tabelas:
    print(f'  - {tabela[0]}')

print('\n📊 Estatísticas:')

# Contar registros em cada tabela
tabelas_count = ['usuarios', 'empresas', 'bancos', 'contas_bancarias', 'cartoes_credito', 'contatos', 'categorias', 'transacoes', 'extratos']

for tabela in tabelas_count:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {tabela}')
        count = cursor.fetchone()[0]
        print(f'  {tabela}: {count} registros')
    except Exception as e:
        print(f'  {tabela}: erro - {e}')

# Estatísticas das transações
try:
    cursor.execute('SELECT COUNT(*), SUM(valor) FROM transacoes WHERE tipo="entrada"')
    entradas_count, entradas_total = cursor.fetchone()
    cursor.execute('SELECT COUNT(*), SUM(valor) FROM transacoes WHERE tipo="saida"')
    saidas_count, saidas_total = cursor.fetchone()

    print(f'\n💰 Transações migradas:')
    print(f'  Entradas: {entradas_count} transações, Total: R$ {entradas_total or 0:.2f}')
    print(f'  Saídas: {saidas_count} transações, Total: R$ {saidas_total or 0:.2f}')
    saldo = (entradas_total or 0) - (saidas_total or 0)
    print(f'  Saldo: R$ {saldo:.2f}')
except Exception as e:
    print(f'Erro nas estatísticas: {e}')

conn.close()