# 🤖 Assistente Pessoal - Sistema de Gestão Financeira

Um sistema completo para processamento automático de extratos bancários, gestão financeira pessoal e empresarial, desenvolvido em Python com interface web moderna.

## 🌟 Funcionalidades Principais

### 📄 Processamento de Extratos
- **Extração automática** de dados de PDFs bancários
- **Suporte a múltiplos bancos**: Itaú, Banco do Brasil, Santander, C6, Nubank, Inter, Bradesco
- **Identificação inteligente** de CNPJ, empresa, agência e conta
- **Categorização automática** de transações

### 👥 Gestão de Cadastros
- **Usuários PF**: Cadastro completo com CPF, dados pessoais
- **Empresas PJ**: Gestão de CNPJ, razão social, responsáveis
- **Contas bancárias**: Vinculação a usuários/empresas
- **Cartões de crédito**: Controle de limites, vencimentos, bandeiras
- **Contatos**: Clientes, fornecedores e outros relacionamentos

### 📊 Dashboard e Relatórios
- **Visualização de transações** por período, categoria, conta
- **Estatísticas financeiras** com gráficos interativos
- **Revisão de categorias** com IA para sugestões automáticas
- **Exportação de dados** em múltiplos formatos

### 🔧 Tecnologias Utilizadas

#### Backend
- **Python 3.8+** - Linguagem principal
- **Flask** - Framework web
- **SQLite** - Banco de dados relacional
- **PyMuPDF** - Processamento de PDFs
- **Tabula-py** - Extração de tabelas
- **OpenAI API** - Categorização inteligente

#### Frontend
- **Bootstrap 5** - Framework CSS responsivo
- **JavaScript ES6+** - Interatividade
- **Font Awesome** - Ícones
- **Chart.js** - Gráficos (futuro)

#### Infraestrutura
- **Docker** - Containerização (planejado)
- **GitHub Actions** - CI/CD (planejado)
- **SQLite** - Persistência de dados

## 🚀 Instalação e Uso

### Pré-requisitos
```bash
Python 3.8 ou superior
Pip (gerenciador de pacotes Python)
```

### Instalação Rápida (Recomendado)

#### Windows
```cmd
# Execute o script de setup automático
setup.bat
```

#### Linux/Mac
```bash
# Execute o script de setup automático
chmod +x setup.sh
./setup.sh
```

### Instalação Manual
```bash
# Clone o repositório
git clone https://github.com/mlisboa17/assistente-pessoal.git
cd assistente-pessoal

# Instale as dependências
pip install -r requirements.txt

# Instale bibliotecas de processamento de PDF (essenciais para extração)
pip install PyMuPDF "camelot-py[cv]" tabula-py ofxparse
```

### Executar o Sistema
```bash
# Iniciar o servidor web
python api_server.py

# Acesse no navegador
# http://localhost:5001
```

### Primeiro Uso
1. **Acesse** http://localhost:5001/cadastros
2. **Cadastre usuários** e empresas
3. **Configure contas bancárias**
4. **Faça upload** dos extratos em PDF
5. **Revise categorias** das transações

## 🔧 Bibliotecas Essenciais

O sistema utiliza bibliotecas especializadas para processamento de PDFs bancários:

- **PyMuPDF (Fitz)**: Processamento avançado de texto em PDFs
- **Camelot**: Extração inteligente de tabelas estruturadas
- **Tabula-py**: Extração de tabelas via Java (Tabula)
- **Ofxparse**: Processamento de arquivos OFX bancários

> **Importante**: Essas bibliotecas são **essenciais** para a funcionalidade completa do sistema. O script de setup as instala automaticamente.

## 📁 Estrutura do Projeto

