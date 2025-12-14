# 📚 Guia de Referência Rápida - Processamento de PDFs & Documentos

## 🎯 Resumo Executivo (30 segundos)

**O sistema processa:**
- ✅ **PDFs** (boletos, faturas, extratos) → Texto via pdfplumber/PyPDF2 ou IA (Gemini)
- ✅ **Imagens** (PIX, transferências, recibos) → OCR + Extrator Brasil especializado
- ✅ **Texto** (descrições) → Categorização automática

**Fluxo geral:**
```
Arquivo → Detectar tipo → Extrair dados (Regex/IA) → Validar → Armazenar JSON → Agendar
```

---

## 🔧 Módulos Principais

| Arquivo | Responsabilidade | Entrada | Saída |
|---------|------------------|---------|-------|
| `modules/faturas.py` | Boletos, Faturas, Extratos | PDF | JSON (boletos.json) |
| `modules/comprovantes.py` | PIX, Transferências, Recibos | Imagem/Texto | JSON (comprovantes.json) |
| `modules/extrator_brasil.py` | Especializado em docs brasileiros | Imagem/Bytes | Dados estruturados |
| `whatsapp_bot/index.js` | Interface WhatsApp | Mensagem + Arquivo | Resposta formatada |
| `api_server.py` | Backend REST | Requisição HTTP | Resposta JSON |

---

## 📋 Tabela de Métodos Principais

### **modules/faturas.py**

| Método | Entrada | Saída | Descrição |
|--------|---------|-------|-----------|
| `processar_arquivo()` | `arquivo: str, user_id: str` | `str (mensagem)` | Detecta tipo de arquivo e roteia |
| `_processar_pdf()` | `arquivo: str, user_id: str` | `str (mensagem)` | Processa PDF com fallbacks (Gemini → pdfplumber → PyPDF2) |
| `_extrair_com_gemini()` | `arquivo: str` | `Dict \| None` | Usa IA (Gemini Vision) para extrair dados |
| `_extrair_dados_boleto()` | `texto: str` | `Dict` | Regex para extrair estrutura |
| `_agendar_boleto()` | `boleto: Boleto, user_id: str` | `None` | Integra com módulo de agenda |

### **modules/comprovantes.py**

| Método | Entrada | Saída | Descrição |
|--------|---------|-------|-----------|
| `processar_imagem_brasil()` | `image_data: bytes, user_id: str` | `Dict` | Usa Extrator Brasil para análise |
| `processar_texto_comprovante()` | `texto: str, user_id: str` | `Dict` | Processa texto com regex e categorização |
| `_sugerir_categoria()` | `texto: str, destinatario: str` | `(str, float)` | Sugere categoria com confiança |
| `_converter_boleto()` | `dados: Dict, user_id: str` | `Dict` | Formata dados de boleto |
| `_converter_pix()` | `dados: Dict, user_id: str` | `Dict` | Formata dados de PIX |
| `_converter_transferencia()` | `dados: Dict, user_id: str` | `Dict` | Formata dados de transferência |

### **modules/extrator_brasil.py**

| Método | Entrada | Saída | Descrição |
|--------|---------|-------|-----------|
| `extrair_automatico()` | `image_data: bytes` | `Dict` | Detecta tipo (boleto/PIX/etc) automaticamente |
| `extrair_boleto()` | `image_data: bytes` | `DadosBoleto` | Extrai boleto de imagem |
| `extrair_pix_imagem()` | `image_data: bytes` | `DadosComprovantePix` | Extrai PIX de imagem |
| `extrair_transferencia()` | `image_data: bytes` | `DadosComprovanteTransferencia` | Extrai TED/DOC |

---

## 🔍 Métodos de Extração (Por Tipo)

### **BOLETO (PDF)**

```
PDF → GEMINI VISION (1ª opção, preciso)
   → pdfplumber (2ª opção, rápido)
   → PyPDF2 (3ª opção, fallback)

Resultado: TEXTO

REGEX:
├─ Valor: r'R\$\s*([\d.,]+)'
├─ Data: r'(\d{2}/\d{2}/\d{4})'
├─ Linha digitável: r'(\d{5}\.\d{5}\s\d{5}\.\d{5}\s\d{5}\.\d{5}\s\d\s\d{14})'
├─ Código barras: r'(\d{44})'
└─ Nomes: r'(Credor|Beneficiário):\s*([^\n]+)'
```

