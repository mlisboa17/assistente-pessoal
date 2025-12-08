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
            # 🆕 Conecta com módulo de finanças para registrar despesas
            if 'financas' in self.modules:
                self.modules['faturas'].set_financas_module(self.modules['financas'])
        except ImportError:
            pass
        
        try:
            from modules.voz import VozModule
            self.modules['voz'] = VozModule()
        except ImportError:
            pass
        
        # Novos módulos
        try:
            from modules.vendas import VendasModule
            self.modules['vendas'] = VendasModule()
        except ImportError:
            pass
        
        try:
            from modules.alertas import AlertasModule
            self.modules['alertas'] = AlertasModule()
            # Conecta módulos para gatilhos automáticos
            if 'financas' in self.modules or 'vendas' in self.modules:
                self.modules['alertas'].set_modules(
                    financas=self.modules.get('financas'),
                    vendas=self.modules.get('vendas'),
                    agenda=self.modules.get('agenda')
                )
        except ImportError:
            pass
        
        # Módulo de Metas Financeiras
        try:
            from modules.metas import MetasModule
            self.modules['metas'] = MetasModule()
            # Conecta com finanças para verificar limites
            if 'financas' in self.modules:
                self.modules['metas'].set_financas_module(self.modules['financas'])
        except ImportError:
            pass
        
        # Módulo de Notificações
        try:
            from modules.notificacoes import NotificacoesModule
            self.modules['notificacoes'] = NotificacoesModule()
            # Conecta com outros módulos
            self.modules['notificacoes'].set_modules(
                financas=self.modules.get('financas'),
                agenda=self.modules.get('agenda'),
                faturas=self.modules.get('faturas'),
                metas=self.modules.get('metas')
            )
        except ImportError:
            pass
        
        # Módulo de Segurança
        try:
            from modules.seguranca import SegurancaModule
            self.modules['seguranca'] = SegurancaModule()
        except ImportError:
            pass
        
        # Módulo de Perfil do Usuário
        try:
            from modules.perfil import PerfilModule
            self.modules['perfil'] = PerfilModule()
        except ImportError:
            pass
        
        # Módulo de Comprovantes
        try:
            from modules.comprovantes import ComprovantesModule
            self.modules['comprovantes'] = ComprovantesModule()
        except ImportError:
            pass
        
        # Módulo de Cadastros
        try:
            from modules.cadastros import CadastrosModule
            self.modules['cadastros'] = CadastrosModule()
        except ImportError:
            pass
        
        # Módulo de Agenda de Grupo
        try:
            from modules.agenda_grupo import AgendaGrupoModule
            self.modules['agenda_grupo'] = AgendaGrupoModule()
        except ImportError:
            pass
        
        # Módulo de OCR
        try:
            from modules.ocr_engine import OCREngine
            self.modules['ocr'] = OCREngine()
        except ImportError:
            pass
        
        # Módulo de Configurações
        try:
            from modules.configuracoes import ConfiguracoesModule
            self.modules['configuracoes'] = ConfiguracoesModule()
        except ImportError:
            pass
        
        # Módulo de Monitor de Emails
        try:
            from modules.email_monitor import EmailMonitorModule
            self.modules['email_monitor'] = EmailMonitorModule()
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
        
        # Verifica se é novo usuário - marca onboarding como completo automaticamente
        if 'perfil' in self.modules and user_id:
            perfil_mod = self.modules['perfil']
            if perfil_mod.is_novo_usuario(user_id):
                # Registra usuário e marca onboarding como completo (sem exigir Google)
                perfil = perfil_mod.get_perfil(user_id)
                perfil_mod.atualizar_perfil(user_id, onboarding_completo=True)
                # Envia boas-vindas simplificadas
                return self._mensagem_boas_vindas_simples()
            else:
                # Registra acesso
                perfil_mod.registrar_acesso(user_id)
        
        # Verifica se há comprovante pendente de confirmação
        if 'comprovantes' in self.modules and user_id:
            resultado = await self._processar_confirmacao_comprovante(user_id, message)
            if resultado:
                return resultado
        
        # Verifica confirmação de apagar dados
        if message.strip().upper() == 'APAGAR TUDO' and 'perfil' in self.modules:
            self.modules['perfil'].apagar_dados_usuario(user_id)
            return "✅ Todos os seus dados foram apagados.\n\nSinta-se à vontade para começar de novo!"
        
        # Detecta código do Google OAuth (começa com 4/ ou é código longo com /)
        text_strip = message.strip()
        if text_strip.startswith('4/') or (len(text_strip) > 40 and '/' in text_strip and ' ' not in text_strip):
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle('login', [text_strip], user_id, attachments)
        
        # Verifica segurança (se ativa)
        if 'seguranca' in self.modules:
            comando = message.split()[0].lstrip('/').lower() if message.startswith('/') else ''
            autorizado, msg_erro = self.modules['seguranca'].verificar_acesso(user_id, comando)
            if not autorizado:
                return msg_erro
        
        # Verifica se há pendência de categoria para responder
        if 'financas' in self.modules and user_id:
            resultado = self.modules['financas']._processar_categoria_pendente(user_id, message)
            if resultado:
                return resultado
        
        # Verifica se é comando direto (com ou sem barra)
        if message.startswith('/'):
            return await self._handle_command(message, user_id, attachments)
        
        # Tenta detectar comandos sem barra
        comando_sem_barra = await self._detectar_comando_sem_barra(message, user_id, attachments)
        if comando_sem_barra:
            return comando_sem_barra
        
        # Tenta entender com NLP
        return await self._handle_natural_language(message, user_id, attachments)
    
    async def _handle_command(self, message: str, user_id: str, 
                               attachments: list) -> str:
        """Processa comandos diretos (/comando)"""
        parsed = self.parser.parse(message)
        
        # Comandos especiais
        if parsed.command in ['start', 'inicio', 'menu']:
            return self._get_menu_principal(user_id)
        
        if parsed.command in ['oi', 'ola', 'hello', 'hi']:
            return self._get_menu_principal(user_id)
        
        if parsed.command in ['help', 'ajuda']:
            return RESPONSES['help']
        
        # Comando de status completo
        if parsed.command == 'status':
            if 'perfil' in self.modules:
                return self.modules['perfil'].get_status_completo(
                    user_id,
                    google_auth=self.modules.get('agenda', {}).google_auth if 'agenda' in self.modules else None,
                    financas=self.modules.get('financas'),
                    tarefas=self.modules.get('tarefas'),
                    metas=self.modules.get('metas')
                )
            return self._get_status()
        
        # Comando de configurações
        if parsed.command in ['config', 'configuracoes', 'configurações', 'settings']:
            if parsed.args:
                sub_cmd = parsed.args[0].lower()
                args_rest = parsed.args[1:] if len(parsed.args) > 1 else []
                
                # Processar sub-comandos de config
                if sub_cmd == 'nome' and 'perfil' in self.modules:
                    return await self.modules['perfil'].handle('config_nome', args_rest, user_id)
                elif sub_cmd in ['notif', 'notificacoes'] and 'perfil' in self.modules:
                    return await self.modules['perfil'].handle('config_notificacoes', args_rest, user_id)
                elif sub_cmd == 'resumo' and 'perfil' in self.modules:
                    return await self.modules['perfil'].handle('config_resumo', args_rest, user_id)
                elif sub_cmd == 'fuso' and 'perfil' in self.modules:
                    return await self.modules['perfil'].handle('config_fuso', args_rest, user_id)
            
            # Usa o novo módulo de configurações se disponível
            if 'configuracoes' in self.modules:
                return await self.modules['configuracoes'].handle('config', [], user_id)
            elif 'perfil' in self.modules:
                return self.modules['perfil'].get_menu_config(user_id)
            return "Módulo de configurações não disponível."
        
        # Comandos de privacidade
        if parsed.command in ['privacidade', 'privacy']:
            if 'configuracoes' in self.modules:
                return await self.modules['configuracoes'].handle('privacidade', parsed.args, user_id)
            return "Módulo de configurações não disponível."
        
        # Comandos de notificações
        if parsed.command in ['notificacoes', 'notificações', 'notifications']:
            if 'configuracoes' in self.modules:
                return await self.modules['configuracoes'].handle('notificacoes', parsed.args, user_id)
            return "Módulo de configurações não disponível."
        
        # Comandos de preferências
        if parsed.command in ['preferencias', 'preferências', 'preferences']:
            if 'configuracoes' in self.modules:
                return await self.modules['configuracoes'].handle('preferencias', parsed.args, user_id)
            return "Módulo de configurações não disponível."
        
        # Comandos de monitoramento de emails (BLOQUEIA EM GRUPOS)
        if parsed.command in ['monitorar', 'monitor', 'alertar', 'palavras', 'keywords']:
            if 'email_monitor' in self.modules:
                # Obtém serviço Gmail se disponível
                gmail_service = None
                if 'agenda' in self.modules and self.modules['agenda'].google_auth:
                    gmail_service = self.modules['agenda'].google_auth.get_gmail_service(user_id)
                
                return await self.modules['email_monitor'].handle(
                    parsed.command, parsed.args, user_id, 
                    gmail_service=gmail_service, 
                    is_group=False  # Em grupos será bloqueado
                )
            return "Módulo de monitoramento não disponível."
        
        # Comando exportar dados
        if parsed.command == 'exportar':
            if 'perfil' in self.modules:
                return await self.modules['perfil'].handle('exportar', [], user_id)
            return "Módulo de perfil não disponível."
        
        # Comandos de segurança (sempre processar)
        if parsed.command in ['pin', 'seguranca']:
            if 'seguranca' in self.modules:
                return await self.modules['seguranca'].handle(
                    parsed.command, parsed.args, user_id, attachments
                )
        
        # Comandos de login/logout Google
        if parsed.command in ['login', 'conectar', 'logar']:
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle(
                    'login', parsed.args, user_id, attachments
                )
            return "❌ Módulo de agenda não disponível."
        
        if parsed.command in ['logout', 'desconectar']:
            if 'agenda' in self.modules:
                return await self.modules['agenda'].handle(
                    'logout', parsed.args, user_id, attachments
                )
            return "❌ Módulo de agenda não disponível."
        
        # Comandos de metas
        if parsed.command in ['meta', 'metas']:
            if 'metas' in self.modules:
                return await self.modules['metas'].handle(
                    parsed.command, parsed.args, user_id, attachments
                )
        
        # Comandos de notificações
        if parsed.command in ['notificacoes', 'silenciar']:
            if 'notificacoes' in self.modules:
                return await self.modules['notificacoes'].handle(
                    parsed.command, parsed.args, user_id, attachments
                )
        
        # Comandos de cancelar - tenta em múltiplos módulos
        if parsed.command in ['cancelar', 'remover', 'excluir', 'deletar']:
            return await self._handle_cancelar(parsed.args, user_id)
        
        # Encontra o módulo correspondente
        module_name = COMMAND_MAPPING.get(parsed.command)
        
        if module_name and module_name in self.modules:
            module = self.modules[module_name]
            return await module.handle(parsed.command, parsed.args, 
                                       user_id, attachments)
        
        return RESPONSES['unknown']
    
    async def _detectar_comando_sem_barra(self, message: str, user_id: str, 
                                          attachments: list) -> str:
        """
        Detecta comandos escritos sem a barra /
        Permite conversar naturalmente sem precisar de /
        """
        text = message.lower().strip()
        words = text.split()
        first_word = words[0] if words else ""
        
        # Comandos de saudação/menu - retorna menu principal
        saudacoes = ['oi', 'ola', 'olá', 'hello', 'hi', 'menu', 'inicio', 'início', 'start', 'bom dia', 'boa tarde', 'boa noite']
        if text in saudacoes or first_word in saudacoes:
            return self._get_menu_principal(user_id)
        
        # Mapeamento de palavras para comandos
        comandos_diretos = {
            # Agenda
            'agenda': ('agenda', []),
            'compromissos': ('agenda', []),
            'calendario': ('agenda', []),
            'lembretes': ('lembretes', []),
            
            # Tarefas
            'tarefas': ('tarefas', []),
            'afazeres': ('tarefas', []),
            'pendencias': ('tarefas', []),
            'pendências': ('tarefas', []),
            
            # Finanças
            'gastos': ('gastos', []),
            'despesas': ('gastos', []),
            'saldo': ('saldo', []),
            'extrato': ('gastos', []),
            
            # Metas
            'metas': ('metas', []),
            
            # Boletos
            'boletos': ('faturas', []),
            
            # Vendas
            'vendas': ('vendas', []),
            'estoque': ('estoque', []),
            
            # Ajuda
            'ajuda': ('help', []),
            'help': ('help', []),
            'comandos': ('help', []),
            
            # Status e Config
            'status': ('status', []),
            'config': ('config', []),
            'configuracoes': ('config', []),
            'configurações': ('config', []),
            
            # Login/Logout Google
            'login': ('login', []),
            'logar': ('login', []),
            'conectar': ('login', []),
            'logout': ('logout', []),
            'desconectar': ('logout', []),
            
            # Notificações
            'notificacoes': ('notificacoes', []),
            'notificações': ('notificacoes', []),
            
            # Exportar
            'exportar': ('exportar', []),
        }
        
        # Verifica comando direto (primeira palavra)
        if first_word in comandos_diretos:
            cmd, default_args = comandos_diretos[first_word]
            args = words[1:] if len(words) > 1 else default_args
            return await self._handle_command(f'/{cmd} {" ".join(args)}'.strip(), user_id, attachments)
        
        # Comandos que precisam de argumentos
        comandos_com_args = {
            # Tarefas
            'tarefa': 'tarefa',
            'fazer': 'tarefa',
            'todo': 'tarefa',
            
            # Lembrete
            'lembrete': 'lembrete',
            'lembrar': 'lembrete',
            'avisar': 'lembrete',
            
            # Meta
            'meta': 'meta',
            
            # Concluir
            'concluir': 'concluir',
            'feito': 'concluir',
            'pronto': 'concluir',
            'concluído': 'concluir',
            'concluido': 'concluir',
        }
        
        if first_word in comandos_com_args:
            cmd = comandos_com_args[first_word]
            args = ' '.join(words[1:]) if len(words) > 1 else ''
            return await self._handle_command(f'/{cmd} {args}'.strip(), user_id, attachments)
        
        # Frases que indicam comandos
        # "nova tarefa: ..." ou "criar tarefa ..."
        if text.startswith(('nova tarefa', 'criar tarefa', 'adicionar tarefa')):
            texto = text.replace('nova tarefa', '').replace('criar tarefa', '').replace('adicionar tarefa', '')
            texto = texto.lstrip(':').strip()
            if texto:
                return await self._handle_command(f'/tarefa {texto}', user_id, attachments)
        
        # "nova meta: ..." 
        if text.startswith(('nova meta', 'criar meta')):
            texto = text.replace('nova meta', '').replace('criar meta', '')
            texto = texto.lstrip(':').strip()
            if texto:
                return await self._handle_command(f'/meta {texto}', user_id, attachments)
        
        # "me lembra de..." ou "lembra de..."
        if text.startswith(('me lembra', 'lembra de', 'me avisa', 'avisa quando')):
            texto = text
            for prefix in ['me lembra de ', 'me lembra ', 'lembra de ', 'me avisa ', 'avisa quando ']:
                texto = texto.replace(prefix, '')
            if texto:
                return await self._handle_command(f'/lembrete {texto}', user_id, attachments)
        
        # Não detectou comando, retorna None para continuar com NLP
        return None
    
    async def _processar_confirmacao_comprovante(self, user_id: str, message: str) -> str:
        """Processa confirmação de comprovante pendente com novos comandos"""
        if 'comprovantes' not in self.modules:
            return None
        
        comp_module = self.modules['comprovantes']
        
        # Verifica se tem comprovante pendente
        if not comp_module.tem_pendente(user_id):
            return None
        
        texto = message.strip().upper()
        texto_lower = message.lower().strip()
        pendente = comp_module.get_pendente(user_id)
        
        # ========== NOVOS COMANDOS ==========
        
        # 1️⃣ COPIAR - Retorna o código para copiar
        if texto in ['COPIAR', '1', 'CODIGO', 'CÓDIGO', 'CHAVE', 'COPIA']:
            codigo = pendente.get('id_transacao', '') or pendente.get('linha_digitavel', '') or pendente.get('chave_pix', '')
            if codigo:
                return f"""📋 *Código para copiar:*

```
{codigo}
```

💡 Copie o código acima e cole no seu app de pagamento.

━━━━━━━━━━━━━━━━━━━━
Quando pagar, digite *PAGO* para registrar."""
            else:
                return "❌ Não há código disponível para este comprovante."
        
        # 2️⃣ PAGO - Marca como pago e registra despesa
        if texto in ['PAGO', '2', 'PAGUEI', 'JA PAGUEI', 'CONFIRMADO'] or texto_lower.startswith('pago '):
            # Verifica se especificou categoria
            categoria = pendente.get('categoria', pendente.get('categoria_sugerida', 'outros'))
            if texto_lower.startswith('pago '):
                categoria = texto_lower.replace('pago ', '').strip()
            
            # Registra como despesa
            resultado_despesa = ""
            if 'financas' in self.modules:
                financas = self.modules['financas']
                despesa = {
                    'valor': pendente.get('valor', 0),
                    'categoria': categoria,
                    'descricao': pendente.get('destinatario', '') or pendente.get('descricao', '') or pendente.get('tipo', 'Pagamento'),
                    'data': pendente.get('data', ''),
                    'tipo': 'despesa',
                    'comprovante_id': pendente.get('id', '')
                }
                financas.adicionar_transacao(user_id, despesa)
                resultado_despesa = f"💰 Despesa registrada: R$ {pendente.get('valor', 0):.2f} ({categoria})"
            
            # Remove pendência
            comp_module.remover_pendente(user_id)
            
            valor_fmt = f"R$ {pendente.get('valor', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"""✅ *PAGAMENTO CONFIRMADO!*

