"""
🎯 Orquestrador - Decide qual módulo acionar
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import re

from config.settings import COMMAND_MAPPING, RESPONSES
from middleware.command_parser import CommandParser
from middleware.nlp_engine import NLPEngine


@dataclass
class ProcessedMessage:
    """Mensagem processada"""
    original: str
    command: Optional[str] = None
    module: Optional[str] = None
    args: list = None
    intent: Optional[str] = None
    entities: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.entities is None:
            self.entities = {}


class Orchestrator:
    """Orquestra o fluxo de mensagens para os módulos corretos"""
    
    def __init__(self):
        self.parser = CommandParser()
        self.nlp = NLPEngine()
        self.modules = {}
        self._load_modules()
    
    def _load_modules(self):
        """Carrega os módulos disponíveis"""
        try:
            from modules.agenda import AgendaModule
            self.modules['agenda'] = AgendaModule()
        except ImportError:
            pass
        
        try:
            from modules.emails import EmailModule
            self.modules['emails'] = EmailModule()
        except ImportError:
            pass
        
        try:
            from modules.financas import FinancasModule
            self.modules['financas'] = FinancasModule()
        except ImportError:
            pass
        
        try:
            from modules.tarefas import TarefasModule
            self.modules['tarefas'] = TarefasModule()
        except ImportError:
            pass
    
    async def process(self, message: str, user_id: str = None, 
                      attachments: list = None) -> str:
        """
        Processa uma mensagem e retorna a resposta
        
        Args:
            message: Texto da mensagem
            user_id: ID do usuário
            attachments: Lista de anexos (arquivos)
            
        Returns:
            Resposta para o usuário
        """
        # Limpa a mensagem
        message = message.strip()
        
        if not message:
            return RESPONSES['unknown']
        
        # Verifica se é comando direto
        if message.startswith('/'):
            return await self._handle_command(message, user_id, attachments)
        
        # Tenta entender com NLP
        return await self._handle_natural_language(message, user_id, attachments)
    
    async def _handle_command(self, message: str, user_id: str, 
                               attachments: list) -> str:
        """Processa comandos diretos (/comando)"""
        parsed = self.parser.parse(message)
        
        # Comandos especiais
        if parsed.command in ['start', 'inicio']:
            return RESPONSES['welcome']
        
        if parsed.command in ['help', 'ajuda']:
            return RESPONSES['help']
        
        if parsed.command == 'status':
            return self._get_status()
        
        # Encontra o módulo correspondente
        module_name = COMMAND_MAPPING.get(parsed.command)
        
        if module_name and module_name in self.modules:
            module = self.modules[module_name]
            return await module.handle(parsed.command, parsed.args, 
                                       user_id, attachments)
        
        return RESPONSES['unknown']
    
    async def _handle_natural_language(self, message: str, user_id: str,
                                        attachments: list) -> str:
        """Processa linguagem natural"""
        # Analisa com NLP
        analysis = self.nlp.analyze(message)
        
        # Se identificou intenção clara
        if analysis.intent and analysis.confidence > 0.7:
            module_name = COMMAND_MAPPING.get(analysis.intent)
            if module_name and module_name in self.modules:
                module = self.modules[module_name]
                return await module.handle_natural(
                    message, analysis, user_id, attachments
                )
        
        # Resposta genérica com sugestões
        return self._suggest_commands(message)
    
    def _get_status(self) -> str:
        """Retorna status do sistema"""
        modules_status = []
        for name, module in self.modules.items():
            status = "✅" if module else "❌"
            modules_status.append(f"  {status} {name.capitalize()}")
        
        return f"""
📊 *Status do Sistema*

🤖 Assistente: Online
📦 Módulos Ativos: {len(self.modules)}

*Módulos:*
{chr(10).join(modules_status)}

⏰ Última atualização: Agora
"""
    
    def _suggest_commands(self, message: str) -> str:
        """Sugere comandos baseado na mensagem"""
        message_lower = message.lower()
        suggestions = []
        
        keywords = {
            'agenda': ['agenda', 'compromisso', 'reunião', 'lembrete', 'marcar'],
            'email': ['email', 'mail', 'mensagem', 'inbox', 'caixa'],
            'financas': ['gasto', 'despesa', 'dinheiro', 'saldo', 'conta'],
            'tarefa': ['tarefa', 'fazer', 'pendente', 'todo', 'lista'],
        }
        
        for cmd, words in keywords.items():
            for word in words:
                if word in message_lower:
                    suggestions.append(f"/{cmd}")
                    break
        
        if suggestions:
            return f"🤔 Você quis dizer:\n" + "\n".join(suggestions) + "\n\nDigite /ajuda para mais opções."
        
        return RESPONSES['unknown']
