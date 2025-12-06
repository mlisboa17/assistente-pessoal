# 🤖 Assistente Pessoal Inteligente

Sistema completo de assistente pessoal com integração WhatsApp, Telegram, e-mails, finanças e muito mais.

## 📐 Arquitetura

```
[Usuário]
   ↑ Voz / Texto / Arquivos
   ↓
[Interface]
   ├── WhatsApp Bot
   └── Telegram Bot
        ↓
[Middleware Inteligente]
   ├── Command Parser (interpreta comandos)
   ├── NLP Engine (IA básica: spaCy, Transformers, GPT APIs)
   └── Orchestrator (decide qual módulo acionar)
        ↓
[Funções / Módulos]
   ├── Agenda (compromissos, lembretes)
   ├── E-mails (Gmail, Outlook, UOL)
   ├── Finanças (gastos, relatórios, alertas)
   ├── Faturas/Extratos (PDF, CSV, TXT)
   ├── Vendas/LOGOS (relatórios, estoque)
   ├── Voz (speech-to-text, voice commands)
   ├── Tarefas rápidas (criar, compartilhar)
   └── Alertas inteligentes (gatilhos automáticos)
        ↓
[Banco de Dados / Armazenamento]
   ├── SQLite / MongoDB / PostgreSQL
   └── Google Drive / OneDrive (anexos, relatórios)
        ↓
[Dashboards / Relatórios Visuais]
   ├── Gráficos (matplotlib, seaborn, plotly)
   └── Relatórios visuais (chart.js, d3.js)
        ↓
[Usuário]
   ↑ Respostas no chat (texto, gráficos, alertas)
```

## 🚀 Início Rápido

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env
# Edite o arquivo .env com suas chaves

# Iniciar o assistente
python main.py
```

## 📁 Estrutura do Projeto

```
assistente_pessoal/
├── main.py                    # Ponto de entrada
├── config/
│   └── settings.py            # Configurações
├── interfaces/
│   ├── telegram_bot.py        # Bot Telegram
│   └── whatsapp_bot.py        # Bot WhatsApp
├── middleware/
│   ├── command_parser.py      # Parser de comandos
│   ├── nlp_engine.py          # Motor NLP
│   └── orchestrator.py        # Orquestrador
├── modules/
│   ├── agenda.py              # Agenda/Lembretes
│   ├── emails.py              # E-mails
│   ├── financas.py            # Finanças
│   ├── faturas.py             # Faturas/Extratos
│   ├── vendas.py              # Vendas/LOGOS
│   ├── voz.py                 # Comandos de voz
│   ├── tarefas.py             # Tarefas rápidas
│   └── alertas.py             # Alertas inteligentes
├── database/
│   └── db_manager.py          # Gerenciador de BD
├── storage/
│   └── cloud_storage.py       # Google Drive/OneDrive
└── dashboard/
    └── visualizer.py          # Gráficos e relatórios
```

## 🔧 Configuração

### Telegram Bot
1. Fale com @BotFather no Telegram
2. Crie um novo bot com `/newbot`
3. Copie o token para o `.env`

### WhatsApp Bot (via Twilio)
1. Crie conta em twilio.com
2. Configure WhatsApp Sandbox
3. Copie as credenciais para o `.env`

### APIs de E-mail
- Gmail: Ative API no Google Cloud Console
- Outlook: Registre app no Azure AD

## 📝 Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `/agenda` | Ver compromissos do dia |
| `/lembrete [texto] [hora]` | Criar lembrete |
| `/emails` | Ver últimos e-mails |
| `/gastos` | Resumo de gastos |
| `/fatura [anexo]` | Processar fatura |
| `/vendas` | Relatório de vendas |
| `/tarefa [texto]` | Criar tarefa rápida |

## 📄 Licença

MIT License
