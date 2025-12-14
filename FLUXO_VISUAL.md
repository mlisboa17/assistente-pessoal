# 📊 Fluxo Visual de Processamento de Documentos

## 1️⃣ ENTRADA MÚLTIPLA

```
        ┌─────────────┐
        │  USUÁRIO    │
        │ WhatsApp    │
        └──────┬──────┘
               │
      ┌────────┼────────┐
      │        │        │
      ▼        ▼        ▼
   PDF 📄   IMAGEM 🖼️   TEXTO 📝
  Boleto    Comprovante  Descrição
  Fatura    PIX         Natureza
  Extrato   Transferência
```

---

## 2️⃣ FLUXO PDF (BOLETOS/FATURAS)

```
PDF → [Gemini Vision? ✅]
         ↓
    [Sucesso?]
    /        \
  SIM       NÃO
   │         │
   ↓         ▼
JSON  ┌─────────────┐
     │ pdfplumber? │
     └──────┬──────┘
            │
        [OK?]
       /     \
     SIM     NÃO
      │       │
      ↓       ▼
    TEXTO  ┌──────────┐
           │ PyPDF2? │
           └────┬────┘
                │
            [OK?]
           /     \
         SIM     NÃO
          │       │
          ↓       ↓
        TEXTO    ❌ FALHA
                 Impossível ler
```

---

## 3️⃣ PIPELINE DE EXTRAÇÃO

```
RAW TEXT / IMAGE
    │
    ├─→ [Extrator Brasil] ─→ Detecta: Boleto? PIX? DARF?
    │
    ├─→ [Regex Patterns]
    │   ├─→ R$ (Valor)
    │   ├─→ DD/MM/YYYY (Data)
    │   ├─→ Linha Digitável (47 dígitos)
    │   ├─→ Código de Barras (44 dígitos)
    │   └─→ Nomes (Beneficiário, Pagador)
    │
    ├─→ [Validação]
    │   ├─→ CPF/CNPJ válido? ✓
    │   ├─→ Valor razoável? (0.01 ≤ x ≤ 1M)
    │   └─→ Data no futuro? ✓
    │
    └─→ [ESTRUTURA FINAL]
        {
            "tipo": "boleto",
            "valor": 150.00,
            "vencimento": "15/12/2025",
            "beneficiario": "Compesa",
            ...
        }
```

---

## 4️⃣ ROTAS DE PROCESSAMENTO

```
ENTRADA
   │
   ├─ É PDF?  → modules/faturas.py
   │           └─→ _processar_pdf()
   │              ├─→ Gemini Vision (IA)
   │              ├─→ pdfplumber (Texto)
   │              ├─→ PyPDF2 (Fallback)
   │              └─→ _extrair_dados_boleto(regex)
   │
   ├─ É Imagem? → modules/comprovantes.py
   │             └─→ processar_imagem()
   │                ├─→ extrator_brasil.extrair_automatico()
   │                ├─→ EasyOCR (OCR)
   │                ├─→ Pyzbar (Código de barras)
   │                └─→ _detectar_tipo()
   │
   └─ É Texto? → processar_texto_comprovante()
                 └─→ Regex + Categorização
```

---

## 5️⃣ FLUXO COMPLETO DE VALIDAÇÃO

```
Usuário: /boleto [PDF]
         │
         ├─ [Arquivo existe?] ✓
         │
         ├─ [Extensão é .pdf?] ✓
         │
         ├─ [Tenta Gemini Vision]
         │  ├─ [ERRO: API offline]
         │  └─ [ERRO: Formato inválido]
         │
         ├─ [Tenta pdfplumber]
         │  ├─ ✓ [Texto extraído: 2.500 chars]
         │  │   └─ Processa Regex
         │  │
         │  └─ ✗ [PDF não tem texto embutido]
         │      └─ [Tenta PyPDF2]
         │
         ├─ [Extrai dados com Regex]
         │  ├─ Valor: R$ 150,00 ✓
         │  ├─ Data: 15/12/2025 ✓
         │  ├─ Linha: xxxxx.xxxxx... ✓
         │  └─ Beneficiário: Compesa ✓
         │
         ├─ [Cria objeto Boleto]
         │  ├─ ID: uuid[:8]
         │  ├─ user_id: 558197723921@...
         │  ├─ extraido_em: timestamp
         │  └─ agendado: false
         │
         ├─ [Salva em boletos.json]
         │
         ├─ [Tenta agendar]
         │  ├─ ✓ Lembrete criado
         │  └─ Status: agendado = true
         │
         └─ [Resposta formatada]
            ├─ 🤖 Extraído com IA (se Gemini)
            ├─ ID, Valor, Vencimento, etc.
            ├─ ✅ Agendado!
            └─ Comandos: /boletos, /pago
```

