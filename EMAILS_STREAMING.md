# 📧 Sistema de Leitura de E-mails com Progresso em Tempo Real

## 🎯 Objetivo

Implementar sistema interativo para ler e-mails que:
- ✅ **Mostra progresso** - "Lendo email 1/10..."
- ✅ **Gera resumos automáticos** - Resumo inteligente de cada e-mail
- ✅ **Permite interação** - Usuário pode enviar comandos durante leitura
- ✅ **Não deixa ansioso** - Feedback constante do progresso

---

## 🏗️ Arquitetura

### **Fluxo Principal**

```
Usuário: /emails
   │
   ├─→ middleware/orchestrator.py
   │   └─→ modules/emails.py
   │       ├─→ _listar_emails_stream() [NEW]
   │       ├─→ _processar_emails_progressivo() [NEW]
   │       ├─→ _buscar_emails_gmail() [NEW]
   │       ├─→ _montar_resposta_emails() [NEW]
   │       └─→ Google OAuth (google_auth)
   │
   └─→ WhatsApp (resposta com progresso)

```

### **Componentes Principais**

```python
# 1. RASTREADOR DE PROGRESSO
progresso_leitura[user_id] = {
    'total': 10,              # Total de e-mails
    'processados': 3,         # Já processados
    'parado': False,          # Usuário pediu parar?
    'emails': [...],          # Lista de e-mails
    'inicio': datetime.now()  # Timestamp início
}

# 2. CATEGORIZAÇÃO AUTOMÁTICA
EMAIL.categoria = detectar_categoria(email)
# Retorna: trabalho, pessoal, importante, notificacao, promotional, spam, outros

# 3. RESUMO AUTOMÁTICO
EMAIL.resumo = gerar_resumo(email.corpo)
# Resumo curto (80 chars) do conteúdo

# 4. INDICADOR VISUAL
[████████░░] 80%  # Barra de progresso
Lendo email 8/10...  # Contador

# 5. INTERFACE INTERATIVA
/mais - Ver mais e-mails
/importante - Filtrar apenas importantes
/trabalho - Filtrar por categoria
/parar - Interromper leitura
```

---

## 📱 Interface do Usuário

### **Resposta Exemplo: /emails**

```
📧 *Leitura de E-mails* [████████░░] 80%

🔄 Total: 10 e-mail(is) para ler

🔴 *IMPORTANTE* (1)
1. 📬 ⚠️ Alerta de Segurança: Acesso Não Autorizado
   De: banco@bancoxx.com.br
   📝 Alerta de segurança - verificar imediatamente...

💼 *TRABALHO* (2)
1. 📬 Reunião urgente hoje às 14:00 - Projeto X
   De: chefe@empresa.com
   📝 Reunião urgente sobre projeto X hoje às 14h...

2. 📬 Feedback sobre proposta de Q4
   De: gerente@empresa.com
   📝 Sua proposta foi revisada e aprovada...

👤 *PESSOAL* (1)
1. 📬 Ô, bora tomar um café no fim de semana?
   De: amigo@hotmail.com
   📝 Convite para café no sábado...

🔔 *NOTIFICACAO* (1)
1. 📬 📦 Seu pedido foi entregue!
   De: noreply@amazon.com.br
   📝 Pedido Amazon entregue...

🛍️ *PROMOTIONAL* (1)
1. 📬 🎉 MEGA DESCONTO: Até 70% em eletrônicos!
   De: noreply@shopee.com.br
   📝 Promoção eletrônicos 70% desconto...

─────────────────────────────────
🎯 *Opções:*
/mais - Ver mais e-mails
/importante - Filtrar importantes
/trabalho - Filtrar trabalho
/pessoal - Filtrar pessoal
/parar - Parar a leitura

📊 *Resumo por categoria:*
• importante: 1
• trabalho: 2
• pessoal: 1
• notificacao: 1
• promotional: 1
• outros: 3

─────────────────────────────────
⏱️ Tempo: 2m 15s
✅ Pronto para interagir!
```

---

## 🔄 Fluxo de Processamento

### **1. Usuário solicita /emails**

```
Resposta imediata:
├─ Barra de progresso visual
├─ Total de e-mails descobertos
├─ Início processamento assíncrono
└─ Botões de interação
```

### **2. Processamento em Tempo Real**

```
Para cada e-mail:
├─ Lê conteúdo
├─ Detecta categoria (keyword matching)
├─ Gera resumo (trunca em 80 chars)
├─ Atualiza contador de progresso
└─ Permite interrupção (/parar)

Paralelo:
└─ Agrega resultados por categoria
```

### **3. Apresentação Agrupada**

```
Por categoria (ordem de importância):
1. 🔴 IMPORTANTE (prioridade máxima)
2. 💼 TRABALHO
3. 👤 PESSOAL
4. 🔔 NOTIFICACAO
5. 🛍️ PROMOTIONAL
6. 🚫 SPAM
7. 📬 OUTROS

Cada categoria mostra:
- Ícone + nome + quantidade
- Primeiros 3 e-mails
- Remetente
- Resumo automático (80 chars)
```

