"""
Módulo de Configurações do Assistente Pessoal
Permite que usuários personalizem preferências do bot
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List


class ConfiguracoesModule:
    """Gerencia configurações personalizadas de cada usuário"""
    
    # Configurações padrão
    DEFAULT_CONFIG = {
        # Privacidade
        'privacidade': {
            'compartilhar_agenda_grupos': False,  # Não compartilha agenda pessoal em grupos
            'mostrar_email_grupos': False,  # Não mostra emails em grupos
            'permitir_lembretes_grupos': True,  # Permite lembretes de grupo
        },
        # Notificações
        'notificacoes': {
            'lembretes_eventos': True,
            'lembretes_tarefas': True,
            'lembretes_boletos': True,
            'antecedencia_minutos': 30,  # Antecedência padrão
            'horario_resumo_diario': '08:00',  # Hora do resumo diário
            'resumo_diario_ativo': False,
        },
        # Preferências
        'preferencias': {
            'idioma': 'pt-BR',
            'formato_data': 'DD/MM/YYYY',
            'formato_hora': '24h',
            'moeda': 'BRL',
            'fuso_horario': 'America/Sao_Paulo',
        },
        # IA
        'ia': {
            'respostas_detalhadas': True,
            'sugestoes_automaticas': True,
            'cadastro_automatico': True,  # Pergunta se quer cadastrar ao ler comprovantes
        },
        # Integrações
        'integracoes': {
            'google_calendar': False,
            'google_gmail': False,
            'google_drive': False,
        }
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "configuracoes_usuarios.json")
        self._configs: Dict[str, Dict] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Carrega todas as configurações"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._configs = json.load(f)
            except:
                self._configs = {}
    
    def _save_all_configs(self):
        """Salva todas as configurações"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._configs, f, ensure_ascii=False, indent=2)
    
    def get_config(self, user_id: str) -> Dict:
        """Retorna configurações do usuário (cria padrão se não existir)"""
        if user_id not in self._configs:
            self._configs[user_id] = {
                'config': self.DEFAULT_CONFIG.copy(),
                'criado_em': datetime.now().isoformat(),
                'atualizado_em': datetime.now().isoformat()
            }
            self._save_all_configs()
        
        # Garante que todas as chaves padrão existem
        config = self._configs[user_id].get('config', {})
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value.copy() if isinstance(value, dict) else value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in config[key]:
                        config[key][subkey] = subvalue
        
        return config
    
    def set_config(self, user_id: str, categoria: str, chave: str, valor: Any) -> bool:
        """Define uma configuração específica"""
        config = self.get_config(user_id)
        
        if categoria not in config:
            return False
        
        if chave not in config[categoria]:
            return False
        
        config[categoria][chave] = valor
        self._configs[user_id]['config'] = config
        self._configs[user_id]['atualizado_em'] = datetime.now().isoformat()
        self._save_all_configs()
        return True
    
    def get_valor(self, user_id: str, categoria: str, chave: str) -> Any:
        """Retorna valor de uma configuração específica"""
        config = self.get_config(user_id)
        return config.get(categoria, {}).get(chave)
    
    def atualizar_integracao(self, user_id: str, servico: str, ativo: bool):
        """Atualiza status de integração"""
        self.set_config(user_id, 'integracoes', servico, ativo)
    
    # ==================== COMANDOS ====================
    
    async def handle(self, command: str, args: List[str], user_id: str) -> str:
        """Processa comandos de configuração"""
        
        if command in ['config', 'configuracoes', 'configurações', 'settings']:
            return self._menu_configuracoes(user_id)
        
        elif command in ['privacidade', 'privacy']:
            if args:
                return self._ajustar_privacidade(user_id, args)
            return self._menu_privacidade(user_id)
        
        elif command in ['notificacoes', 'notificações', 'notifications']:
            if args:
                return self._ajustar_notificacoes(user_id, args)
            return self._menu_notificacoes(user_id)
        
        elif command in ['preferencias', 'preferências', 'preferences']:
            if args:
                return self._ajustar_preferencias(user_id, args)
            return self._menu_preferencias(user_id)
        
        # Comandos rápidos
        elif command == 'resumo_diario':
            if args:
                return self._toggle_resumo_diario(user_id, args)
            atual = self.get_valor(user_id, 'notificacoes', 'resumo_diario_ativo')
            status = "ativado ✅" if atual else "desativado ❌"
            return f"📊 Resumo diário está {status}\n\nUse: *resumo_diario on/off*"
        
        elif command == 'compartilhar_agenda':
            if args:
                return self._toggle_compartilhar_agenda(user_id, args)
            atual = self.get_valor(user_id, 'privacidade', 'compartilhar_agenda_grupos')
            status = "permitido ✅" if atual else "bloqueado 🔒"
            return f"📅 Compartilhamento de agenda em grupos: {status}\n\nUse: *compartilhar_agenda on/off*"
        
        return self._menu_configuracoes(user_id)
    
    def _menu_configuracoes(self, user_id: str) -> str:
        """Menu principal de configurações"""
        config = self.get_config(user_id)
        
        # Status das integrações
        google_cal = "✅" if config['integracoes'].get('google_calendar') else "❌"
        google_mail = "✅" if config['integracoes'].get('google_gmail') else "❌"
        
        # Status privacidade
        agenda_grupos = "🔓" if config['privacidade'].get('compartilhar_agenda_grupos') else "🔒"
        
        # Status notificações
        resumo = "✅" if config['notificacoes'].get('resumo_diario_ativo') else "❌"
        
        return f"""⚙️ *CONFIGURAÇÕES*

━━━━━━━━━━━━━━━━━━━━━

🔐 *Privacidade*
• Agenda em grupos: {agenda_grupos}
• Emails em grupos: 🔒
→ Digite *privacidade* para ajustar

━━━━━━━━━━━━━━━━━━━━━

🔔 *Notificações*
• Resumo diário: {resumo}
• Antecedência: {config['notificacoes'].get('antecedencia_minutos', 30)} min
→ Digite *notificacoes* para ajustar

━━━━━━━━━━━━━━━━━━━━━

📧 *Monitor de Emails*
Busca palavras-chave a cada 24h
→ Digite *monitorar* para configurar

━━━━━━━━━━━━━━━━━━━━━

🔗 *Integrações Google*
• Calendar: {google_cal}
• Gmail: {google_mail}
→ Digite *login* para conectar

━━━━━━━━━━━━━━━━━━━━━

🤖 *IA & Automação*
• Cadastro automático: {"✅" if config['ia'].get('cadastro_automatico') else "❌"}
• Sugestões: {"✅" if config['ia'].get('sugestoes_automaticas') else "❌"}
→ Digite *preferencias* para ajustar

━━━━━━━━━━━━━━━━━━━━━

💡 *Comandos rápidos:*
• *privacidade* → Ajustar privacidade
• *notificacoes* → Configurar alertas
• *monitorar* → Monitorar emails
• *preferencias* → Personalizar bot"""
    
    def _menu_privacidade(self, user_id: str) -> str:
        """Menu de configurações de privacidade"""
        config = self.get_config(user_id)
        priv = config.get('privacidade', {})
        
        agenda = "🔓 Permitido" if priv.get('compartilhar_agenda_grupos') else "🔒 Bloqueado"
        email = "🔓 Permitido" if priv.get('mostrar_email_grupos') else "🔒 Bloqueado"
        lembretes = "✅ Ativo" if priv.get('permitir_lembretes_grupos') else "❌ Desativado"
        
        return f"""🔐 *PRIVACIDADE*

━━━━━━━━━━━━━━━━━━━━━

📅 *Agenda pessoal em grupos*
Estado: {agenda}
_Quando bloqueado, sua agenda pessoal não é visível em grupos_

📧 *Emails em grupos*
Estado: {email}
_Quando bloqueado, não mostro emails em grupos_

🔔 *Lembretes de grupo*
Estado: {lembretes}
_Receber notificações de eventos do grupo_

━━━━━━━━━━━━━━━━━━━━━

*Para alterar, digite:*

• *privacidade agenda on/off*
• *privacidade email on/off*
• *privacidade lembretes on/off*

━━━━━━━━━━━━━━━━━━━━━

💡 _Em grupos, mantenho suas informações pessoais privadas por padrão_"""
    
    def _menu_notificacoes(self, user_id: str) -> str:
        """Menu de configurações de notificações"""
        config = self.get_config(user_id)
        notif = config.get('notificacoes', {})
        
        eventos = "✅" if notif.get('lembretes_eventos') else "❌"
        tarefas = "✅" if notif.get('lembretes_tarefas') else "❌"
        boletos = "✅" if notif.get('lembretes_boletos') else "❌"
        resumo = "✅" if notif.get('resumo_diario_ativo') else "❌"
        hora_resumo = notif.get('horario_resumo_diario', '08:00')
        antecedencia = notif.get('antecedencia_minutos', 30)
        
        return f"""🔔 *NOTIFICAÇÕES*

━━━━━━━━━━━━━━━━━━━━━

📅 *Lembretes de Eventos*: {eventos}
✅ *Lembretes de Tarefas*: {tarefas}
💰 *Lembretes de Boletos*: {boletos}

━━━━━━━━━━━━━━━━━━━━━

📊 *Resumo Diário*: {resumo}
⏰ *Horário*: {hora_resumo}

⏱️ *Antecedência*: {antecedencia} minutos

━━━━━━━━━━━━━━━━━━━━━

*Para alterar, digite:*

• *notificacoes eventos on/off*
• *notificacoes tarefas on/off*
• *notificacoes boletos on/off*
• *notificacoes resumo on/off*
• *notificacoes horario 08:00*
• *notificacoes antecedencia 30*"""
    
    def _menu_preferencias(self, user_id: str) -> str:
        """Menu de preferências gerais"""
        config = self.get_config(user_id)
        ia = config.get('ia', {})
        pref = config.get('preferencias', {})
        
        cadastro_auto = "✅" if ia.get('cadastro_automatico') else "❌"
        sugestoes = "✅" if ia.get('sugestoes_automaticas') else "❌"
        detalhado = "✅" if ia.get('respostas_detalhadas') else "❌"
        
        return f"""🤖 *PREFERÊNCIAS*

━━━━━━━━━━━━━━━━━━━━━

🧠 *Inteligência Artificial*

• Cadastro automático: {cadastro_auto}
  _Pergunta se deseja cadastrar ao ler documentos_

• Sugestões automáticas: {sugestoes}
  _Sugere ações baseadas no contexto_

• Respostas detalhadas: {detalhado}
  _Explicações mais completas_

━━━━━━━━━━━━━━━━━━━━━

🌍 *Regional*
• Idioma: {pref.get('idioma', 'pt-BR')}
• Fuso: {pref.get('fuso_horario', 'America/Sao_Paulo')}
• Moeda: {pref.get('moeda', 'BRL')}

━━━━━━━━━━━━━━━━━━━━━

*Para alterar, digite:*

• *preferencias cadastro on/off*
• *preferencias sugestoes on/off*
• *preferencias detalhado on/off*"""
    
    def _ajustar_privacidade(self, user_id: str, args: List[str]) -> str:
        """Ajusta configurações de privacidade"""
        if len(args) < 2:
            return "❌ Use: *privacidade [agenda/email/lembretes] [on/off]*"
        
        opcao = args[0].lower()
        valor = args[1].lower() in ['on', 'sim', 'yes', 'ativar', '1', 'true']
        
        mapa = {
            'agenda': 'compartilhar_agenda_grupos',
            'email': 'mostrar_email_grupos',
            'lembretes': 'permitir_lembretes_grupos'
        }
        
        if opcao not in mapa:
            return "❌ Opções: agenda, email, lembretes"
        
        self.set_config(user_id, 'privacidade', mapa[opcao], valor)
        status = "ativado ✅" if valor else "desativado 🔒"
        
        nomes = {'agenda': 'Compartilhamento de agenda', 'email': 'Emails em grupos', 'lembretes': 'Lembretes de grupo'}
        return f"✅ *{nomes[opcao]}* {status}"
    
    def _ajustar_notificacoes(self, user_id: str, args: List[str]) -> str:
        """Ajusta configurações de notificações"""
        if len(args) < 2:
            return "❌ Use: *notificacoes [opcao] [valor]*"
        
        opcao = args[0].lower()
        valor_str = args[1].lower()
        
        mapa_bool = {
            'eventos': 'lembretes_eventos',
            'tarefas': 'lembretes_tarefas',
            'boletos': 'lembretes_boletos',
            'resumo': 'resumo_diario_ativo'
        }
        
        if opcao in mapa_bool:
            valor = valor_str in ['on', 'sim', 'yes', 'ativar', '1', 'true']
            self.set_config(user_id, 'notificacoes', mapa_bool[opcao], valor)
            status = "ativado ✅" if valor else "desativado ❌"
            return f"✅ *{opcao.capitalize()}* {status}"
        
        elif opcao == 'horario':
            # Valida formato HH:MM
            if ':' not in valor_str:
                return "❌ Use formato HH:MM (ex: 08:00)"
            self.set_config(user_id, 'notificacoes', 'horario_resumo_diario', valor_str)
            return f"✅ Horário do resumo diário: *{valor_str}*"
        
        elif opcao == 'antecedencia':
            try:
                minutos = int(valor_str)
                if minutos < 5 or minutos > 1440:
                    return "❌ Antecedência deve ser entre 5 e 1440 minutos"
                self.set_config(user_id, 'notificacoes', 'antecedencia_minutos', minutos)
                return f"✅ Antecedência: *{minutos} minutos*"
            except:
                return "❌ Informe um número válido de minutos"
        
        return "❌ Opções: eventos, tarefas, boletos, resumo, horario, antecedencia"
    
    def _ajustar_preferencias(self, user_id: str, args: List[str]) -> str:
        """Ajusta preferências gerais"""
        if len(args) < 2:
            return "❌ Use: *preferencias [opcao] [valor]*"
        
        opcao = args[0].lower()
        valor_str = args[1].lower()
        
        mapa = {
            'cadastro': 'cadastro_automatico',
            'sugestoes': 'sugestoes_automaticas',
            'detalhado': 'respostas_detalhadas'
        }
        
        if opcao in mapa:
            valor = valor_str in ['on', 'sim', 'yes', 'ativar', '1', 'true']
            self.set_config(user_id, 'ia', mapa[opcao], valor)
            status = "ativado ✅" if valor else "desativado ❌"
            return f"✅ *{opcao.capitalize()}* {status}"
        
        return "❌ Opções: cadastro, sugestoes, detalhado"
    
    def _toggle_resumo_diario(self, user_id: str, args: List[str]) -> str:
        """Toggle rápido do resumo diário"""
        valor = args[0].lower() in ['on', 'sim', 'yes', 'ativar', '1', 'true']
        self.set_config(user_id, 'notificacoes', 'resumo_diario_ativo', valor)
        status = "ativado ✅" if valor else "desativado ❌"
        return f"📊 Resumo diário {status}"
    
    def _toggle_compartilhar_agenda(self, user_id: str, args: List[str]) -> str:
        """Toggle rápido do compartilhamento de agenda"""
        valor = args[0].lower() in ['on', 'sim', 'yes', 'ativar', '1', 'true']
        self.set_config(user_id, 'privacidade', 'compartilhar_agenda_grupos', valor)
        status = "permitido 🔓" if valor else "bloqueado 🔒"
        return f"📅 Compartilhamento de agenda em grupos: {status}"


# Singleton
_configuracoes: Optional[ConfiguracoesModule] = None

def get_configuracoes(data_dir: str = "data") -> ConfiguracoesModule:
    """Retorna instância singleton"""
    global _configuracoes
    if _configuracoes is None:
        _configuracoes = ConfiguracoesModule(data_dir)
    return _configuracoes