---

## 6️⃣ MATRIZ DE MÉTODOS

```
╔════════════════╦══════════╦═══════════╦═══════════╦═══════╗
║ TIPO DOCUMENTO ║ GEMINI   ║ PDFPLUM   ║ EXTRATOR  ║ REGEX ║
╠════════════════╬══════════╬═══════════╬═══════════╬═══════╣
║ Boleto (texto) ║    ✅    ║    ✅     ║    ✅     ║  ✅   ║
║ Boleto (img)   ║    ✅    ║    ❌     ║    ✅     ║  ❌   ║
║ DARF/Imposto   ║    ✅    ║    ✅     ║    ⚠️     ║  ✅   ║
║ Conta Luz/Água ║    ✅    ║    ✅     ║    ⚠️     ║  ✅   ║
║ PIX            ║    ✅    ║    ❌     ║    ✅     ║  ✅   ║
║ TED/DOC        ║    ✅    ║    ❌     ║    ✅     ║  ✅   ║
║ Nota Fiscal    ║    ✅    ║    ✅     ║    ⚠️     ║  ✅   ║
║ Extrato Banco  ║    ✅    ║    ✅     ║    ⚠️     ║  ✅   ║
╚════════════════╩══════════╩═══════════╩═══════════╩═══════╝

LEGENDA:
✅ = Implementado e testado
⚠️  = Parcialmente suportado
❌ = Não suportado neste método
```

---

## 7️⃣ PRIORIDADE DE PROCESSAMENTO

```
┌─ ORDEM DE TENTATIVA ─┐
│                      │
│  1️⃣ Gemini Vision    │ ← IA (MELHOR, mais lento, custoso)
│     (Se disponível)  │
│                      │
│  2️⃣ pdfplumber      │ ← Rápido, preciso, MELHOR fallback
│     (PDF → Texto)    │
│                      │
│  3️⃣ PyPDF2          │ ← Confiável, mais lento
│     (PDF → Texto)    │
│                      │
│  4️⃣ EasyOCR         │ ← Para PDFs escaneados (futuro)
│     (Imagem → Texto) │
│                      │
│  5️⃣ Regex           │ ← Extrair dados estruturados
│     (Texto → JSON)   │
│                      │
│  6️⃣ Fallback Manual  │ ← Pedir confirmação ao usuário
│                      │
└──────────────────────┘
```

---

## 8️⃣ CATEGORIZAÇÃO AUTOMÁTICA

```
INPUT: "Restaurante Almeida Silva"

┌─ SCORING ─────────────────────────────┐
│                                       │
│ alimentacao:                          │
│ ├─ "restaurante" ✓ +1                │
│ ├─ "silva" ✗                         │
│ └─ Score: 1 ✓                        │
│                                       │
│ transporte:                           │
│ ├─ "restaurante" ✗                   │
│ └─ Score: 0 ✗                        │
│                                       │
│ vestuario:                            │
│ ├─ "restaurante" ✗                   │
│ └─ Score: 0 ✗                        │
│                                       │
│ ⭐ VENCEDOR: alimentacao              │
│ Confiança: 20% (1/5 keywords)         │
│                                       │
└───────────────────────────────────────┘

OUTPUT:
{
    "categoria_sugerida": "alimentacao",
    "confianca": 0.20  ← 0 a 1.0
}
```

---

