import json

with open('data/transacoes.json', 'r', encoding='utf-8') as f:
    transacoes = json.load(f)

tipos = {}
valores_negativos = 0
valores_positivos = 0

for t in transacoes:
    tipo = t.get('tipo', 'sem_tipo')
    valor = t.get('valor', 0)
    
    if tipo not in tipos:
        tipos[tipo] = 0
    tipos[tipo] += 1
    
    if valor < 0:
        valores_negativos += 1
    elif valor > 0:
        valores_positivos += 1

print(f'Total de transações: {len(transacoes)}')
print(f'Distribuição por tipo: {tipos}')
print(f'Valores positivos: {valores_positivos}')
print(f'Valores negativos: {valores_negativos}')

# Verificar algumas transações
print('\nPrimeiras 5 transações:')
for i, t in enumerate(transacoes[:5]):
    print(f'{i+1}. Tipo: {t.get("tipo")}, Valor: {t.get("valor")}, Descrição: {t.get("descricao", "")[:50]}...')