💰 *Valor:* {valor_fmt}
🏷️ *Categoria:* {categoria.upper()}
📅 *Data:* {pendente.get('data', 'Hoje')}

{resultado_despesa}

━━━━━━━━━━━━━━━━━━━━
💡 Use */financas* para ver seu extrato"""

        # 3️⃣ DESPESA - Registra como despesa (sem marcar pago)
        if texto in ['DESPESA', '3', 'GASTO', 'REGISTRAR'] or texto_lower.startswith('despesa '):
            categoria = pendente.get('categoria', pendente.get('categoria_sugerida', 'outros'))
            if texto_lower.startswith('despesa '):
                categoria = texto_lower.replace('despesa ', '').strip()
            
            if 'financas' in self.modules:
                financas = self.modules['financas']
                despesa = {
                    'valor': pendente.get('valor', 0),
                    'categoria': categoria,
                    'descricao': pendente.get('destinatario', '') or pendente.get('descricao', '') or pendente.get('tipo', 'Pagamento'),
                    'data': pendente.get('data', ''),
                    'tipo': 'despesa',
                    'comprovante_id': pendente.get('id', '')
                }
                financas.adicionar_transacao(user_id, despesa)
                
                comp_module.remover_pendente(user_id)
                
                valor_fmt = f"R$ {pendente.get('valor', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                return f"""💰 *DESPESA REGISTRADA!*

