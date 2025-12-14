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
    
    def __post_init__(self):
        """Carrega valores do ambiente"""
        self.debug = os.getenv('DEBUG', 'True').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.timezone = os.getenv('TIMEZONE', 'America/Sao_Paulo')
        self.language = os.getenv('LANGUAGE', 'pt-BR')
        self.database_url = os.getenv('DATABASE_URL', self.database_url)


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
    
    # Faturas
    'fatura': 'faturas',
    'faturas': 'faturas',
    'boleto': 'faturas',
    
    # Extratos Bancários
    'extrato': 'extratos',
    'extratos': 'extratos',
    'banco': 'extratos',
    'conta': 'extratos',
    
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
    
    # Sistema
    'ajuda': 'sistema',
    'help': 'sistema',
    'status': 'sistema',
    'config': 'sistema',
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

Digite /ajuda para ver todos os comandos.
""",
    
    'help': """
📚 *Comandos Disponíveis:*

*Agenda:*
/agenda - Ver compromissos
/lembrete [texto] [hora] - Criar lembrete

*E-mails:*
/emails - Ver últimos e-mails
/email [busca] - Buscar e-mail

*Finanças:*
/gastos - Resumo de gastos
/despesas [valor] [desc] - Registrar despesa

*Faturas:*
/fatura - Processar fatura (envie o arquivo)
/extrato - Ver extrato

*Vendas:*
/vendas - Relatório de vendas
/estoque - Ver estoque

*Tarefas:*
/tarefa [texto] - Criar tarefa
/tarefas - Ver tarefas pendentes

*Sistema:*
/status - Status do sistema
/config - Configurações
""",
    
    'unknown': "🤔 Não entendi. Digite /ajuda para ver os comandos disponíveis.",
    'error': "❌ Ocorreu um erro. Tente novamente.",
    'processing': "⏳ Processando...",
}