### **PIX (IMAGEM)**

```
IMAGEM → EXTRATOR BRASIL (automático)
      → EasyOCR (detecção de texto)
      → Regex padrão PIX

REGEX:
├─ Chave PIX: r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
├─ CPF: r'(\d{3}\.\d{3}\.\d{3}-\d{2})'
├─ Valor: r'R\$\s*([\d.,]+)'
└─ ID transação: r'([A-Z]\d{34})'
```

### **DARF/IMPOSTO (PDF)**

```
PDF → GEMINI VISION (melhor para extrair tipo)
   → pdfplumber/PyPDF2

REGEX:
├─ Tipo: "DARF" | "GPS" | "DAS" | "IPTU" | "IPVA"
├─ Período: r'(\d{2}/\d{4})'
├─ Código receita: r'Código Receita:\s*(\d+)'
├─ Valor: r'Valor:\s*R\$\s*([\d.,]+)'
└─ CNPJ/CPF: r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})'
```

---

## 💾 Estrutura de Dados

### **Boleto**
```python
{
    "id": "a3f5b2c1",                           # UUID[:8]
    "tipo": "boleto",                           # boleto|darf|gps|das|iptu|etc
    "valor": 150.50,                            # float
    "codigo_barras": "12345678901234...",       # 44 dígitos
    "linha_digitavel": "xxxxx.xxxxx ...",       # 47 dígitos formatados
    "vencimento": "15/12/2025",                 # DD/MM/YYYY
    "beneficiario": "Empresa XYZ",              # credor
    "pagador": "João Silva",                    # devedor
    "descricao": "Conta de água",               # o que está sendo cobrado
    "arquivo_origem": "boleto.pdf",             # nome original
    "user_id": "558197723921@s.whatsapp.net",  # quem enviou
    "extraido_em": "2025-12-01T10:30:45.123456",  # timestamp
    "pago": false,                              # status
    "agendado": true,                           # lembrete criado?
    "cnpj_cpf": "12.345.678/0001-90",          # opcional
    "periodo_apuracao": null,                   # para impostos
    "codigo_receita": null                      # para DARF/guias
}
```

### **Comprovante**
```python
{
    "id": "xyz456def",                          # hash MD5
    "tipo": "pix",                              # pix|boleto|transferencia|nf|recibo
    "valor": 50.00,                             # float
    "descricao": "PIX para João Silva",         # automático
    "data": "2025-12-01",                       # YYYY-MM-DD
    "destinatario": "João Silva",               # quem recebe
    "origem": "",                               # quem envia (se aplicável)
    "categoria_sugerida": "alimentacao",        # IA sugere
    "confianca": 0.85,                          # 0-1.0
    "user_id": "558197723921@s.whatsapp.net",  # quem enviou
    "status": "pendente",                       # pendente|confirmado|cancelado
    "criado_em": "2025-12-01T14:30:00.123456", # timestamp
    "texto_original": "Texto extraído...",      # para referência
    
    // Dados extras por tipo:
    "pix_dados": {
        "chave_pix": "12345678-1234-1234-1234-123456789012",
        "tipo_chave": "cpf",                    # cpf|cnpj|email|telefone|aleatoria
        "id_transacao": "E...",
        "banco": "Itaú"
    },
    "boleto_dados": {
        "linha_digitavel": "xxxxx.xxxxx ...",
        "codigo_barras": "12345...",
        "banco": "Bradesco",
        "nosso_numero": "1234567890123"
    },
    "transferencia_dados": {
        "tipo": "TED",
        "origem_banco": "Bradesco",
        "destino_banco": "Itaú",
        "id_transacao": "1234567890"
    }
}
```

---

## 🚀 Fluxo Típico (Passo a Passo)

### **Cenário 1: Usuário envia PDF de boleto**