💵 *Valor:* {valor_fmt}
🏷️ *Categoria:* {categoria.upper()}
📝 *Descrição:* {pendente.get('destinatario', '') or pendente.get('descricao', '-')}

━━━━━━━━━━━━━━━━━━━━
💡 Use */financas* para ver seu extrato"""
            return "❌ Módulo de finanças não disponível."

        # 4️⃣ AGENDA / AGENDAR - Salva na agenda
        if texto in ['AGENDA', 'AGENDAR', '4', 'LEMBRETE', 'SALVAR AGENDA']:
            if 'agenda' in self.modules:
                agenda = self.modules['agenda']
                
                # Monta dados do evento
                descricao = pendente.get('destinatario', '') or pendente.get('beneficiario', '') or pendente.get('tipo', 'Pagamento')
                valor = pendente.get('valor', 0)
                data = pendente.get('data_vencimento', '') or pendente.get('data', '')
                
                titulo = f"💳 {descricao} - R$ {valor:.2f}"
                
                # Cria evento/lembrete
                resultado = await agenda.handle('criar', [titulo, data], user_id, [])
                
                valor_fmt = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                return f"""📅 *SALVO NA AGENDA!*

📋 *Evento:* {titulo}
📅 *Data:* {data or 'Hoje'}

{resultado if 'criado' not in resultado.lower() else ''}

