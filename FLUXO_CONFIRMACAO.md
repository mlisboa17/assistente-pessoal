# ✅ Fluxo Interativo de Confirmação de Documentos

## 🎯 Novo Fluxo de Extração

Após extrair um boleto/comprovante/transferência, o sistema **MOSTRA NA TELA** e pede confirmação:

```
┌─────────────────────────────────────┐
│  📄 BOLETO EXTRAÍDO                 │
├─────────────────────────────────────┤
│  💰 Valor: R$ 150.50                │
│  📤 Beneficiário: Empresa XYZ LTDA  │
│  📥 Pagador: João da Silva          │
│  📅 Data: 2024-12-31                │
│  📝 Descrição: Boleto - Empresa XYZ │
└─────────────────────────────────────┘
        ↓
    [MOSTRA DADOS]
        ↓
┌─────────────────────────────────────┐
│  ✅ CONFIRME OS DADOS               │
├─────────────────────────────────────┤
│  1️⃣  /confirmar ou /ok              │
│  2️⃣  /editar campo valor            │
│  3️⃣  /agenda /despesa /pago         │
│  4️⃣  /cancelar                      │
└─────────────────────────────────────┘
```

---

## 📋 Opções de Resposta

### 1️⃣ Confirmar Dados
```
Usuario: /confirmar
       ou /ok
       ou /sim
       ou /correto

Sistema: Mostra menu de opções
```

### 2️⃣ Editar Campo
```
Usuario: /editar valor 250.50
       ou /editar beneficiario "Nova Empresa"
       ou /editar data 2024-12-31

Sistema: Atualiza campo e mostra dados novamente
```

### 3️⃣ Selecionar Opções (Pode fazer TUDO junto!)
```
Usuario: /agenda                    (apenas agenda)
       ou /despesa                  (apenas despesa)
       ou /pago                     (apenas marcar pago)
       ou /agenda /despesa /pago    (as 3 opções!)
       ou /todas                    (atalho para as 3)

Sistema: Executa TODAS as opções selecionadas simultaneamente
```

### 4️⃣ Cancelar
```
Usuario: /cancelar
       ou /nao
       ou /no

Sistema: Descarta o documento
```

---

## 💾 As 3 Rotinas Simultâneas

### 📅 ROTINA 1: AGENDAR
```
Ação: Cria lembrete no calendário
Quando: Na data de vencimento do documento
O quê: Lembrete para pagar o boleto
Resultado: Você recebe notificação no dia ✅
```

### 💰 ROTINA 2: REGISTRAR COMO DESPESA
```
Ação: Adiciona ao módulo de finanças
Categoria: Automática (boleto → 'outros', luz → 'moradia', etc)
Data: Data do vencimento ou data atual
Resultado: Contabilizado nos gastos totais 💹
```

### ✅ ROTINA 3: MARCAR COMO PAGO
```
Ação: Atualiza status do boleto
Status: Pago = True
Data: Marca data de pagamento
Resultado: Removido da lista de pendências ✔️
```

---

## 🔄 Exemplos Práticos

### Exemplo 1: Confirmar Tudo
```
SISTEMA: 📄 BOLETO EXTRAÍDO
         💰 Valor: R$ 100.00
         📤 Beneficiário: Empresa XYZ
         [Mostra tudo...]

USUARIO: /confirmar

SISTEMA: Mostra menu de opções

USUARIO: /todas

SISTEMA: ✅ Agendado para 2024-12-31
         ✅ Registrado como despesa (categoria: outros)
         ✅ Marcado como pago
         
         Pronto! 3 ações executadas 🎉
```

### Exemplo 2: Editar e Depois Confirmar
```
USUARIO: /editar valor 250.00

SISTEMA: ✅ Campo 'valor' atualizado para: 250.0
         [Mostra dados novamente com novo valor]

USUARIO: /editar beneficiario "Novo Credenciado"

SISTEMA: ✅ Campo 'beneficiario' atualizado
         [Mostra dados novamente]

USUARIO: /agenda /despesa

SISTEMA: ✅ Agendado
         ✅ Registrado como despesa
         ⏭️ Não foi marcado como pago (você não pediu)
```

### Exemplo 3: Apenas Marcar Pago
```
SISTEMA: 📄 PIX EXTRAÍDO
         💰 Valor: R$ 50.00
         📲 Remetente: Maria Santos
         [Mostra dados...]

USUARIO: /pago

SISTEMA: ✅ Marcado como pago em 08/12/2024
         ⏭️ Não foi agendado
         ⏭️ Não foi registrado como despesa
```

---

## 🎛️ Campos Editáveis

| Campo | Formato | Exemplo |
|-------|---------|---------|
| `valor` | Número decimal | `/editar valor 150.50` |
| `beneficiario` | Texto | `/editar beneficiario "Empresa ABC"` |
| `pagador` | Texto | `/editar pagador "João Silva"` |
| `data` | DD/MM/YYYY ou YYYY-MM-DD | `/editar data 2024-12-31` |
| `descricao` | Texto | `/editar descricao "Descrição novo"` |

