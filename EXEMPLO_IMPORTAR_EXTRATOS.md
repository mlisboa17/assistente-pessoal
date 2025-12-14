# 📊 EXEMPLO PRÁTICO - Importar Extratos

## Como Testar a Funcionalidade

### 1️⃣ Criar um arquivo CSV de exemplo

Crie um arquivo `extrato_teste.csv` com este conteúdo:

```csv
data,descricao,valor,saldo
01/12/2024,Salário,5000.00,15000.00
02/12/2024,Mercado Carrefour,250.50,14749.50
03/12/2024,Farmácia Drogasil,85.30,14664.20
04/12/2024,Uber para casa,45.00,14619.20
05/12/2024,Conta de Água,120.00,14499.20
06/12/2024,Netflix,49.90,14449.30
07/12/2024,Restaurante XYZ,180.00,14269.30
```

### 2️⃣ Testar via código Python

```python
from modules.financas import FinancasModule

# Criar instância
financas = FinancasModule()

# Conteúdo do CSV
csv_content = """data,descricao,valor,saldo
01/12/2024,Salário,5000.00,15000.00
02/12/2024,Mercado Carrefour,250.50,14749.50
03/12/2024,Farmácia Drogasil,85.30,14664.20"""

# Importar
resultado = financas.importar_extrato(
    conteudo=csv_content,
    tipo_extrato="csv_generico",
    nome_arquivo="extrato_dezembro.csv",
    user_id="seu_user_id"
)

print(resultado)
# Output:
# ✅ *Extrato Importado com Sucesso!*
# 📊 Resumo:
#    • Movimentos: 3
#    • Valor Total: R$ 5335.80
#    • Período: 2024-12-01 a 2024-12-03
```

### 3️⃣ Testar via WhatsApp Bot

Envie uma mensagem para o bot:
```
/importar extrato
```

O bot vai pedir para você enviar o arquivo CSV ou colar o conteúdo.

### 4️⃣ Verificar os resultados

Após importar, use:
```
/gastos - Para ver resumo de gastos
/categorias - Para ver por categoria
/saldo - Para ver saldo atual
```

## 📋 Formatos Suportados

### CSV Genérico
- Colunas: `data`, `descricao`, `valor`, `saldo` (opcional)
- Formato data: DD/MM/YYYY ou YYYY-MM-DD
- Formato valor: 1234.56 ou 1.234,56

### Itaú
- Formato específico do extrato Itaú
- Detectado automaticamente

### Cartão de Crédito
- Formato genérico para cartões
- Detectado automaticamente

## 🔧 Funcionalidades

✅ **Importação automática** de CSV
✅ **Detecção de tipo** de extrato
✅ **Categorização automática** dos gastos
✅ **Integração com finanças** existentes
✅ **Suporte a múltiplos formatos**
✅ **Validação de dados**
✅ **Relatórios detalhados**

## 🐛 Problemas Corrigidos

1. **Extração de valores**: Corrigido bug que não reconhecia formato americano (5000.00)
2. **Método _gerar_metadata**: Movido para classe base para evitar erros
3. **Detecção de delimitadores**: Melhorada para CSV brasileiro (;)

## 📈 Próximos Passos

- [ ] Suporte a PDF (OCR)
- [ ] Integração com bancos via API
- [ ] Reconciliação automática
- [ ] Relatórios avançados

---

**🎯 Status: TOTALMENTE FUNCIONAL**

Todos os testes passando! ✅