━━━━━━━━━━━━━━━━━━━━
Ainda posso:
• *DESPESA* - Registrar como despesa
• *PAGO* - Marcar como pago"""
            return "❌ Módulo de agenda não disponível."

        # 5️⃣ TUDO - Faz tudo de uma vez (pago + despesa + agenda)
        if texto in ['TUDO', '5', 'TODOS', 'TODAS', 'COMPLETO']:
            resultados = []
            valor = pendente.get('valor', 0)
            categoria = pendente.get('categoria', pendente.get('categoria_sugerida', 'outros'))
            descricao = pendente.get('destinatario', '') or pendente.get('beneficiario', '') or pendente.get('descricao', '') or pendente.get('tipo', 'Pagamento')
            data = pendente.get('data_vencimento', '') or pendente.get('data', '')
            
            # 1. Registra despesa
            if 'financas' in self.modules:
                financas = self.modules['financas']
                despesa = {
                    'valor': valor,
                    'categoria': categoria,
                    'descricao': descricao,
                    'data': data,
                    'tipo': 'despesa',
                    'comprovante_id': pendente.get('id', '')
                }
                financas.adicionar_transacao(user_id, despesa)
                resultados.append("✅ Despesa registrada")
            
            # 2. Salva na agenda
            if 'agenda' in self.modules:
                agenda = self.modules['agenda']
                titulo = f"💳 {descricao} - R$ {valor:.2f}"
                await agenda.handle('criar', [titulo, data], user_id, [])
                resultados.append("✅ Salvo na agenda")
            
            # 3. Remove pendência (marca como pago)
            comp_module.remover_pendente(user_id)
            resultados.append("✅ Marcado como pago")
            
            valor_fmt = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"""⭐ *TUDO FEITO!*