---

## 🎯 Funcionalidades Implementadas

### ✅ Indicadores de Progresso

```python
def _gerar_barra_progresso(processados: int, total: int) -> str:
    """Gera barra visual"""
    # [████████░░] 80%
    
    percentual = (processados / total) * 100
    blocos = int(percentual / 10)
    barra = "█" * blocos + "░" * (10 - blocos)
    return f"[{barra}] {int(percentual)}%"
```

**Exemplo:**
```
[░░░░░░░░░░] 0%    - Início
[██░░░░░░░░] 20%   - 2/10 processados
[████░░░░░░] 40%   - 4/10 processados
[██████░░░░] 60%   - 6/10 processados
[████████░░] 80%   - 8/10 processados
[██████████] 100%  - Pronto!
```

### ✅ Categorização Automática

```python
KEYWORDS_CATEGORIA = {
    'trabalho': ['reunião', 'trabalho', 'projeto', 'deadline', ...],
    'importante': ['urgente', 'importante', 'atenção', 'crítico', ...],
    'pessoal': ['amigo', 'família', 'pessoal', 'convite', ...],
    'notificacao': ['confirmação', 'recebimento', 'aviso', ...],
    'promotional': ['desconto', 'oferta', 'promoção', ...],
}

# Scoring:
score = 0
for keyword in categoria_keywords:
    if keyword in email_texto:
        score += 1

melhor_categoria = max_score_category
confianca = score / total_keywords
```

**Exemplos:**
```
Email: "Reunião urgente HOJE"
├─ trabalho: "reunião" +1 = 1 ponto ✓
├─ importante: "urgente" +1 = 1 ponto ✓
└─ Vencedor: IMPORTANTE (urgente > reunião)

Email: "Seu pedido foi entregue!"
├─ notificacao: "recebimento" +1 = 1 ponto ✓
└─ Resultado: NOTIFICACAO

Email: "Desconto de 70%!"
├─ promotional: "desconto" +1 = 1 ponto ✓
└─ Resultado: PROMOTIONAL
```

### ✅ Geração de Resumos

```python
# Trunca o corpo do e-mail em 80 caracteres
resumo = corpo[:80] + "..."

# Exemplos:
"Reunião urgente sobre projeto X hoje às 14h" (45 chars)
"Pedido Amazon entregue" (22 chars)
"Promoção eletrônicos 70% desconto" (34 chars)
"Alerta de segurança - verificar imediatamente" (47 chars)
```

### ✅ Interface Interativa

**Comandos disponíveis durante/após leitura:**

| Comando | Função | Resposta |
|---------|--------|----------|
| `/mais` | Ver mais e-mails | Próximas 5 | 
| `/importante` | Filtrar importantes | Apenas IMPORTANTE |
| `/trabalho` | Filtrar trabalho | Apenas TRABALHO |
| `/pessoal` | Filtrar pessoal | Apenas PESSOAL |
| `/parar` | Parar leitura | ⏸️ Leitura pausada |
| `/de:email@...` | De um remetente | Filtra por remetente |
| `/assunto:...` | Por palavra-chave | Busca no assunto |

**Exemplo interativo:**

```
Usuário: /emails
Bot: [carregando com barra 80%]
     Total: 10 e-mails
     (lista agrupada por categoria)

Usuário: /importante
Bot: 🔴 *IMPORTANTE* (1)
     1. ⚠️ Alerta de Segurança...

Usuário: /trabalho
Bot: 💼 *TRABALHO* (2)
     1. Reunião urgente...
     2. Feedback sobre...

Usuário: /parar
Bot: ⏸️ Leitura Parada
     Você pode continuar com:
     /mais, /importante, /trabalho, etc
```

---

## 🔌 Integração com Google OAuth

### **Inicialização**

```python
# middleware/orchestrator.py

# 1. Carrega módulos
self.modules['agenda'] = AgendaModule()
self.modules['emails'] = EmailModule()

# 2. Conecta google_auth
if 'agenda' in self.modules:
    google_auth = self.modules['agenda'].google_auth
    self.modules['emails'].set_google_auth(google_auth)
```

### **Uso em Produção (Gmail API)**

```python
# modules/emails.py

async def _buscar_emails_gmail(self, user_id: str) -> List[Email]:
    """Busca e-mails reais do Gmail"""
    
    # Obter credenciais do usuário
    credentials = self.google_auth.get_credentials(user_id)
    
    # Criar serviço Gmail
    service = self.google_auth.get_gmail_service(credentials)
    
    # Buscar últimos 10 e-mails
    results = service.users().messages().list(
        userId='me',
        maxResults=10,
        q='is:unread'  # Apenas não lidos
    ).execute()
    
    # Processar cada e-mail
    emails = []
    for msg in results.get('messages', []):
        email = self._processar_mensagem_gmail(msg)
        emails.append(email)
        # Simula delay de processamento
        await asyncio.sleep(0.5)
    
    return emails
```

