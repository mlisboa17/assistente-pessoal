# 📄 Arquitetura de Leitura de PDFs, Boletos, Comprovantes e Extratos

## 🏗️ Visão Geral do Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ENTRADA DE DOCUMENTOS                           │
│            (PDF, Imagem, Comprovante, Extrato)                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼────────┐   ┌───────▼────────┐
            │   PDF FILES    │   │    IMAGENS     │
            │   (Boletos)    │   │  (Comprovantes)│
            │   (Extratos)   │   │     (PIX)      │
            └───────┬────────┘   └───────┬────────┘
                    │                     │
        ┌───────────┴─────────────────────┴───────────┐
        │                                             │
        │    MÓDULO DE PROCESSAMENTO CENTRAL          │
        │   (whatsapp_bot/index.js + api_server.py)  │
        │                                             │
        └───────────────────────┬─────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌──────▼────────┐            ┌────────▼────────┐
        │ FATURAS.PY    │            │COMPROVANTES.PY  │
        │               │            │                 │
        │ • Boletos     │            │ • PIX           │
        │ • Faturas     │            │ • Transferência │
        │ • Extratos    │            │ • Recibos       │
        │ • Guias       │            │ • Notas Fiscais │
        │ • Impostos    │            │                 │
        └──────┬────────┘            └────────┬────────┘
               │                              │
        ┌──────▼─────────────────────────────▼───────┐
        │   EXTRATOR_BRASIL.PY (Especializado)       │
        │   🇧🇷 Documentos Financeiros Brasileiros    │
        │                                             │
        │  • Validação CPF/CNPJ                      │
        │  • Decode Códigos de Barras                │
        │  • Parse Linha Digitável                   │
        │  • OCR com EasyOCR                         │
        │  • Extração PIX Automática                 │
        │                                             │
        └──────┬─────────────────────────────────────┘
               │
        ┌──────▼──────────────┐
        │  GEMINI VISION (IA) │
        │  (Backup inteligente)│
        │                     │
        │ • Análise de PDFs   │
        │ • Extração de dados │
        │ • Validação de tipos│
        └──────┬──────────────┘
               │
        ┌──────▼──────────────────────┐
        │   BANCO DE DADOS (JSON)      │
        │                              │
        │ • boletos.json               │
        │ • comprovantes.json          │
        │ • comprovantes_pendentes.json│
        │                              │
        └──────────────────────────────┘
```

---

## 📋 FLUXO 1: Processamento de PDFs (Boletos, Faturas, Extratos)

### Arquivo: `modules/faturas.py`

```
┌─────────────────────────────────────┐
│  Usuário envia PDF via WhatsApp     │
│  (/fatura, /boleto, /extrato)       │
└──────────────────┬──────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ processar_arquivo()  │
        │                      │
        │ Valida:              │
        │ • Arquivo existe?    │
        │ • Extensão .pdf?     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │   _processar_pdf()       │
        │                          │
        │ 1️⃣ GEMINI VISION (IA)    │
        │ ┌──────────────────┐     │
        │ │ _extrair_com     │     │
        │ │ _gemini()        │     │
        │ │                  │     │
        │ │ • Envia PDF      │     │
        │ │ • Recebe JSON    │     │
        │ │ • Parse resposta │     │
        │ └──────────────────┘     │
        │        ✅ SIM            │
        │         │                │
        │         ├─► Usa dados IA │
        │         │                │
        │      ❌ NÃO              │
        │         │                │
        └─────────┼────────────────┘
                  │
                  ▼
        ┌──────────────────────────┐
        │  2️⃣ MÉTODO TRADICIONAL   │
        │                          │
        │ Tenta em ordem:          │
        │ • pdfplumber (melhor)    │
        │ • PyPDF2 (fallback)      │
        │                          │
        │ Extrai: TEXTO do PDF     │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  _extrair_dados_boleto() │
        │                          │
        │ • Regex para valor       │
        │ • Regex para datas       │
        │ • Regex para linha digit │
        │ • Regex para código barr │
        │ • Detect tipo (DARF etc) │
        │                          │
        │ Retorna: Dict com dados  │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Cria Objeto Boleto()    │
        │                          │
        │ • id: UUID[:8]           │
        │ • valor: float           │
        │ • linha_digitavel: str   │
        │ • vencimento: DD/MM/YYYY │
        │ • beneficiario: str      │
        │ • pagador: str           │
        │ • tipo: boleto|darf|etc  │
        │ • cnpj_cpf: str          │
        │ • etc...                 │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Salva no JSON           │
        │  boletos.json            │
        │                          │
        │ ✅ Armazenado            │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Agenda Automaticamente   │
        │ (se data de vencimento)  │
        │                          │
        │ • Integra com agenda.py  │
        │ • Cria lembrete          │
        │ • Notifica usuário       │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Retorna para WhatsApp    │
        │                          │
        │ ✅ BOLETO PROCESSADO     │
        │ ID: xxx                  │
        │ Valor: R$ 150,00         │
        │ Vencimento: 15/12/2025   │
        │ ...                      │
        └──────────────────────────┘