## 9️⃣ ARMAZENAMENTO HIERÁRQUICO

```
data/
├── boletos.json
│   ├── [ID] Boleto 1 (confirmado, pago=false)
│   ├── [ID] Boleto 2 (confirmado, agendado=true)
│   └── [ID] DARF 2025 (imposto)
│
├── comprovantes.json
│   ├── [ID] PIX para João Silva (confirmado)
│   ├── [ID] Transferência para Empresa (confirmado)
│   └── [ID] Nota Fiscal (pendente)
│
├── comprovantes_pendentes.json
│   └── {user_id}
│       └── [ID] PIX "Restaurante"
│           └── categoria: "alimentacao" (85% confiança)
│               ✋ Aguardando confirmação: /sim ou /nao
│
└── google_tokens/
    └── token_558197723921@s.whatsapp.net.pickle
        └── Integração com Google Agenda
```

---

## 🔟 PIPELINE VISUAL COMPLETO

```
RECEBERR PDF
    │
    ├─→ Download & Save
    │
    ├─→ File Type Check
    │
    ├─→ Open & Process
    │   ├─→ Try Gemini Vision API
    │   │   ├─→ Convert to Base64
    │   │   ├─→ Send to Gemini
    │   │   ├─→ Wait for Response
    │   │   └─→ Parse JSON (remove markdown)
    │   │
    │   ├─→ If Gemini fails or disabled
    │   │   ├─→ Try pdfplumber
    │   │   │   ├─→ Open PDF
    │   │   │   ├─→ Iterate pages
    │   │   │   ├─→ Extract text
    │   │   │   └─→ Combine all pages
    │   │   │
    │   │   └─→ If pdfplumber fails
    │   │       ├─→ Try PyPDF2
    │   │       ├─→ Open PDF
    │   │       ├─→ Read all pages
    │   │       └─→ Extract text
    │   │
    │   └─→ Have text? Process Regex
    │
    ├─→ Extract Fields (Regex)
    │   ├─→ VALOR: r'R\$\s*([\d.,]+)'
    │   │   └─→ Convert: "1.234,56" → 1234.56
    │   │
    │   ├─→ VENCIMENTO: r'(\d{2}/\d{2}/\d{4})'
    │   │   └─→ Parse date
    │   │
    │   ├─→ LINHA_DIGITAVEL: r'(\d{5}\.\d{5}\s...)'
    │   │   └─→ Format & normalize
    │   │
    │   ├─→ CODIGO_BARRAS: r'(\d{44})'
    │   │   └─→ Validate barcode
    │   │
    │   └─→ NOMES: r'(Credor|Beneficiário):\s*([^\n]+)'
    │       └─→ Clean whitespace
    │
    ├─→ Detect Type
    │   ├─→ Has "código de barras"? → boleto
    │   ├─→ Has "DARF"? → darf
    │   ├─→ Has "luz"? → conta_luz
    │   ├─→ Has "água"? → conta_agua
    │   └─→ Else → boleto
    │
    ├─→ Create Boleto Object
    │   ├─→ Generate ID (uuid[:8])
    │   ├─→ Set user_id (from WhatsApp)
    │   ├─→ Set timestamp
    │   ├─→ Set flags (pago, agendado)
    │   └─→ Validate fields
    │
    ├─→ Validate
    │   ├─→ Has valor? (> 0.01 and < 1M)
    │   ├─→ Has vencimento? (future date)
    │   ├─→ Has beneficiario?
    │   └─→ Has linha_digitavel or codigo_barras?
    │
    ├─→ Save to boletos.json
    │   ├─→ Serialize object
    │   ├─→ Append to array
    │   └─→ Write JSON file
    │
    ├─→ Schedule (if possible)
    │   ├─→ Has agenda_module?
    │   ├─→ Create reminder 3 days before
    │   └─→ Mark agendado = true
    │
    └─→ Format & Send Response
        ├─→ Show all data
        ├─→ Show agenda status
        ├─→ Show commands
        └─→ Done! ✅
```

---

## 1️⃣1️⃣ FLUXO DE COMPROVANTES (IMAGEM)

