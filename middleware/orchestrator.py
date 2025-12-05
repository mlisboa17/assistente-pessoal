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
        
        try:
            from modules.faturas import FaturasModule
            self.modules['faturas'] = FaturasModule()
            # Conecta com módulo de agenda para agendar boletos
            if 'agenda' in self.modules:
                self.modules['faturas'].set_agenda_module(self.modules['agenda'])
        except ImportError:
            pass
        
        try:
            from modules.voz import VozModule
            self.modules['voz'] = VozModule()
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
        
        # Verifica se há pendência de categoria para responder
        if 'financas' in self.modules and user_id:
            resultado = self.modules['financas']._processar_categoria_pendente(user_id, message)
            if resultado:
                return resultado
        
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
        """Processa linguagem natural - SEM PRECISAR DE /"""
        text = message.lower().strip()
        
        # ========== FINANÇAS ==========
        import re
        
        # Função para converter números por extenso para dígitos
        def texto_para_numero(texto):
            """Converte 'cinquenta reais' para 50"""
            numeros = {
                'zero': 0, 'um': 1, 'uma': 1, 'dois': 2, 'duas': 2, 'três': 3, 'tres': 3,
                'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9,
                'dez': 10, 'onze': 11, 'doze': 12, 'treze': 13, 'quatorze': 14, 'catorze': 14,
                'quinze': 15, 'dezesseis': 16, 'dezessete': 17, 'dezoito': 18, 'dezenove': 19,
                'vinte': 20, 'trinta': 30, 'quarenta': 40, 'cinquenta': 50,
                'sessenta': 60, 'setenta': 70, 'oitenta': 80, 'noventa': 90,
                'cem': 100, 'cento': 100, 'duzentos': 200, 'trezentos': 300,
                'quatrocentos': 400, 'quinhentos': 500, 'seiscentos': 600,
                'setecentos': 700, 'oitocentos': 800, 'novecentos': 900,
                'mil': 1000
            }
            
            texto_lower = texto.lower()
            total = 0
            parcial = 0
            
            # Primeiro tenta encontrar número direto
            num_match = re.search(r'(\d+(?:[.,]\d+)?)', texto)
            if num_match:
                return float(num_match.group(1).replace(',', '.'))
            
            # Tenta converter por extenso
            palavras = re.findall(r'\b\w+\b', texto_lower)
            for palavra in palavras:
                if palavra in numeros:
                    valor = numeros[palavra]
                    if valor == 1000:
                        parcial = (parcial if parcial else 1) * 1000
                    elif valor >= 100:
                        parcial = (parcial if parcial else 0) + valor
                    else:
                        parcial += valor
                elif palavra == 'e':
                    continue
                elif palavra in ['reais', 'real', 'conto', 'contos', 'pila', 'pilas']:
                    total += parcial
                    parcial = 0
            
            total += parcial
            return total if total > 0 else None
        
        # Registrar despesa: "gastei 50 no almoço", "paguei cinquenta reais de luz"
        gasto_patterns = ['gastei', 'paguei', 'comprei', 'despesa', 'gastar', 'pagar']
        if any(p in text for p in gasto_patterns):
            valor = texto_para_numero(text)
            if valor and valor > 0:
                descricao = text
                if 'financas' in self.modules:
                    return await self.modules['financas'].handle('despesas', [str(valor), descricao], user_id, attachments)
        
        # Registrar entrada: "recebi 1000", "ganhei quinhentos reais"
        entrada_patterns = ['recebi', 'ganhei', 'entrada', 'salário', 'salario', 'receber']
        if any(p in text for p in entrada_patterns):
            valor = texto_para_numero(text)
            if valor and valor > 0:
                descricao = text
                if 'financas' in self.modules:
                    return await self.modules['financas'].handle('entrada', [str(valor), descricao], user_id, attachments)
        
        # Ver gastos: "gastos", "quanto gastei", "minhas despesas"
        if any(word in text for word in ['gastos', 'quanto gastei', 'minhas despesas', 'despesas do mês']):
            if 'financas' in self.modules:
                return await self.modules['financas'].handle('gastos', [], user_id, attachments)
        
        # Ver saldo: "saldo", "quanto tenho", "meu dinheiro"
        if any(word in text for word in ['saldo', 'quanto tenho', 'meu dinheiro', 'finanças', 'financas']):
            if 'financas' in self.modules:
                return await self.modules['financas'].handle('saldo', [], user_id, attachments)
        
        # ========== AGENDA ==========
        # Detecta menção a datas - ativa agenda automaticamente
        datas_patterns = [
            # Dias relativos
            'hoje', 'amanhã', 'amanha', 'depois de amanhã', 'depois de amanha',
            'ontem', 'anteontem',
            # Dias da semana
            'segunda', 'terça', 'terca', 'quarta', 'quinta', 'sexta', 'sábado', 'sabado', 'domingo',
            'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira',
            # Períodos
            'próxima semana', 'proxima semana', 'semana que vem', 'fim de semana',
            'próximo mês', 'proximo mes', 'mês que vem', 'mes que vem',
            'esse mês', 'este mês', 'essa semana', 'esta semana',
            # Datas específicas
            'dia ', '/01', '/02', '/03', '/04', '/05', '/06', '/07', '/08', '/09', '/10', '/11', '/12',
            # Horários
            'às ', 'as ', ' horas', ':00', ':30', 'meio-dia', 'meio dia', 'meia-noite',
            # Expressões de tempo
            'daqui a', 'daqui há', 'em uma hora', 'em duas horas', 'em 1 hora', 'em 2 horas',
            'de manhã', 'de manha', 'de tarde', 'de noite', 'à noite', 'a noite',
            # Ações de agenda
            'marcar', 'agendar', 'compromisso', 'reunião', 'reuniao', 'encontro', 'consulta'
        ]
        
        if any(p in text for p in datas_patterns):
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle_natural(message, None, user_id, attachments)
        
        # Criar lembrete: "lembrete amanhã pagar conta", "me lembra de..."
        if any(word in text for word in ['lembrete', 'me lembra', 'lembre-me', 'lembrar']):
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle_natural(message, None, user_id, attachments)
        
        # Ver agenda: "agenda", "compromissos", "eventos"
        if any(word in text for word in ['agenda', 'compromissos', 'eventos', 'reuniões']):
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle('agenda', [], user_id, attachments)
        
        # ========== TAREFAS ==========
        # Criar tarefa: "tarefa comprar leite", "adiciona tarefa..."
        if any(word in text for word in ['tarefa', 'todo', 'afazer', 'pendente']):
            if 'tarefas' in self.modules:
                return await self.modules['tarefas'].handle_natural(message, None, user_id, attachments)
        
        # ========== FATURAS/BOLETOS ==========
        # Processar PDF se tiver anexo
        if attachments:
            for anexo in attachments:
                if anexo.lower().endswith('.pdf'):
                    if 'faturas' in self.modules:
                        return await self.modules['faturas'].handle('fatura', [], user_id, attachments)
        
        # Falar sobre fatura/boleto
        if any(word in text for word in ['boleto', 'fatura', 'conta para pagar']):
            if 'faturas' in self.modules:
                return await self.modules['faturas'].handle('fatura', [], user_id, attachments)
        
        # ========== COMANDOS GERAIS ==========
        if any(word in text for word in ['ajuda', 'help', 'comandos', 'o que você faz']):
            return RESPONSES['help']
        
        if any(word in text for word in ['status', 'como está', 'funcionando']):
            return self._get_status()
        
        if any(word in text for word in ['oi', 'olá', 'ola', 'eae', 'ei', 'bom dia', 'boa tarde', 'boa noite']):
            return "👋 Olá! Como posso ajudar?\n\nDiga algo como:\n• *gastei 50 no almoço*\n• *quanto gastei esse mês*\n• *lembrete amanhã pagar conta*\n• Ou envie um *boleto em PDF*!"
        
        # Analisa com NLP como fallback
        analysis = self.nlp.analyze(message)
        
        # Se identificou intenção clara
        if analysis.intent and analysis.confidence > 0.7:
            module_name = COMMAND_MAPPING.get(analysis.intent)
            if module_name and module_name in self.modules:
                module = self.modules[module_name]
                return await module.handle_natural(
                    message, analysis, user_id, attachments
                )
        
        # Não entendeu - dá dicas
        return """🤔 Não entendi. Tente algo como:

💰 *Finanças:*
• gastei 50 no almoço
• recebi 1000 de salário
• quanto gastei esse mês

📅 *Agenda:*
• lembrete amanhã reunião
• agenda de hoje

📋 *Tarefas:*
• tarefa comprar leite

📄 *Boletos:*
• Envie um PDF de boleto"""
    
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