💰 *Valor:* {valor_fmt}
🏷️ *Categoria:* {categoria.upper()}
📝 *Descrição:* {descricao}
📅 *Data:* {data or 'Hoje'}

{chr(10).join(resultados)}

━━━━━━━━━━━━━━━━━━━━
💡 Use */financas* para ver seu extrato
📅 Use */agenda* para ver seus eventos"""

        # ❌ CANCELAR
        if texto in ['CANCELAR', 'NAO', 'NÃO', 'N', 'DESCARTAR', 'IGNORAR']:
            comp_module.remover_pendente(user_id)
            return "❌ Comprovante descartado."
        
        # Usa o novo método de processamento de resposta (legado)
        financas_module = self.modules.get('financas')
        resultado = comp_module.processar_resposta_confirmacao(
            message, user_id, financas_module
        )
        
        # Se retornou algo, é uma resposta válida
        if resultado:
            return resultado
        
        # Comandos de edição
        # valor X
        if texto_lower.startswith('valor ') or texto_lower.startswith('valor:'):
            try:
                valor_str = texto_lower.replace('valor:', '').replace('valor ', '').replace('r$', '').replace(',', '.').strip()
                novo_valor = float(valor_str)
                pendente['valor'] = novo_valor
                comp_module.pendentes[user_id] = pendente
                comp_module._save_pendentes()
                return f"✅ Valor alterado para R$ {novo_valor:.2f}\n\nEscolha: *PAGO* | *DESPESA* | *AGENDA* | *TUDO*"
            except:
                return "❌ Valor inválido. Use: *valor 100* ou *valor:50.90*"
        
        # categoria X ou cat:X
        if texto_lower.startswith('categoria ') or texto_lower.startswith('cat:'):
            cat = texto_lower.replace('categoria ', '').replace('cat:', '').strip()
            categorias_validas = ['alimentacao', 'combustivel', 'transporte', 'moradia', 
                                  'saude', 'lazer', 'educacao', 'vestuario', 'tecnologia', 
                                  'contas', 'impostos', 'folha_pagamento', 'outros']
            # Normaliza
            cat = cat.replace('ã', 'a').replace('í', 'i').replace('ú', 'u').replace('ç', 'c')
            if cat in categorias_validas:
                pendente['categoria'] = cat
                pendente['categoria_sugerida'] = cat
                comp_module.pendentes[user_id] = pendente
                comp_module._save_pendentes()
                return f"✅ Categoria alterada para *{cat.upper()}*\n\nEscolha: *PAGO* | *DESPESA* | *AGENDA* | *TUDO*"
            else:
                return "❌ Categoria inválida.\n\nUse: alimentacao, combustivel, transporte, moradia, saude, lazer, educacao, vestuario, tecnologia, contas, impostos, folha_pagamento, outros"
        
        # descricao X ou desc:X
        if texto_lower.startswith('descricao ') or texto_lower.startswith('descrição ') or texto_lower.startswith('desc:'):
            if texto_lower.startswith('desc:'):
                desc = message[5:].strip()
            else:
                desc = message[10:].strip()
            pendente['descricao'] = desc
            comp_module.pendentes[user_id] = pendente
            comp_module._save_pendentes()
            return f"✅ Descrição alterada para: *{desc}*\n\nEscolha: *PAGO* | *DESPESA* | *AGENDA* | *TUDO*"
        
        # SIM (compatibilidade)
        if texto in ['SIM', 'S', 'OK', 'CONFIRMAR', 'SALVAR']:
            # Faz o mesmo que PAGO
            return await self._processar_confirmacao_comprovante(user_id, 'PAGO')
        
        # Não reconheceu - mostra opções
        return """🤔 *Não entendi.*