```
1. Usuário: "Aqui está meu boleto de água" + arquivo.pdf
   └─ WhatsApp Bot recebe

2. whatsapp_bot/index.js
   ├─ Valida: extensão .pdf ✓
   ├─ Download do arquivo
   └─ POST para /api/processar_arquivo

3. api_server.py
   ├─ Roteia para: modules/faturas.py
   └─ Chama: processar_arquivo(arquivo, user_id)

4. modules/faturas.py → _processar_pdf()
   ├─ TENTA: _extrair_com_gemini(arquivo)
   │  ├─ Carrega: genai.GenerativeModel('gemini-1.5-flash')
   │  ├─ Converte: PDF → Imagem (pdf2image)
   │  ├─ Envia: Imagem + prompt → Gemini
   │  └─ Recebe: JSON {"tipo":"boleto", "valor":150.50, ...}
   │
   ├─ SE FALHAR: Tenta pdfplumber
   │  ├─ with pdfplumber.open(arquivo):
   │  ├─ Extrai: TEXTO (2500+ caracteres)
   │  └─ Vai para próximo passo
   │
   ├─ EXTRAI DADOS (se Gemini não teve sucesso)
   │  ├─ Chama: _extrair_dados_boleto(texto)
   │  ├─ Regex 1: Valor → r'R\$\s*([\d.,]+)' → "150,50"
   │  ├─ Regex 2: Data → r'(\d{2}/\d{2}/\d{4})' → "15/12/2025"
   │  ├─ Regex 3: Linha → xxxxx.xxxxx ... (47 dígitos)
   │  └─ Resultado: Dict {"valor": 150.5, "vencimento": "15/12/2025", ...}
   │
   ├─ CRIA OBJETO
   │  ├─ Boleto(
   │  │     id=uuid[:8],
   │  │     valor=150.5,
   │  │     linha_digitavel="...",
   │  │     vencimento="15/12/2025",
   │  │     beneficiario="Compesa",
   │  │     ...
   │  │  )
   │  └─ SALVA: boletos.json
   │
   ├─ AGENDA (se tiver data)
   │  ├─ Chama: _agendar_boleto(boleto, user_id)
   │  ├─ Cria lembrete 3 dias antes
   │  └─ Status: agendado=true
   │
   ├─ FORMATA RESPOSTA
   │  └─ ✅ Boleto Processado!
   │     ID: a3f5b2c1
   │     Valor: R$ 150,50
   │     ...

5. Retorna para WhatsApp
   └─ Usuário recebe mensagem com dados extraídos
```

### **Cenário 2: Usuário envia print de PIX**

```
1. Usuário: "Enviei PIX para João, aqui o comprovante" + imagem.jpg
   └─ WhatsApp Bot recebe

2. whatsapp_bot/index.js
   ├─ Valida: extensão .jpg ✓
   ├─ Download da imagem
   └─ POST para /api/processar_imagem

3. api_server.py
   ├─ Roteia para: modules/comprovantes.py
   └─ Chama: processar_imagem_brasil(image_data, user_id)

4. modules/comprovantes.py
   ├─ EXTRATOR BRASIL
   │  ├─ Chama: self._extrator_brasil.extrair_automatico(image_data)
   │  ├─ Detecta: "PIX" ✓
   │  ├─ Extrai: chave_pix, valor, data_hora, destino
   │  └─ Retorna: {"tipo": "pix", "dados": {...}}
   │
   ├─ CONVERTER
   │  ├─ Chama: _converter_pix(dados)
   │  ├─ Cria: ComprovanteExtraido(...)
   │  └─ Status: "pendente" (aguardando confirmação)
   │
   ├─ CATEGORIZAR
   │  ├─ Texto: "João Silva" (nenhuma palavra-chave)
   │  ├─ Score: 0/5 keywords
   │  ├─ Categoria: "outros"
   │  └─ Confiança: 0.0
   │
   ├─ SALVA PENDENTE
   │  └─ comprovantes_pendentes.json
   │
   └─ RESPOSTA USUÁRIO
      ├─ Mostra dados extraídos
      ├─ Sugere categoria (com 0% confiança)
      ├─ Pede confirmação
      └─ Botões: /sim, /nao, /categoria

5. Usuário responde:
   "/categoria alimentacao"
   └─ Atualiza e move para comprovantes.json
```

---

## 📊 Árvore de Decisão (Qual método usar?)

```
            ARQUIVO RECEBIDO
                   │
        ┌──────────┴──────────┐
        │                     │
      PDF?                  IMAGEM?
        │                     │
        ├─ Gemini? ✓         ├─ Extrator Brasil ✓
        │  └─ API disponível  │  └─ Detecta tipo
        │  └─ Ativa           │  └─ EasyOCR se needed
        │                     │
        ├─ pdfplumber? ✓      └─ Resultado estruturado
        │  └─ Rápido          
        │  └─ Preciso         
        │                     
        ├─ PyPDF2? ✓          
        │  └─ Fallback        
        │                     
        └─ Regex             
           └─ Padrões       
```

---

