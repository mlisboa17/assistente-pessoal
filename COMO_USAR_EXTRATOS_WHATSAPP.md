# 🏦 Como Usar: Extrato Bancário via WhatsApp

## ✅ Implementação Completa!

Agora você pode processar extratos bancários diretamente pelo WhatsApp!

---

## 🚀 Como Iniciar

### 1️⃣ Inicie o Servidor Python (Flask)
```cmd
cd c:\Users\mlisb\OneDrive\Desktop\Projetos\assistente-pessoal-main\assistente-pessoal-main
python api_server.py
```
✅ Deve mostrar: `Running on http://127.0.0.1:8005`

### 2️⃣ Inicie o Bot WhatsApp (Node.js)
```cmd
cd c:\Users\mlisb\OneDrive\Desktop\Projetos\assistente-pessoal-main\assistente-pessoal-main\whatsapp_bot
node index.js
```
✅ Deve conectar e escanear QR Code

---

## 📱 Como Usar no WhatsApp

### 🏦 PROCESSAR EXTRATO BANCÁRIO

**Passo 1:** Anexe o PDF do extrato bancário

**Passo 2:** Na legenda/caption, escreva uma dessas palavras:
- `extrato`
- `bancário` / `bancario`
- `banco`
- `bb` / `bradesco` / `itau` / `santander` / `caixa` / `c6`

**Passo 3 (se tiver senha):** Adicione a senha na legenda:
```
extrato senha 024296
```

**Exemplo completo:**
```
📎 [anexar PDF]
💬 Legenda: "extrato c6 senha 024296"
```

### 💳 ANALISAR TARIFAS BANCÁRIAS

**Passo 1:** Anexe o PDF do extrato/comprovante

**Passo 2:** Na legenda, escreva:
- `tarifas`
- `tarifa`
- `taxas`

**Exemplo:**
```
📎 [anexar PDF]
💬 Legenda: "tarifas banco do brasil"
```

---

## 📊 O Que o Sistema Faz

### ✅ Processamento de Extrato:
1. 🔍 Identifica o banco automaticamente
2. 📑 Extrai todas as transações
3. 💾 Salva no banco de dados (`layouts_extratos.db`)
4. 🔄 Detecta duplicatas (não reprocessa)
5. 📱 Envia resumo formatado no WhatsApp:
   - Total de transações
   - Créditos e débitos
   - Saldo final
   - Data do período

### ✅ Análise de Tarifas:
1. 🔍 Identifica códigos de tarifa bancária
2. 📊 Separa tarifas de operações normais
3. 💰 Calcula total de tarifas por tipo
4. 📱 Envia breakdown detalhado:
   - Pacote de Serviços (9903)
   - Pacote PJ (13013)
   - Taxa Judicial (13373)
   - PIX (geralmente R$ 0,00 para PF)

---

## 🏦 Bancos Suportados

✅ **Bradesco** - Parser específico  
✅ **C6 Bank** - Layout mapeado (senha: 024296)  
✅ **Banco do Brasil** - Layout PJ mapeado  
🔄 **Outros bancos** - Sistema aprende automaticamente!

### Sistema de Aprendizado Automático:
- Na primeira vez: solicita mapeamento manual
- Nas próximas: reconhece pelo fingerprint
- Salva na `data/layouts_extratos.db`

---

## 📝 Exemplos de Uso

### Exemplo 1: Extrato BB sem senha
```
📎 extrato_bb_dezembro.pdf
💬 "extrato bb"
```

**Resposta:**
```
🏦 EXTRATO PROCESSADO ✅

📅 Período: 01/12/2024 - 31/12/2024
🏦 Banco: Banco do Brasil

📊 RESUMO:
💰 Créditos: R$ 252.640,00
💸 Débitos: R$ 5.750,00
💵 Saldo Final: R$ 246.890,00

📝 Transações: 117
🆕 Novas: 117
🔄 Duplicadas: 0

✅ Salvo no banco de dados!
```

### Exemplo 2: Extrato C6 com senha
```
📎 fatura_c6_novembro.pdf
💬 "extrato c6 senha 024296"
```

**Resposta:**
```
🏦 EXTRATO PROCESSADO ✅

📅 Período: 01/11/2024 - 30/11/2024
🏦 Banco: C6 Bank

📊 RESUMO:
💰 Créditos: R$ 12.450,00
💸 Débitos: R$ 8.320,50
💵 Saldo Final: R$ 4.129,50

📝 Transações: 34
🆕 Novas: 34
🔄 Duplicadas: 0

✅ Salvo no banco de dados!
```

### Exemplo 3: Análise de Tarifas
```
📎 comprovante_bb_tarifas.pdf
💬 "tarifas"
```

**Resposta:**
```
💳 ANÁLISE DE TARIFAS ✅

📅 Período: 01/12/2024 - 10/12/2024

💰 TOTAL DE TARIFAS: R$ 15.507,07

📋 DETALHAMENTO:

🔹 Pacote de Serviços (9903)
   Quantidade: 5
   Total: R$ 14.449,78

🔹 Pacote PJ (13013)
   Quantidade: 2
   Total: R$ 1.044,69

🔹 Taxa Judicial (13373)
   Quantidade: 1
   Total: R$ 12,60

ℹ️ PIX é GRATUITO para PF
ℹ️ PIX NÃO está incluído nos pacotes

✅ Análise completa!
```

---

## 🎯 Recursos Implementados

✅ Detecção automática de banco  
✅ Extração multi-estratégia (Tabula + pdfplumber)  
✅ Sistema de fingerprinting para layouts  
✅ Detecção de duplicatas  
✅ Suporte a PDFs protegidos por senha  
✅ Classificação de tarifas bancárias  
✅ Base de dados de códigos tarifários  
✅ Integração completa WhatsApp  
✅ Formatação automática de respostas  

---

## 🔧 Troubleshooting

### ❌ Erro: "Timeout no download"
**Solução:** Reenvie o PDF após 10 segundos

### ❌ Erro: "Layout desconhecido"
**Solução:** Sistema vai solicitar mapeamento interativo

### ❌ Erro: "Senha incorreta"
**Solução:** Verifique a senha e reenvie

### ❌ Servidor Flask não responde
**Solução:** Verifique se `python api_server.py` está rodando

### ❌ Bot WhatsApp desconectou
**Solução:** Reinicie `node index.js` e escaneie QR Code

---

## 📚 Arquivos Importantes

- `api_server.py` - Servidor Flask com endpoints `/process-extrato` e `/process-tarifas`
- `whatsapp_bot/index.js` - Bot WhatsApp com detecção automática
- `modules/extratobancario_importacao_discere.py` - Motor de extração
- `modules/tarifas_bancarias.py` - Classificação de tarifas
- `data/layouts_extratos.db` - Banco de layouts e transações
- `data/tarifas_bancarias.db` - Banco de códigos tarifários

---

## 🎉 Pronto para Usar!

Agora é só enviar PDFs de extratos pelo WhatsApp com a legenda apropriada!

**Dica:** Primeiro teste com um extrato pequeno para validar o sistema.

**Suporte:** Se encontrar problemas, verifique os logs no terminal do Flask e do Node.js.