---

## 💾 Estrutura de Dados

### **Email (com novos campos)**

```python
@dataclass
class Email:
    id: str                    # ID único do e-mail
    de: str                   # Remetente
    para: str                 # Destinatário
    assunto: str              # Assunto
    corpo: str                # Conteúdo
    data: str                 # Data/hora
    lido: bool = False        # Já foi lido?
    anexos: List[str] = None  # Arquivos anexados
    
    # 🆕 NOVOS CAMPOS
    resumo: str = ""          # Resumo automático (80 chars)
    categoria: str = ""       # Tipo: trabalho, pessoal, etc
```

### **Progresso de Leitura**

```python
progresso_leitura[user_id] = {
    'total': 10,              # Total de e-mails para ler
    'processados': 3,         # Já lidos
    'parado': False,          # Parou por request do user?
    'emails': [...],          # Lista de Email objects
    'inicio': datetime.now()  # Quando começou
}

# Acesso:
progresso = self.progresso_leitura[user_id]
percentual = (progresso['processados'] / progresso['total']) * 100
tempo = (datetime.now() - progresso['inicio']).total_seconds()
```

---

## 📊 Exemplos de Fluxo Completo

### **Cenário 1: Verificar e-mails rápido**

```
USER: /emails

BOT:
📧 *Leitura de E-mails* [██████░░░░] 60%
🔄 Total: 10 e-mail(is) para ler

🔴 *IMPORTANTE* (1)
1. ⚠️ Alerta de Segurança
   De: banco@bancoxx.com.br
   📝 Alerta de segurança...

💼 *TRABALHO* (2)
1. Reunião urgente hoje às 14:00
   De: chefe@empresa.com
   📝 Reunião urgente sobre projeto...

/importante - Ver apenas importantes
/trabalho - Ver apenas trabalho
⏱️ Tempo: 45s

---

USER: /importante

BOT:
🔴 *IMPORTANTE* (1)
1. ⚠️ Alerta de Segurança: Acesso Não Autorizado
   De: banco@bancoxx.com.br
   📝 Alerta de segurança - verificar imediatamente

💡 Ação recomendada: Verificar sua conta bancária!
```

### **Cenário 2: Interrupção e retomada**

```
USER: /emails

BOT: [carregando... 30%]

USER: /parar

BOT: ⏸️ *Leitura Parada*
     A leitura foi interrompida.
     
     Você pode:
     /mais - Continuar lendo
     /importante - Filtrar importantes
     /emails - Recomeçar do zero

---

USER: /mais

BOT: [retomando... 60%]
     (continua de onde parou)
```

### **Cenário 3: Filtro por categoria**

```
USER: /emails

BOT: [lista completa com progresso]

USER: /trabalho

BOT: 💼 *TRABALHO* (3)
     1. Reunião urgente hoje às 14:00
     2. Feedback sobre proposta Q4
     3. Newsletter semanal

USER: /pessoal

BOT: 👤 *PESSOAL* (1)
     1. Ô, bora tomar um café?
```

---

## 🚀 Próximas Melhorias

```
🔄 [EM PROGRESSO]
├─ Integração real com Gmail API
├─ Suporte a múltiplas contas
└─ Sincronização local de cache

📋 [FUTURO]
├─ Responder e-mails via WhatsApp
├─ Marcar como lido/arquivar
├─ Delegação de e-mails
├─ Templates de resposta
├─ Agendamento de respostas
├─ Integração com Outlook
├─ Busca avançada
├─ Labels/Tags customizadas
├─ Priorização inteligente
└─ Análise de sentimento
```

---

## 📝 Resumo Técnico

| Aspecto | Detalhe |
|---------|---------|
| **Método Principal** | `_listar_emails_stream()` |
| **Processamento** | Assíncrono (async/await) |
| **Progresso** | Barra visual + contador |
| **Categorização** | Keyword matching + scoring |
| **Resumo** | Truncamento inteligente |
| **Interatividade** | Comandos durante leitura |
| **Cache** | `progresso_leitura[user_id]` |
| **Integração** | Google OAuth (Gmail API) |
| **Responsividade** | Não bloqueia (streaming) |

---

## 🎓 Como Usar

### **Básico**

```
/emails              - Listar todos os e-mails
/mais                - Ver mais e-mails
/importante          - Filtrar importantes
/trabalho            - Filtrar trabalho
/parar               - Parar leitura
```

### **Avançado**

```
/email busca         - Buscar por termo
/de:email@...        - De um remetente
/assunto:palavras    - No assunto
/categoria:trabalho  - Por categoria
```

### **Gerenciamento**

```
/ler ID              - Ler e-mail específico
/responder ID        - Responder a um e-mail
/arquivar ID         - Arquivar e-mail
/marcar_spam ID      - Marcar como spam
```