```

### Métodos Principais

#### 1️⃣ `_extrair_com_gemini(arquivo: str)` → `Dict`

**Usa Gemini Vision (IA) para análise inteligente**

```python
# ENTRADA
arquivo = "/caminho/para/boleto.pdf"

# PROCESSO
1. Carrega API Key: GEMINI_API_KEY
2. Inicializa: genai.GenerativeModel('gemini-1.5-flash')
3. Tenta converter PDF → Imagem
   - if pdf2image: convert_from_path(pdf, dpi=150)
   - if falhar: Envia PDF diretamente (Gemini 1.5 suporta)
4. Monta PROMPT de extração
5. Envia para Gemini + Imagem/PDF
6. Recebe: JSON com dados

# RETORNO
{
    "tipo": "boleto",
    "valor": 150.00,
    "linha_digitavel": "xxxxx.xxxxx xxxxx.xxxxx xxxxx.xxxxx x xxxxx",
    "codigo_barras": "xxxxx...",
    "vencimento": "15/12/2025",
    "beneficiario": "Empresa XYZ",
    "pagador": "Meu Nome",
    "descricao": "Conta de água",
    "cnpj_cpf": "12.345.678/0001-90",
    "periodo_apuracao": null,
    "codigo_receita": null
}
```

**Prompt de Extração:**
```
Analise este documento (boleto, fatura, guia de imposto) e extraia as informações em formato JSON.

Retorne APENAS um JSON válido com:
- tipo: boleto|darf|gps|das|iptu|ipva|fgts|conta_luz|...
- valor: número decimal
- linha_digitavel: completa (47 dígitos)
- codigo_barras: 44 dígitos
- vencimento: DD/MM/YYYY
- beneficiario: nome do credor
- pagador: quem paga
- descricao: o que está sendo cobrado
- cnpj_cpf: do beneficiário
- periodo_apuracao: se for imposto
- codigo_receita: se for DARF/guia
```

#### 2️⃣ `_extrair_dados_boleto(texto: str)` → `Dict`

**Extração via Regex do texto do PDF**

```python
# ENTRADA
texto = "Código de Barras: 12345.67890 12345.678901 12345.678901 1 12345678901234"

# PROCESS - Busca padrões
- LINHA_DIGITAVEL: r"(\d{5}\.\d{5}\s\d{5}\.\d{5}\s\d{5}\.\d{5}\s\d+\s\d{14})"
- CODIGO_BARRAS: r"(\d{44})"
- VALOR: r"R\$\s*([\d.,]+)"
- VENCIMENTO: r"(\d{2}/\d{2}/\d{4})"
- BENEFICIARIO: r"Credor:?\s*([^\n]+)"
- PAGADOR: r"Pagador:?\s*([^\n]+)"