```
RECEBER IMAGEM (PIX/TED)
    │
    ├─→ Download & Save
    │
    ├─→ File Type Check (.jpg, .png)
    │
    ├─→ Use Extrator Brasil
    │   ├─→ Detecta tipo automaticamente
    │   ├─→ Valida CPF/CNPJ
    │   ├─→ Decodifica códigos
    │   └─→ Extrai dados estruturados
    │
    ├─→ Identify Type
    │   ├─→ Código de Barras? → boleto
    │   ├─→ Chave PIX? → pix
    │   ├─→ TED/DOC? → transferencia
    │   └─→ Else → desconhecido
    │
    ├─→ Convert to Standard Format
    │   ├─→ Boleto → _converter_boleto()
    │   ├─→ PIX → _converter_pix()
    │   └─→ Transferência → _converter_transferencia()
    │
    ├─→ Create ComprovanteExtraido Object
    │   ├─→ Generate ID (hash MD5)
    │   ├─→ Set user_id
    │   ├─→ Status: "pendente" (awaiting confirmation)
    │   └─→ Calculate confidence (0-1.0)
    │
    ├─→ Suggest Category
    │   ├─→ Match keywords
    │   ├─→ Calculate score
    │   └─→ Return (category, confidence)
    │
    ├─→ Save as PENDING
    │   └─→ comprovantes_pendentes.json
    │
    └─→ Ask User Confirmation
        ├─→ Show data
        ├─→ Show category
        ├─→ Show confidence
        └─→ Buttons: /sim ou /nao
```

---

## 1️⃣2️⃣ EXEMPLOS REAIS

### Exemplo 1: Boleto de Água

```
INPUT (PDF Text):
─────────────────
Companhia de Água - Compesa
Boleto de Cobrança
Código de Barras: 10497.56090 01234.567891 12345.678901 2 12345678901234
Linha Digitável: 10497.56090 01234.567891 12345.678901 2 12345678901234
Valor: R$ 150,50
Vencimento: 15/12/2025
Pagador: João Silva
Descrição: Água (Nov/2025)
─────────────────

REGEX EXTRACTION:
├─ Valor: R$ 150,50 → 150.50 ✓
├─ Data: 15/12/2025 ✓
├─ Linha: 10497.56090... ✓
├─ Beneficiário: Compesa ✓
└─ Tipo: "boleto" ✓

OUTPUT (JSON):
{
    "id": "a3f5b2c1",
    "tipo": "boleto",
    "valor": 150.50,
    "vencimento": "15/12/2025",
    "beneficiario": "Companhia de Água - Compesa",
    "pagador": "João Silva",
    "descricao": "Água (Nov/2025)",
    "linha_digitavel": "10497.56090 01234.567891 12345.678901 2 12345678901234",
    "codigo_barras": "10497560900123456789112345678901234567890",
    "user_id": "558197723921@s.whatsapp.net",
    "extraido_em": "2025-12-01T10:30:45.123456",
    "pago": false,
    "agendado": true
}

ARMAZENADO: data/boletos.json
AGENDADO: Lembrete para 12/12/2025 (3 dias antes)
```

### Exemplo 2: Comprovante PIX