*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago
3️⃣ *DESPESA* - Registrar como despesa
4️⃣ *AGENDA* - Salvar na agenda
5️⃣ *TUDO* - Pago + Despesa + Agenda

❌ *CANCELAR* - Descartar

*Ou edite os dados:*
• *valor 100* - Altera valor
• *categoria alimentacao* - Altera categoria
• *despesa contas* - Salva com categoria específica"""
    
    async def _handle_cancelar(self, args: list, user_id: str) -> str:
        """Processa comandos de cancelar/remover"""
        if not args:
            return """
❌ *Para cancelar, informe o ID do item.*

Use:
• `cancelar [id]` - Cancela uma tarefa, evento ou lembrete
• `tarefas` - Ver lista de tarefas com IDs
• `agenda` - Ver eventos e lembretes com IDs
"""
        
        item_id = args[0]
        
        # Tenta cancelar em cada módulo que suporta cancelamento
        
        # 1. Tarefas
        if 'tarefas' in self.modules:
            resultado = self.modules['tarefas']._cancelar_tarefa(user_id, item_id)
            if "não encontrada" not in resultado.lower():
                return resultado
        
        # 2. Agenda (eventos e lembretes)
        if 'agenda' in self.modules:
            resultado = self.modules['agenda']._cancelar_item(user_id, item_id)
            if "não encontrado" not in resultado.lower():
                return resultado
        
        return f"❌ Item `{item_id}` não encontrado em nenhum módulo."
    
    def _solicitar_login(self, user_id: str) -> str:
        """Solicita que o usuário faça login para usar o assistente"""
        # Gera URL de login se disponível
        auth_url = None
        if 'agenda' in self.modules:
            google_auth = getattr(self.modules['agenda'], 'google_auth', None)
            if google_auth:
                auth_url = google_auth.get_auth_url(user_id)
        
        msg = """🔐 *Conectar conta Google*