# RETORNO
{
    "valor": 150.00,
    "linha_digitavel": "12345.67890 12345.678901 12345.678901 1 12345678901234",
    "codigo_barras": "12345678901234567890123456789012345678901234",
    "vencimento": "15/12/2025",
    "beneficiario": "Empresa XYZ",
    "pagador": "Meu Nome",
    "tipo": "boleto",
    "etc": "..."
}
```

---

## 🧾 FLUXO 2: Processamento de Comprovantes (PIX, Transferências, Recibos)

### Arquivo: `modules/comprovantes.py`

```
┌─────────────────────────────────────┐
│  Usuário envia Imagem via WhatsApp  │
│  (PIX, Transferência, Recibo)       │
└──────────────────┬──────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ processar_imagem()       │
        │                          │
        │ Valida:                  │
        │ • Arquivo existe?        │
        │ • Extensão .jpg/.png?    │
        │ • Download da WhatsApp   │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ processar_imagem_brasil()    │
        │                              │
        │ Usa EXTRATOR_BRASIL:         │
        │ • Decodifica barras          │
        │ • Valida CPF/CNPJ            │
        │ • OCR (EasyOCR)              │
        │ • Detecção automática        │
        │                              │
        │ Retorna:                     │
        │ - tipo: 'pix'|'boleto'|'ted' │
        │ - dados: Dict                │
        └──────────┬───────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    BOLETO               PIX/TRANSFERÊNCIA
        │                     │
    ┌───▼────────┐       ┌────▼──────────┐
    │_converter  │       │_converter     │
    │_boleto()   │       │_pix()         │
    │            │       │               │
    │Adiciona:   │       │Adiciona:      │
    │• linha_dig │       │• chave_pix    │
    │• cod_barr  │       │• tipo_chave   │
    │• banco     │       │• id_transacao │
    │• cnpj      │       │• tipo_transac │
    │            │       │               │
    └────┬───────┘       └────┬──────────┘
         │                    │
         └──────────┬─────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │ ComprovanteExtraido()│
        │                      │
        │ id: hash MD5         │
        │ tipo: pix|ted|etc    │
        │ valor: float         │
        │ data: YYYY-MM-DD     │
        │ descricao: str       │
        │ destinatario: str    │
        │ status: 'pendente'   │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ _sugerir_categoria() │
        │                      │
        │ Palavras-chave:      │
        │ • alimentacao        │
        │ • combustivel        │
        │ • transporte         │
        │ • moradia            │
        │ • saude              │
        │ • lazer              │
        │ • educacao           │
        │ • vestuario          │
        │ • tecnologia         │
        │                      │
        │ Score: 0 a 1.0       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Salva PENDENTE       │
        │                      │
        │comprovantes_        │
        │ pendentes.json       │
        │                      │
        │ Status: 'pendente'   │
        │ Aguarda confirmação  │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Retorna para WhatsApp│
        │                      │
        │ ✅ COMPROVANTE ANALIS│
        │ ID: xxx              │
        │ Tipo: PIX            │
        │ Valor: R$ 50,00      │
        │ Para: João Silva     │
        │ Categoria: Alimentaçã│
        │ Confiança: 85%       │
        │                      │
        │ ✋ Confirma?         │
        │ /sim  /nao           │
        └──────────────────────┘
```

### Métodos Principais

#### 1️⃣ `processar_imagem_brasil(image_data: bytes)`

**Usa módulo extrator_brasil.py**

```python
# ENTRADA
image_data = bytes (imagem da câmera do WhatsApp)

# PROCESSO
resultado = self._extrator_brasil.extrair_automatico(
    image_data=image_data
)
# Retorna:
# {
#     "tipo": "pix",
#     "dados": {
#         "valor": 50.00,
#         "chave_pix": "12345678-1234-1234-1234-123456789012",
#         "destino_nome": "João Silva",
#         "id_transacao": "E12345678901234567890123456789012",
#         ...
#     }
# }

# CONVERSÃO AUTOMÁTICA
if tipo == 'boleto':
    return _converter_boleto(dados)
elif tipo == 'pix':
    return _converter_pix(dados)
elif tipo == 'transferencia':
    return _converter_transferencia(dados)