## 🔐 Validações Implementadas

| Campo | Validação | Exemplo |
|-------|-----------|---------|
| **Valor** | 0.01 ≤ x ≤ 1.000.000 | ✓ 150.50, ✗ 0.00, ✗ 999999999 |
| **Data** | Futuro (para boletos) | ✓ 15/12/2025, ✗ 01/01/2020 |
| **CNPJ** | Dígitos verificadores | validate_docbr.CNPJ().is_valid() |
| **CPF** | Dígitos verificadores | validate_docbr.CPF().is_valid() |
| **Linha digitável** | 47 dígitos | ✓ "xxxxx.xxxxx xxxx.xxxxx ...", ✗ "xxxx" |
| **Código barras** | 44 dígitos | ✓ "12345678901234567890...", ✗ "123456" |

---

## ⚡ Otimizações Implementadas

```
✅ Fallbacks em cascata (se IA falha, tenta tradicional)
✅ Cache de modelos Gemini (reutiliza conexão)
✅ Regex compilado (não recompila cada busca)
✅ Async/await para operações longas
✅ Salva JSON incremental (não reescreve tudo)
✅ Detecção automática de tipo (não precisa input)
✅ Categorização com scoring (inteligente)
✅ Agendamento integrado (reduz etapas)
```

---

## 🐛 Troubleshooting Rápido

| Problema | Causa | Solução |
|----------|-------|---------|
| "Não consegui ler o PDF" | PDF é imagem/escaneado | Ative Gemini Vision ou envie como foto |
| Valor extraído = 0 | Regex não encontrou R$ | Verifique se PDF tem texto (não imagem) |
| Data = hoje | Regex não encontrou data | DARF/Imposto pode não ter data visível |
| Boleto não agenda | Sem data de vencimento | Informe data manualmente via comando |
| Categoria errada | Sem keywords no nome | Treine modelo com mais exemplos |

---

## 📞 Referência Rápida de Comandos

```bash
# Ver boletos pendentes
/boletos

# Marcar boleto como pago
/pago a3f5b2c1

# Ver comprovantes pendentes
/comprovantes

# Confirmar comprovante
/sim

# Rejeitar comprovante
/nao

# Alterar categoria
/categoria alimentacao

# Reprocessar arquivo
/reprocessar a3f5b2c1
```

---

## 📌 Notas Importantes

```
1. ✅ Suporta múltiplos users (WhatsApp ID = user_id)
2. ✅ Dados persistem em JSON (sem banco de dados)
3. ✅ Google Oauth integrado (para agenda)
4. ⚠️  Gemini Vision consome tokens/créditos
5. ⚠️  EasyOCR é lento (considere usar para fallback)
6. 🔄 Sincronização Google Drive (em desenvolvimento)
7. 📊 Estatísticas de despesas (futuro)
```

---

## 🎓 Exemplos de Uso

### Ex. 1: Boleto de Água

```
INPUT: PDF "agua_novembro.pdf"
└─ pdfplumber → TEXTO
└─ Regex:
   - Valor: R$ 150,50 → 150.5
   - Data: 15/12/2025
   - Linha: 10497.56090 ...
   - Beneficiário: Compesa

OUTPUT: Boleto {id: "a3f5b2c1", tipo: "boleto", valor: 150.5, ...}
AGENDA: Lembrete em 12/12/2025
```

### Ex. 2: Comprovante PIX

```
INPUT: Imagem "pix_joao.jpg"
└─ Extrator Brasil → Detecção automática
└─ Detecta: PIX ✓
└─ Extrai:
   - Valor: R$ 50,00
   - Para: João Silva (CPF 123.456.789-10)
   - ID: E123456789012345...
   - Data: 2025-12-01 14:30

OUTPUT: Comprovante {id: "xyz456def", tipo: "pix", valor: 50, status: "pendente"}
AGUARDA: Confirmação + Categoria
```

### Ex. 3: DARF/Imposto

```
INPUT: PDF "darf_2025.pdf"
└─ Gemini Vision → JSON
└─ Detecta: DARF ✓
└─ Extrai:
   - Tipo: DARF
   - Período: 11/2025
   - Código Receita: 0320
   - Valor: R$ 500,00
   - Vencimento: 15/12/2025

OUTPUT: Boleto {id: "d4e5f6a7", tipo: "darf", valor: 500, periodo: "11/2025", ...}
AGENDA: Lembrete especial para DARF
```