Conectando sua conta Google, você terá acesso a:
• 📅 Google Calendar (agenda e lembretes)
• 📧 Gmail (leitura de e-mails)

━━━━━━━━━━━━━━━━━━━━━

⚠️ *SEM conectar o Google, você NÃO terá:*
❌ Sincronização com Google Calendar
❌ Leitura de e-mails do Gmail

✅ *MAS poderá usar normalmente:*
• 💰 Controle de finanças e gastos
• ✅ Gerenciamento de tarefas
• 🎯 Metas financeiras
• 📄 Processamento de boletos/faturas
• 🧾 Análise de comprovantes
• 🎤 Transcrição de áudios

━━━━━━━━━━━━━━━━━━━━━

"""
        
        if auth_url:
            msg += f"""📱 *Como conectar:*

1️⃣ Clique no link abaixo:
{auth_url}

2️⃣ Faça login com sua conta Google

3️⃣ Copie o código que aparecer

4️⃣ Cole o código aqui no chat

━━━━━━━━━━━━━━━━━━━━━

🔹 Digite *login* para conectar
🔹 Digite *pular* para continuar SEM Google"""
        else:
            msg += """🔹 Digite *login* para conectar sua conta Google
🔹 Digite *pular* para continuar SEM Google"""
        
        return msg
    
    def _mensagem_continuar_sem_google(self) -> str:
        """Mensagem quando usuário escolhe continuar sem Google"""
        return """✅ *Tudo certo! Você pode usar o assistente sem Google.*