```

#### 2️⃣ `_sugerir_categoria(texto: str, destinatario: str)` → `(str, float)`

**Categorização automática inteligente**

```python
# CATEGORIA KEYWORDS EXEMPLO
CATEGORIAS_KEYWORDS = {
    'alimentacao': [
        'restaurante', 'lanchonete', 'mercado', 'supermercado',
        'ifood', 'uber eats', 'mcdonald', 'subway', ...
    ],
    'combustivel': [
        'posto', 'gasolina', 'shell', 'br', 'ipiranga', ...
    ],
    'transporte': [
        'uber', 'taxi', 'estacionamento', 'pedágio', ...
    ],
    'moradia': [
        'aluguel', 'condomínio', 'luz', 'água', ...
    ],
    'saude': [
        'farmácia', 'hospital', 'clínica', 'médico', ...
    ],
    # ... mais categorias
}

# SCORING
Para cada categoria:
    score = 0
    for keyword in categoria_keywords:
        if keyword in texto:
            score += 1
            if keyword in destinatario:  # Match exato = bonus
                score += 2

confianca = min(score / 5.0, 1.0)
# Resultado: (categoria, confianca: 0.0 a 1.0)
```

---

## 🇧🇷 FLUXO 3: Extrator Brasil (Especializado)

### Arquivo: `modules/extrator_brasil.py`

```
┌─────────────────────────────────────┐
│   ENTRADA: Imagem ou Texto          │
│   (Boleto, PIX, TED/DOC)            │
└──────────────────┬──────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ extrair_automatico()     │
        │                          │
        │ Detecta tipo do doc      │
        └──────────┬───────────────┘
                   │
        ┌──────────┴──────────────────────┐
        │                                 │
    BOLETO                            PIX
        │                                 │
        ▼                                 ▼
    ┌─────────────────┐          ┌─────────────────┐
    │extrair_boleto() │          │extrair_pix()    │
    │                 │          │                 │
    │ 1. Detecta barr │          │ 1. OCR (EasyOCR)│
    │    code         │          │                 │
    │                 │          │ 2. Regex PIX    │
    │ 2. Decodifica   │          │                 │
    │    linha_digit  │          │ 3. Valida CPF   │
    │                 │          │                 │
    │ 3. Extrai dados │          │ 4. Parse banco  │
    │    via regex    │          │                 │
    │                 │          │ 5. Retorna struct
    │ 4. Calcula      │          └─────────────────┘
    │    vencimento   │
    │    (fator)      │
    │                 │
    │ 5. Valida CNPJ  │
    │    (opcional)   │
    │                 │
    │ 6. Retorna      │
    │    DadosBoleto()│
    └─────────────────┘
```

### Classes de Dados

```python
@dataclass
class DadosBoleto:
    linha_digitavel: str      # "xxxxx.xxxxx xxxxx.xxxxx xxxxx.xxxxx x xxxxx"
    codigo_barras: str        # 44 dígitos
    valor: float              # 150.50
    vencimento: str           # "15/12/2025"
    beneficiario: str         # "Empresa XYZ"
    beneficiario_cnpj: str    # "12.345.678/0001-90"
    pagador: str              # "Meu Nome"
    pagador_cpf_cnpj: str     # "123.456.789-10"
    banco: str                # "Bradesco"
    codigo_banco: str         # "237"
    nosso_numero: str         # "1234567890123"
    confianca: float          # 0.95 (95%)

@dataclass
class DadosComprovantePix:
    tipo_transacao: str       # "enviado" ou "recebido"
    valor: float              # 50.00
    data_hora: str            # "2025-12-01T15:30:00"
    destino_nome: str         # "João Silva"
    destino_documento: str    # "123.456.789-10"
    chave_pix: str            # "12345678-1234-1234-1234-123456789012"
    tipo_chave: str           # "cpf", "cnpj", "email", "telefone", "aleatoria"
    id_transacao: str         # "E12345678901234567890123456789012"
    confianca: float          # 0.98 (98%)

