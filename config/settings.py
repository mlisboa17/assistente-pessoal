"""
⚙️ Configurações do Assistente
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Configurações gerais do sistema"""
    
    # Geral
    debug: bool = True
    log_level: str = "INFO"
    timezone: str = "America/Sao_Paulo"
    language: str = "pt-BR"
    
    # Banco de Dados
    database_url: str = "sqlite:///data/assistente.db"
    
    # Limites
    max_message_length: int = 4096
    max_file_size_mb: int = 50
    
    # 🆕 Configuração de IA (Gemini)
    # True = Usa Gemini para melhor precisão (gratuito até o limite)
    # False = Usa apenas métodos tradicionais (OCR/regex) - 100% gratuito
    usar_gemini: bool = True
    
    def __post_init__(self):
        """Carrega valores do ambiente"""
        self.debug = os.getenv('DEBUG', 'True').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.timezone = os.getenv('TIMEZONE', 'America/Sao_Paulo')
        self.language = os.getenv('LANGUAGE', 'pt-BR')
        self.database_url = os.getenv('DATABASE_URL', self.database_url)
        # Carrega configuração de Gemini do ambiente
        self.usar_gemini = os.getenv('USAR_GEMINI', 'True').lower() == 'true'


# Instância global de configurações
SETTINGS = Settings()


# Mapeamento de comandos para módulos
COMMAND_MAPPING = {
    # Agenda
    'agenda': 'agenda',
    'compromissos': 'agenda',
    'lembrete': 'agenda',
    'lembretes': 'agenda',
    'calendario': 'agenda',
    
    # E-mails
    'email': 'emails',
    'emails': 'emails',
    'mail': 'emails',
    'inbox': 'emails',
    
    # Finanças
    'gastos': 'financas',
    'despesas': 'financas',
    'saldo': 'financas',
    'financas': 'financas',
    'dinheiro': 'financas',
    'entrada': 'financas',
    'sugestoes': 'financas',
    'aprovar': 'financas',
    'rejeitar': 'financas',
    'categorias': 'financas',
    'categoria': 'financas',
    'criar': 'financas',
    'adicionar': 'financas',
    
    # Faturas
    'fatura': 'faturas',
    'faturas': 'faturas',
    'extrato': 'faturas',
    'boleto': 'faturas',
    
    # Vendas
    'vendas': 'vendas',
    'estoque': 'vendas',
    'produtos': 'vendas',
    'logos': 'vendas',
    
    # Tarefas
    'tarefa': 'tarefas',
    'tarefas': 'tarefas',
    'todo': 'tarefas',
    'fazer': 'tarefas',
    'concluir': 'tarefas',
    
    # Cancelar/Remover (pode ser em qualquer módulo)
    'cancelar': 'sistema',  # Será roteado dinamicamente
    'remover': 'sistema',
    'excluir': 'sistema',
    'deletar': 'sistema',
    
    # Alertas
    'alerta': 'alertas',
    'alertas': 'alertas',
    'gatilhos': 'alertas',
    'notificacao': 'alertas',
    'silenciar': 'alertas',
    
    # Metas
    'meta': 'metas',
    'metas': 'metas',
    
    # Notificações
    'notificacoes': 'notificacoes',
    
    # Segurança
    'pin': 'seguranca',
    'logout': 'seguranca',
    'seguranca': 'seguranca',
    
    # Perfil
    'config': 'perfil',
    'configuracoes': 'perfil',
    'exportar': 'perfil',
    'perfil': 'perfil',
    
    # Sistema
    'ajuda': 'sistema',
    'help': 'sistema',
    'status': 'sistema',
    'dashboard': 'sistema',
    'grafico': 'sistema',
    'login': 'agenda',
    'conectar': 'agenda',
}

# Respostas padrão
RESPONSES = {
    'welcome': """
🤖 *Olá! Sou seu Assistente Pessoal.*

Posso ajudar você com:
📅 Agenda e lembretes
📧 E-mails
💰 Finanças e gastos
📄 Faturas e extratos
📊 Vendas e relatórios
✅ Tarefas rápidas
🎯 Metas financeiras
🔔 Notificações proativas

💡 *Dica:* Você pode conversar naturalmente comigo!
Exemplos: "gastos", "tarefas", "me lembra de...", "gastei 50 no mercado"

Digite "ajuda" para ver todos os comandos.
""",
    
    'help': """
📚 *Comandos Disponíveis*
_(Não precisa usar "/" - basta digitar!)_

*🔐 Conta Google:*
login - Conectar sua conta Google
logout - Desconectar Google
status - Ver seu status completo

*📅 Agenda:*
agenda - Ver compromissos
lembrete [texto] [hora] - Criar lembrete

*📧 E-mails:*
emails - Ver últimos e-mails
email [busca] - Buscar e-mail

*💰 Finanças:*
gastos - Resumo de gastos
despesas [valor] [desc] - Registrar despesa
entrada [valor] [desc] - Registrar entrada
saldo - Ver saldo atual

*📄 Faturas:*
fatura - Processar fatura (envie PDF)
boletos - Ver boletos pendentes
pago [id] - Marcar boleto como pago

*📊 Vendas:*
vendas - Relatório de vendas
venda [produto] [valor] - Registrar venda
estoque - Ver estoque

*✅ Tarefas:*
tarefa [texto] - Criar tarefa
tarefas - Ver tarefas pendentes
concluir [id] - Concluir tarefa

*🎯 Metas:*
metas - Ver metas ativas
meta [nome] [valor] - Criar meta
meta depositar [id] [valor] - Depositar

*🔔 Notificações:*
notificacoes - Configurar notificações
silenciar - Pausar notificações

*⚙️ Configurações:*
config - Menu de configurações
config nome [seu nome] - Alterar nome
config resumo [HH:MM] - Horário do resumo
exportar - Exportar seus dados

*🎤 Voz e Arquivos:*
Envie um áudio e eu transcrevo!
Envie um PDF e eu processo!

*📈 Dashboard:*
dashboard - Abrir painel web

*💬 Linguagem Natural:*
"gastei 50 no mercado"
"nova tarefa: comprar leite"
"me lembra de ligar às 10h"
"quanto gastei esse mês?"
""",
    
    'unknown': "🤔 Não entendi. Digite 'ajuda' para ver os comandos disponíveis.",
    'error': "❌ Ocorreu um erro. Tente novamente.",
    'processing': "⏳ Processando...",
}