```
assistente-pessoal/
├── api_server.py              # Servidor Flask principal
├── database_setup.py           # Configuração do banco de dados
├── requirements.txt            # Dependências Python
├── README.md                   # Esta documentação
├── config/
│   ├── __init__.py
│   └── settings.py            # Configurações do sistema
├── data/
│   ├── financeiro.db          # Banco SQLite
│   ├── extratos.json          # Cache de extratos
│   └── transacoes.json        # Transações processadas
├── interfaces/
│   ├── __init__.py
│   └── telegram_bot.py        # Bot Telegram (futuro)
├── middleware/
│   ├── __init__.py
│   ├── command_parser.py      # Parser de comandos
│   ├── ia_interpreter.py      # IA para interpretação
│   ├── nlp_engine.py          # Processamento de linguagem
│   └── orchestrator.py        # Orquestrador principal
├── modules/
│   ├── __init__.py
│   ├── agenda.py              # Gestão de agenda
│   ├── condominio.py          # Gestão condominial
│   ├── emails.py              # Integração com email
│   ├── extratos.py            # Processamento de extratos
│   ├── faturas.py             # Gestão de faturas
│   ├── financas.py            # Módulo financeiro
│   └── tarefas.py             # Gestão de tarefas
├── static/
│   ├── style.css              # Estilos CSS
│   └── js/                    # Scripts JavaScript
├── templates/
│   ├── base.html              # Template base
│   ├── index.html             # Dashboard principal
│   ├── upload.html            # Upload de arquivos
│   ├── revisao_categorias.html # Revisão de categorias
│   └── cadastros/             # Templates de cadastro
├── tests/
│   └── test_*.py              # Testes automatizados
└── utils/
    ├── __pycache__/           # Cache Python
    ├── camelot/               # Biblioteca Camelot
    ├── ofxparse/              # Parser OFX
    ├── PyMuPDF/               # PyMuPDF
    └── tabula-py/             # Tabula-py
```

## 🔄 Fluxo de Processamento

1. **Upload do Extrato**
   - Usuário faz upload do PDF bancário
   - Sistema identifica automaticamente o banco

2. **Extração de Dados**
   - PyMuPDF extrai texto do PDF
   - Regex identifica CNPJ, empresa, conta
   - Tabula-py extrai tabelas de transações

3. **Processamento**
   - Dados são normalizados e estruturados
   - Transações são categorizadas automaticamente
   - Valores são validados e formatados

4. **Armazenamento**
   - Dados salvos no SQLite
   - Cache em JSON para performance
   - Logs de processamento mantidos

5. **Revisão Manual**
   - Interface web para revisão de categorias
   - Sugestões de IA para transações duvidosas
   - Aprovação/correção manual

## 🎯 APIs Disponíveis

### Endpoints Principais
- `GET /` - Dashboard principal
- `GET /upload` - Página de upload
- `GET /revisao-categorias` - Revisão de categorias
- `GET /cadastros` - Menu de cadastros

### APIs de Cadastro
- `POST /api/usuarios` - Criar usuário
- `POST /api/empresas` - Criar empresa
- `POST /api/contas` - Criar conta bancária
- `POST /api/cartoes` - Criar cartão
- `POST /api/contatos` - Criar contato

### API de Processamento
- `POST /process` - Processar arquivo/extrato

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para suporte ou dúvidas:
- Abra uma issue no GitHub
- Entre em contato: seu-email@exemplo.com

## 🔄 Roadmap

### Próximas Features
- [ ] **Dashboard com gráficos** (Chart.js)
- [ ] **API REST completa** para integrações
- [ ] **Bot Telegram** para notificações
- [ ] **Exportação para Excel/PDF**
- [ ] **Backup automático** da base de dados
- [ ] **Multi-usuário** com autenticação
- [ ] **Integração com bancos** via API
- [ ] **Aplicativo mobile** (React Native)

### Melhorias Técnicas
- [ ] **Docker Compose** para desenvolvimento
- [ ] **Testes automatizados** completos
- [ ] **CI/CD com GitHub Actions**
- [ ] **Documentação da API** (Swagger)
- [ ] **Monitoramento** com logs estruturados
- [ ] **Cache Redis** para performance
- [ ] **Banco PostgreSQL** para produção