---

## 📊 Fluxo Completo

```
ARQUIVO ENVIADO
     ↓
EXTRAÇÃO (Boleto/PIX/Transferência)
     ↓
MOSTRA NA TELA
┌────────────────────────────────┐
│  Dados extraídos              │
│  ✅ Confirmar                 │
│  ✏️ Editar                    │
│  ❌ Cancelar                  │
└────────────────────────────────┘
     ↓
USER ESCOLHE UMA AÇÃO
     ↓
┌─────────────────┬──────────────┬──────────────┐
│  CANCELAR       │  EDITAR      │  CONFIRMAR   │
├─────────────────┼──────────────┼──────────────┤
│ Descarta doc    │ Mostra dados │ Menu opções  │
│ Fim ❌          │ Volta ao menu│    ↓         │
│                 │              │  USER SELEC. │
│                 │              │  (agenda?)   │
│                 │              │  (despesa?)  │
│                 │              │  (pago?)     │
│                 │              │    ↓         │
│                 │              │  EXECUTA     │
│                 │              │  TODAS ✅    │
│                 │              │  Fim ✔️      │
└─────────────────┴──────────────┴──────────────┘
```

---

## 🔐 Integração com Módulos

### Com Agenda
```python
# Cria lembrete automático
await agenda_module.handle('criar', [data, descricao], user_id)
```

### Com Finanças
```python
# Registra transação de saída
financas_module.registrar_transacao(
    tipo='saida',
    valor=150.50,
    categoria='outros',
    data='2024-12-31'
)
```

### Com Boletos
```python
# Atualiza status permanentemente
boleto.pago = True
salva_boleto(boleto)
```

---

## 💡 Vantagens

✅ **Sem Automação Agressiva**
- Usuário vê o que foi extraído antes de salvar
- Pode editar erros

✅ **Flexível**
- Pode escolher as 3 opções ou apenas algumas
- Combina como quiser

✅ **Eficiente**
- Executa todas as opções em paralelo
- Não precisa de múltiplas interações

✅ **Seguro**
- Validação de dados antes de salvar
- Possibilidade de cancelar

---

## ⚡ Comandos Rápidos

| Comando | O que faz |
|---------|-----------|
| `/confirmar`, `/ok`, `/sim` | Mostra menu de opções |
| `/editar campo valor` | Edita um campo |
| `/agenda` | Apenas agenda |
| `/despesa` | Apenas despesa |
| `/pago` | Apenas marcar pago |
| `/todas` | Agenda + Despesa + Pago |
| `/cancelar`, `/nao` | Cancela/descarta |

---

## 🎓 Casos de Uso

### Cenário 1: Boleto do mês
```
1. Usuário envia foto do boleto
2. Sistema extrai: R$ 150.00, Empresa XYZ, 31/12/2024
3. Usuário confirma
4. Usuário digita: /todas
5. Sistema:
   - Cria lembrete para 31/12
   - Registra despesa de R$ 150.00
   - Marca como pago
6. Pronto! ✅
```

### Cenário 2: Erro na extração
```
1. Usuário envia boleto
2. Sistema extrai: R$ 100.00 (estava errado, é 150.00)
3. Usuário não confirma, edita: /editar valor 150.00
4. Sistema mostra novo valor: R$ 150.00
5. Usuário confirma
6. Usuário escolhe opções: /agenda /despesa
   (não escolhe pago, pois ainda não pagou)
7. Pronto! ✅
```

### Cenário 3: Apenas registrar
```
1. Usuário envia comprovante de PIX
2. Sistema extrai: R$ 50.00 para Maria
3. Usuário apenas quer registrar como gasto
4. Digita: /despesa
5. Sistema registra na categoria 'outros'
6. Pronto! ✅
```

---

## 🔧 Configuração

No módulo de faturas/comprovantes:

```python
# Ativa sistema de confirmação
faturas = FaturasModule()
# Confirmação carregada automaticamente ✅

# Processar confirmação depois
resposta, dados = await faturas.processar_confirmacao(
    mensagem="/editar valor 200.00",
    user_id="usuario123"
)
```

---

## ❌ Troubleshooting

### Problema: "Nenhum documento pendente"
```
Solução: Envie um arquivo (PDF ou foto) primeiro
         O documento precisa ser extraído
```

### Problema: "Campo inválido"
```
Solução: Use campos válidos:
         valor, beneficiario, pagador, data, descricao
         Exemplo: /editar valor 150.00
```

### Problema: "Erro ao editar data"
```
Solução: Use formato YYYY-MM-DD ou DD/MM/YYYY
         /editar data 2024-12-31
         ou
         /editar data 31/12/2024
```

---

## 📈 Métricas de Sucesso

- ✅ 100% confirmação antes de salvar
- ✅ 0% perda de dados por automação
- ✅ 3 ações possíveis em 1 comando
- ✅ Suporta edição de 5 campos
- ✅ Interface clara e intuitiva