@dataclass
class DadosComprovanteTransferencia:
    tipo: str                 # "TED" ou "DOC"
    valor: float              # 1000.00
    data_hora: str            # "2025-12-01T15:30:00"
    origem_nome: str          # "Minha Conta"
    origem_banco: str         # "Bradesco"
    destino_nome: str         # "Empresa XYZ"
    destino_banco: str        # "Santander"
    id_transacao: str         # "1234567890"
    confianca: float          # 0.95
```

---

## 🤖 FLUXO 4: Gemini Vision (Fallback Inteligente)

```
┌──────────────────────────────────────┐
│  Quando métodos tradicionais falham: │
│                                      │
│  • PDF é imagem (escaneado)         │
│  • Texto não é extraível             │
│  • Formato não reconhecido            │
│  • Precisão baixa com regex           │
└──────────────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ _extrair_com_gemini()    │
        │                          │
        │ 1. Carrega API Key       │
        │ 2. Inicializa modelo     │
        │    gemini-1.5-flash      │
        │ 3. Converte PDF→Imagem   │
        │    (se possível)         │
        │ 4. Monta prompt          │
        │ 5. Envia para Gemini     │
        │ 6. Parse resposta JSON   │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Gemini retorna JSON      │
        │                          │
        │ Com alta precisão:       │
        │ • Valores monetários     │
        │ • Datas de vencimento    │
        │ • Linhas digitáveis      │
        │ • Tipos de documentos    │
        │ • Beneficiários/Pagadores│
        │                          │
        │ Com markup explicativo   │
        │ (depois removido)        │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ _parse_resposta_gemini() │
        │                          │
        │ 1. Remove markdown (```) │
        │ 2. Faz parse JSON        │
        │ 3. Normaliza valores     │
        │ 4. Converte datas        │
        │ 5. Valida tipos          │
        │                          │
        │ Retorna: Dict pronto     │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ ✅ Usa dados do Gemini   │
        │                          │
        │ Maior precisão! 🎯       │
        └──────────────────────────┘
```

### Prompt do Gemini

```python
"""
Analise este documento (boleto, fatura, guia de imposto) 
e extraia as informações em formato JSON.

Retorne APENAS um JSON válido (sem markdown, sem ```json) 
com os seguintes campos:

{
    "tipo": "boleto" ou "darf" ou "gps" ou "das" ou "iptu" 
            ou "ipva" ou "fgts" ou "conta_luz" ou "outro",
    
    "valor": número decimal (apenas o número, ex: 150.00),
    
    "linha_digitavel": "linha digitável completa com todos 
                        os números (47 dígitos)",
    
    "codigo_barras": "código de barras se visível (44 dígitos)",
    
    "vencimento": "data de vencimento no formato DD/MM/YYYY",
    
    "beneficiario": "nome do credor/empresa que vai receber 
                     o pagamento",
    
    "pagador": "nome de quem deve pagar",
    
    "descricao": "descrição do que está sendo cobrado",
    
    "cnpj_cpf": "CNPJ ou CPF do beneficiário se visível",
    
    "periodo_apuracao": "período de referência/competência 
                         se for imposto",
    
    "codigo_receita": "código da receita se for DARF 
                       ou guia de imposto"
}

IMPORTANTE:
- Extraia a linha digitável COMPLETA (todos os números, 
  sem espaços)