---

⭐ **Star este repositório** se o projeto foi útil para você!

Desenvolvido com ❤️ para facilitar a gestão financeira pessoal e empresarial.
# Edite o arquivo .env com suas chaves

# Iniciar o assistente
python main.py

# Interface Web (opcional)
python api_server.py
# Acesse: http://localhost:5001
```

## 🌐 Interface Web

O assistente possui uma interface web amigável para visualizar dados e fazer uploads:

### Funcionalidades
- **Dashboard**: Visão geral com estatísticas e últimos extratos
- **Extratos**: Lista completa de extratos processados com filtros
- **Upload**: Interface drag-and-drop para processar novos extratos
- **Relatórios**: Gráficos e análises visuais (em desenvolvimento)

### Como usar
1. Execute o servidor web: `python api_server.py`
2. Abra o navegador em `http://localhost:5001`
3. Navegue pelas seções usando o menu lateral
4. Faça upload de extratos PDFs/TXT diretamente pela interface

### Benefícios da Interface Web
- ✅ Visualização clara dos dados
- ✅ Upload fácil de arquivos
- ✅ Navegação intuitiva
- ✅ Relatórios visuais
- ✅ Acesso remoto via navegador

## � Processamento de Extratos Bancários

O assistente possui um sistema avançado para processamento de extratos bancários com as seguintes funcionalidades:

### Funcionalidades do Processamento
- **Extração Inteligente**: Suporte a múltiplos bancos (Itaú, Bradesco, Santander, etc.)
- **Categorização Automática**: Algoritmos de IA para sugerir categorias apropriadas
- **Revisão Interativa**: Permite ao usuário confirmar, alterar ou adicionar categorias
- **Integração Financeira**: Importação automática para controle financeiro
- **Relatórios Detalhados**: Análises completas com gráficos e estatísticas

### Como Usar o Processamento
```bash
# Via interface de linha de comando
python seletor_arquivos.py

# Via interface web
python api_server.py
# Acesse: http://localhost:5001/upload-extrato
```

### Processo de Revisão de Categorias
1. **Upload do Extrato**: Arquivo PDF ou TXT do banco
2. **Extração de Dados**: Texto é processado e transações são identificadas
3. **Categorização Automática**: Sistema sugere categorias para cada transação
4. **Revisão Visual**: **Interface web amigável** para revisar e editar categorias:
   - ✅ Confirmar categorias sugeridas
   - 🔄 Alterar para categoria existente
   - ➕ **Adicionar nova categoria personalizada**
   - 📋 Aplicar categoria a múltiplas transações
   - 🔍 Filtrar e buscar transações
5. **Integração Final**: Transações são importadas com categorias confirmadas

### Exemplo de Revisão Visual (Interface Web)
```
🌐 REVISÃO DE CATEGORIAS:
------------------------------
📱 Abrindo interface web para revisão visual...
📝 Acesse: http://localhost:5001/revisao-categorias
💡 Use o navegador para revisar e confirmar as categorias

✅ Navegador aberto automaticamente!

[Interface Web Abre com:]
• Tabela interativa com todas as transações
• Dropdowns para alterar categorias
• Filtros por tipo, categoria e busca
• Botão "+ Nova Categoria" para adicionar personalizadas
• Aplicar categoria a múltiplas transações
• Estatísticas em tempo real
• Botão "Salvar e Integrar" quando terminar
```

🎉 Revisão concluída na interface web!

🎉 Revisão de categorias concluída!

## �📁 Estrutura do Projeto

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
| `/extrato [anexo]` | Processar extrato bancário |
| `/extratos` | Ver extratos processados |
| `/fatura [anexo]` | Processar fatura |
| `/vendas` | Relatório de vendas |
| `/tarefa [texto]` | Criar tarefa rápida |

## 📄 Licença

MIT License