Você tem acesso a:
• 💰 *Finanças* - Controle de gastos (digite "gastos")
• ✅ *Tarefas* - Lista de afazeres (digite "tarefas")
• 🎯 *Metas* - Objetivos financeiros (digite "metas")
• 📄 *Boletos* - Envie PDFs de faturas
• 🧾 *Comprovantes* - Envie fotos de comprovantes
• 🎤 *Áudio* - Envie mensagens de voz

━━━━━━━━━━━━━━━━━━━━━

⚠️ *Funcionalidades desativadas (precisa do Google):*
• 📅 Google Calendar
• 📧 Gmail

💡 *Dica:* A qualquer momento digite *login* para conectar sua conta Google.

Digite *ajuda* para ver todos os comandos disponíveis."""
    
    def _mensagem_boas_vindas_simples(self) -> str:
        """Mensagem de boas-vindas simples sem exigir login"""
        return """👋 *Olá! Bem-vindo ao seu Assistente Pessoal!*

━━━━━━━━━━━━━━━━━━━━━

📌 *O que posso fazer por você:*

💰 *Finanças* → "gastei 50 no mercado"
📄 *Boletos* → Envie um PDF
🧾 *Comprovantes* → Envie uma foto
🎤 *Áudio* → Mande um áudio

━━━━━━━━━━━━━━━━━━━━━

🔗 *Conecte sua conta Google* para:
• 📅 Agendar compromissos
• 📧 Gerenciar emails

👉 Digite *login* para conectar

━━━━━━━━━━━━━━━━━━━━━

💬 Digite *menu* para ver todas as opções!"""
    
    def _get_menu_principal(self, user_id: str = None) -> str:
        """Menu principal com opções baseado no status do usuário"""
        
        # Verifica se está logado no Google
        google_conectado = False
        nome_usuario = None
        
        if 'agenda' in self.modules and self.modules['agenda'].google_auth:
            google_auth = self.modules['agenda'].google_auth
            if google_auth.is_authenticated(user_id):
                google_conectado = True
                try:
                    user_info = google_auth.get_user_info(user_id)
                    if user_info:
                        nome_usuario = user_info.get('name', '').split()[0]  # Primeiro nome
                except:
                    pass
        
        # Header personalizado
        if nome_usuario:
            header = f"👋 *Olá, {nome_usuario}!*"
        else:
            header = "👋 *Olá!*"
        
        # Status Google
        if google_conectado:
            google_status = "✅ Google conectado"
        else:
            google_status = "⚪ Google não conectado"
        
        menu = f"""{header}

━━━━━━━━━━━━━━━━━━━━━
{google_status}
━━━━━━━━━━━━━━━━━━━━━

📌 *Escolha uma opção:*

💰 *1. Finanças*
   → "gastei", "recebi", "gastos"
   
📄 *2. Boletos/Faturas*
   → Envie um PDF

🧾 *3. Comprovantes*
   → Envie uma foto
   
🎤 *4. Áudio*
   → Mande um áudio"""
        
        # Opções Google (só se conectado)
        if google_conectado:
            menu += """

📅 *5. Agenda*
   → "eventos", "criar evento"
   
📧 *6. Emails*
   → "emails", "ler emails" """
        
        menu += """

━━━━━━━━━━━━━━━━━━━━━

⚙️ *Outros comandos:*"""
        
        if not google_conectado:
            menu += """
• *login* → Conectar conta Google"""
        else:
            menu += """
• *logout* → Desconectar Google"""
        
        menu += """
• *ajuda* → Ver todos os comandos
• *status* → Ver seu resumo
• *config* → ⚙️ Configurações

━━━━━━━━━━━━━━━━━━━━━

💬 _Ou simplesmente me diga o que precisa!_"""
        
        return menu
    
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
        # Processar PDF ou imagem se tiver anexo
        if attachments:
            for anexo in attachments:
                anexo_lower = anexo.lower()
                # PDF de boleto
                if anexo_lower.endswith('.pdf'):
                    if 'faturas' in self.modules:
                        return await self.modules['faturas'].handle('fatura', [], user_id, attachments)
                # Imagem de boleto (foto)
                if any(anexo_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
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