- O valor deve ser apenas números com ponto decimal (1234.56)
- Se algum campo não estiver visível, use null
- Retorne APENAS o JSON, sem explicações
"""
```

---

## 💾 Armazenamento de Dados

### 1️⃣ **boletos.json**
```json
[
  {
    "id": "a3f5b2c1",
    "valor": 150.00,
    "codigo_barras": "xxxxx...",
    "linha_digitavel": "xxxxx.xxxxx xxxxx.xxxxx xxxxx.xxxxx x xxxxx",
    "vencimento": "15/12/2025",
    "beneficiario": "Empresa XYZ",
    "pagador": "Meu Nome",
    "descricao": "Conta de água",
    "arquivo_origem": "boleto_agua.pdf",
    "user_id": "558197723921@s.whatsapp.net",
    "extraido_em": "2025-12-01T10:30:45.123456",
    "pago": false,
    "agendado": true,
    "tipo": "boleto",
    "cnpj_cpf": "12.345.678/0001-90",
    "periodo_apuracao": null,
    "codigo_receita": null
  }
]
```

### 2️⃣ **comprovantes.json**
```json
[
  {
    "id": "xyz123abc",
    "tipo": "pix",
    "valor": 50.00,
    "descricao": "Pagamento para João Silva",
    "data": "2025-12-01",
    "destinatario": "João Silva",
    "categoria_sugerida": "alimentacao",
    "confianca": 0.95,
    "user_id": "558197723921@s.whatsapp.net",
    "status": "confirmado",
    "criado_em": "2025-12-01T15:30:45.123456",
    "pix_dados": {
      "chave_pix": "12345678-1234-1234-1234-123456789012",
      "id_transacao": "E12345678901234567890123456789012",
      "banco": "Itaú",
      "tipo_transacao": "enviado"
    }
  }
]
```

### 3️⃣ **comprovantes_pendentes.json**
```json
{
  "558197723921@s.whatsapp.net": {
    "id": "xyz123abc",
    "tipo": "pix",
    "valor": 50.00,
    "descricao": "Pagamento para Restaurante ABC",
    "categoria_sugerida": "alimentacao",
    "confianca": 0.85,
    "status": "pendente",
    "criado_em": "2025-12-01T20:00:00.123456"
  }
}
```

---

## 📦 Dependências Utilizadas

### **Para Leitura de PDFs**
```
pdfplumber>=0.9.0         # Extração de texto de PDFs (MELHOR)
PyPDF2>=3.0.0             # Fallback para PyPDF2
pdf2image>=1.16.0         # Converte PDF para imagem
```

### **Para OCR (Texto em Imagem)**
```
easyocr>=1.7.0            # OCR multilingue (português)
pytesseract>=0.3.10       # OCR alternativo
python-magic              # Detecção de tipo de arquivo
Pillow>=9.0.0             # Processamento de imagens
```

### **Para Validação Brasileira**
```
validate-docbr>=1.10.0    # Validação CPF/CNPJ
brazilcep>=2.0.0          # Consulta CEP
python-barcode>=1.13.0    # Geração de códigos de barras
pyzbar>=0.1.9             # Leitura de códigos de barras
```

### **Para IA**
```
google-generativeai>=0.3.0 # Gemini Vision API
```

### **Outras**
```
ofxparse>=0.21            # Parser OFX (extratos bancários)
```

---

## 🔄 Fluxo Completo de um Boleto via WhatsApp

```
1️⃣ USUÁRIO envia PDF
   "Aqui está meu boleto de água"
   📎 boleto_agua.pdf

2️⃣ BOT recebe arquivo
   • Valida extensão .pdf
   • Faz download do WhatsApp
   • Salva temporário em /temp/

3️⃣ PROCESSAMENTO
   • Tenta Gemini Vision (IA) ✓ SE DISPONÍVEL
   • Fallback: pdfplumber ✓
   • Fallback: PyPDF2 ✓
   • Extrai: TEXTO

4️⃣ EXTRAÇÃO DE DADOS
   • Regex para linha digitável
   • Regex para código de barras
   • Regex para valor (R$)
   • Regex para data de vencimento
   • Regex para beneficiário

5️⃣ DETECÇÃO AUTOMÁTICA
   • É boleto? → "boleto"
   • É DARF? → "darf"
   • É conta de luz? → tipo "conta_luz"
   • É IPTU? → tipo "iptu"

6️⃣ CRIAÇÃO DE OBJETO
   boleto = Boleto(
       id="a3f5b2c1",
       valor=150.00,
       linha_digitavel="...",
       vencimento="15/12/2025",
       beneficiario="Compesa",
       pagador="João Silva",
       ...
   )

7️⃣ ARMAZENAMENTO
   • Salva em: data/boletos.json
   • ID gerado: UUID[:8]
   • User ID: 558197723921@s.whatsapp.net

8️⃣ AGENDAMENTO AUTOMÁTICO
   • Se tem vencimento
   • Integra com agenda.py
   • Cria lembrete 3 dias antes
   • Notifica usuário

9️⃣ RESPOSTA AO USUÁRIO
   "✅ Boleto Processado com Sucesso!
    
    ID: a3f5b2c1
    Descrição: Conta de água
    Valor: R$ 150,00
    Vencimento: 15/12/2025
    
    Credor: Compesa
    Linha Digitável: xxxxx.xxxxx ...
    
    ✅ Agendado automaticamente!
    Você receberá um lembrete antes do vencimento.
    
    Comandos:
    /boletos - Ver todos os boletos
    /pago a3f5b2c1 - Marcar como pago"

🔟 USUÁRIO CONFIRMA
   "/pago a3f5b2c1"
   
   ✅ Boleto marcado como PAGO
   • Status atualizado no JSON
   • Lembrete cancelado (se existisse)
   • Registrado em finanças
```

---

## 🎯 Métodos de Extração (Por Prioridade)

### ✅ Método Preferencial: **Gemini Vision (IA)**
- **Pros:** Altíssima precisão, detecta contexto, suporta PDFs escaneados
- **Cons:** Requer API Key, chamadas à IA (limitadas), latência
- **Uso:** Quando PDF é imagem ou texto não é extraível

### ✅ Método Alternativo 1: **pdfplumber**
- **Pros:** Rápido, preciso, gratuito, texto limpo
- **Cons:** Apenas PDF com texto embutido, não funciona com escaneados
- **Uso:** PDFs digitais padrão

### ✅ Método Alternativo 2: **PyPDF2**
- **Pros:** Fallback confiável, gratuito
- **Cons:** Texto às vezes desorganizado, latência
- **Uso:** Quando pdfplumber falha

### ✅ Método Alternativo 3: **EasyOCR (em breve)**
- **Pros:** Funciona com PDFs escaneados, alta precisão português
- **Cons:** Lento, processamento em CPU, requer modelo baixado
- **Uso:** Quando PDF é puramente imagem

### ✅ Método Alternativo 4: **Extrator Brasil**
- **Pros:** Especializado em documentos brasileiros, reconhece padrões
- **Cons:** Requer dependências nativas (pyzbar)
- **Uso:** Detecção de boletos, PIX, TED automática

---

## 📊 Matriz de Suporte

| Tipo Documento | PDF Texto | PDF Imagem | Imagem | Gemini | Extrator | Regex |
|---|---|---|---|---|---|---|
| **Boleto** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **DARF/Imposto** | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ |
| **Conta Luz/Água** | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ |
| **PIX** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **TED/DOC** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Nota Fiscal** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Extrato Bancário** | ✅ | ❌ | ❌ | ✅ | ⚠️ | ✅ |
| **Recibo Genérico** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |

---

## 🚀 Próximas Implementações

1. **OCR Automático com EasyOCR**
   - Para PDFs completamente escaneados
   - Detecção português nativa

2. **Integração com Extrato Bancário (OFX)**
   - Parser para arquivos `.ofx`
   - Categorização automática de transações

3. **Machine Learning para Categorização**
   - Treinar modelo com histórico do usuário
   - Melhorar precisão de categorias

4. **Processamento em Batch**
   - Enviar vários boletos/comprovantes de uma vez
   - Processamento paralelo

5. **Webhook para Confirmação Automática**
   - Confirmar comprovantes automaticamente
   - Baseado em regras do usuário

---

## 📝 Resumo Técnico

**Arquitetura:** Modular, com fallbacks em cascata
**Entrada:** PDF, Imagem, Texto
**Processamento:** Regex → IA (Gemini) → Extrator Especializado
**Saída:** JSON estruturado, pronto para banco de dados
**Armazenamento:** JSON local + MongoDB (futuro)
**Integração:** WhatsApp Bot ↔️ API Flask ↔️ Módulos Python