```
INPUT (IMAGE - Screenshot):
─────────────────────────────
[PIX COMPROVANTE]
Tipo: Enviado
Valor: R$ 50,00
Hora: 14:30
Para: João Silva
CPF: 123.456.789-10
Banco: Itaú
Chave PIX: 12345678-1234-1234-1234-123456789012
ID da Transação: E123456789012345678901234567890
─────────────────────────────

EXTRATOR BRASIL:
├─ Detecta: "Enviado" → tipo_transacao ✓
├─ OCR: Texto da imagem ✓
├─ Valida CPF: 123.456.789-10 ✓
├─ Extrai Valor: R$ 50,00 → 50.0 ✓
└─ Extrai Data: 2025-12-01 ✓

SUGERIR CATEGORIA:
Input: "João Silva, PIX"
├─ alimentacao: score=0 (nenhuma keyword)
├─ transporte: score=0
├─ moradia: score=0
└─ Resultado: "outros" (0% confiança) ⚠️

OUTPUT (JSON - PENDENTE):
{
    "id": "xyz456def",
    "tipo": "pix",
    "valor": 50.00,
    "descricao": "PIX enviado para João Silva",
    "data": "2025-12-01",
    "destinatario": "João Silva",
    "categoria_sugerida": "outros",
    "confianca": 0.0,
    "status": "pendente",
    "criado_em": "2025-12-01T14:30:00.123456",
    "user_id": "558197723921@s.whatsapp.net",
    "pix_dados": {
        "chave_pix": "12345678-1234-1234-1234-123456789012",
        "id_transacao": "E123456789012345678901234567890",
        "tipo_transacao": "enviado",
        "banco": "Itaú"
    }
}

RESPOSTA USUÁRIO:
✅ PIX Analisado com Sucesso!

Para: João Silva (123.456.789-10)
Valor: R$ 50,00
Data: 01/12/2025 às 14:30
Transação: E123456789012345678901234567890

🤔 Qual é a categoria desta despesa?
A) 🍔 Alimentação
B) 🚗 Transporte
C) 🏠 Moradia
D) 🏥 Saúde
E) 🎮 Lazer
F) 👕 Vestuário
G) 💻 Tecnologia
H) 📚 Educação
I) ❓ Outro

Ou envie: /categoria alimentacao

⏳ Aguardando sua confirmação...
```

---

## 1️⃣3️⃣ DIAGRAMA DE DEPENDÊNCIAS

```
whatsapp_bot/index.js
    │
    └─→ api_server.py
        │
        ├─→ modules/faturas.py
        │   ├─→ pdfplumber
        │   ├─→ PyPDF2
        │   ├─→ pdf2image
        │   ├─→ google.generativeai (Gemini Vision)
        │   ├─→ modules/extrator_brasil.py
        │   │   ├─→ validate_docbr (CPF/CNPJ)
        │   │   ├─→ brazilcep
        │   │   ├─→ pyzbar (barcode decode)
        │   │   ├─→ easyocr
        │   │   └─→ PIL/Pillow
        │   │
        │   └─→ modules/agenda.py
        │       └─→ Criar lembretes
        │
        ├─→ modules/comprovantes.py
        │   ├─→ modules/extrator_brasil.py
        │   ├─→ easyocr
        │   └─→ PIL/Pillow
        │
        └─→ database/
            └─→ boletos.json
            └─→ comprovantes.json
            └─→ comprovantes_pendentes.json
```

---

## 🎯 Checklist de Funcionalidades

```
LEITURA DE PDFs:
  ✅ Suporta pdfplumber
  ✅ Suporta PyPDF2 (fallback)
  ✅ Suporta pdf2image (converter para imagem)
  ✅ Integração Gemini Vision (IA)
  🔄 EasyOCR (em desenvolvimento)

EXTRAÇÃO DE BOLETOS:
  ✅ Linha digitável (47 dígitos)
  ✅ Código de barras (44 dígitos)
  ✅ Valor monetário (R$)
  ✅ Data de vencimento
  ✅ Beneficiário
  ✅ Pagador
  ✅ Tipo (boleto, DARF, etc)
  ✅ CNPJ/CPF

PROCESSAMENTO DE COMPROVANTES:
  ✅ PIX (automático)
  ✅ Transferência (TED/DOC)
  ✅ Recibos genéricos
  ✅ Notas Fiscais (básico)
  ✅ Validação CPF/CNPJ
  ✅ Categorização automática
  ✅ Cálculo de confiança

ARMAZENAMENTO:
  ✅ JSON estruturado
  ✅ Status de pagamento
  ✅ Integração com agenda
  ✅ Histórico completo
  ⏳ Sincronização Google Drive

INTEGRAÇÃO:
  ✅ WhatsApp Bot (Baileys)
  ✅ Flask API (REST)
  ✅ Google Oauth (autenticação)
  🔄 Google Calendar (agendamento)
  🔄 Google Drive (backup)
```

