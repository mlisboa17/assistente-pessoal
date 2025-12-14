"""
👤 Módulo de Perfil do Usuário
Gerencia preferências, onboarding e configurações pessoais
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field


@dataclass
class PerfilUsuario:
    user_id: str
    nome: str = ""
    telefone: str = ""
    email: str = ""
    fuso_horario: str = "America/Recife"
    idioma: str = "pt-BR"
    
    # Status de conexões
    google_conectado: bool = False
    google_email: str = ""
    
    # Preferências de notificação
    notificacoes_ativas: bool = True
    horario_resumo_diario: str = "08:00"
    silenciado_ate: str = ""
    
    # Onboarding
    primeiro_acesso: str = ""
    onboarding_completo: bool = False
    tutorial_visto: bool = False
    
    # Estatísticas
    total_mensagens: int = 0
    ultimo_acesso: str = ""
    
    # 🗣️ Personalização de Linguagem (aprende com o usuário)
    nivel_formalidade: str = "neutro"  # informal, neutro, formal
    palavras_frequentes: Dict[str, int] = field(default_factory=dict)
    emojis_usados: Dict[str, int] = field(default_factory=dict)
    saudacoes_preferidas: List[str] = field(default_factory=list)
    confirmacoes_preferidas: List[str] = field(default_factory=list)
    negacoes_preferidas: List[str] = field(default_factory=list)
    usa_maiusculas: bool = False
    usa_pontuacao: bool = True
    
    # Configurações
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)


class PerfilModule:
    """Gerenciador de perfis de usuários"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.perfis_file = os.path.join(data_dir, "perfis.json")
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.perfis_file):
            with open(self.perfis_file, 'r', encoding='utf-8') as f:
                self.perfis = json.load(f)
        else:
            self.perfis = {}
    
    def _save_data(self):
        with open(self.perfis_file, 'w', encoding='utf-8') as f:
            json.dump(self.perfis, f, ensure_ascii=False, indent=2)
    
    def get_perfil(self, user_id: str) -> Dict[str, Any]:
        """Obtém perfil do usuário, cria se não existir"""
        if user_id not in self.perfis:
            self.perfis[user_id] = PerfilUsuario(
                user_id=user_id,
                primeiro_acesso=datetime.now().isoformat(),
                ultimo_acesso=datetime.now().isoformat()
            ).to_dict()
            self._save_data()
        return self.perfis[user_id]
    
    def atualizar_perfil(self, user_id: str, **kwargs) -> bool:
        """Atualiza campos do perfil"""
        perfil = self.get_perfil(user_id)
        for key, value in kwargs.items():
            if key in perfil:
                perfil[key] = value
        perfil['ultimo_acesso'] = datetime.now().isoformat()
        self._save_data()
        return True
    
    def registrar_acesso(self, user_id: str):
        """Registra acesso do usuário"""
        perfil = self.get_perfil(user_id)
        perfil['total_mensagens'] = perfil.get('total_mensagens', 0) + 1
        perfil['ultimo_acesso'] = datetime.now().isoformat()
        self._save_data()
    
    def is_novo_usuario(self, user_id: str) -> bool:
        """Verifica se é primeiro acesso"""
        return user_id not in self.perfis
    
    def completar_onboarding(self, user_id: str):
        """Marca onboarding como completo"""
        self.atualizar_perfil(user_id, onboarding_completo=True)
    
    def set_google_conectado(self, user_id: str, email: str = ""):
        """Marca Google como conectado"""
        self.atualizar_perfil(user_id, google_conectado=True, google_email=email)
    
    def set_google_desconectado(self, user_id: str):
        """Marca Google como desconectado"""
        self.atualizar_perfil(user_id, google_conectado=False, google_email="")
    
    def get_mensagem_boas_vindas(self, user_id: str, nome_contato: str = "") -> str:
        """Gera mensagem de boas-vindas para novo usuário"""
        perfil = self.get_perfil(user_id)
        
        if nome_contato:
            self.atualizar_perfil(user_id, nome=nome_contato)
        
        nome = nome_contato or "!"
        
        return f"""👋 *Olá{', ' + nome if nome != '!' else ''}! Bem-vindo ao seu Assistente Pessoal!*

Sou um assistente inteligente que pode te ajudar com:

📅 *Agenda* - Compromissos e lembretes
📧 *E-mails* - Ler e buscar e-mails
💰 *Finanças* - Controle de gastos e metas
✅ *Tarefas* - Lista de afazeres
🎯 *Metas* - Objetivos financeiros

━━━━━━━━━━━━━━━━━━━━━

🔐 *Para começar, conecte sua conta Google:*
➡️ Digite *login*

Isso me permite acessar seu Calendar e Gmail.

━━━━━━━━━━━━━━━━━━━━━

💡 *Dica:* Você pode conversar naturalmente!
Exemplos:
• "gastos" - ver resumo financeiro
• "tarefas" - ver suas tarefas
• "me lembra de ligar às 15h"
• "gastei 50 no mercado"

Digite *ajuda* para ver todos os comandos."""
    
    def get_status_completo(self, user_id: str, google_auth=None, financas=None, tarefas=None, metas=None) -> str:
        """Gera status completo do usuário"""
        perfil = self.get_perfil(user_id)
        
        # Status Google
        google_status = "❌ Não conectado"
        calendar_status = "❌ Não disponível"
        gmail_status = "❌ Não disponível"
        
        if google_auth and google_auth.is_authenticated(user_id):
            email = perfil.get('google_email', 'conectado')
            google_status = f"✅ Conectado ({email})"
            calendar_status = "✅ Sincronizado"
            gmail_status = "✅ Ativo"
        
        # Estatísticas de finanças
        gastos_mes = "0"
        if financas:
            try:
                resumo = financas.get_resumo_mensal(user_id)
                if resumo:
                    gastos_mes = f"R$ {resumo.get('total_despesas', 0):.2f}"
            except:
                pass
        
        # Estatísticas de tarefas
        tarefas_pendentes = "0"
        if tarefas:
            try:
                lista = tarefas.get_tarefas_pendentes(user_id)
                tarefas_pendentes = str(len(lista))
            except:
                pass
        
        # Estatísticas de metas
        metas_ativas = "0"
        if metas:
            try:
                lista = metas.listar_metas(user_id)
                metas_ativas = str(len([m for m in lista if m.get('status') == 'ativa']))
            except:
                pass
        
        # Notificações
        notif_status = "🔔 Ligadas" if perfil.get('notificacoes_ativas', True) else "🔕 Desligadas"
        if perfil.get('silenciado_ate'):
            notif_status = f"🔕 Silenciado até {perfil['silenciado_ate'][:16]}"
        
        # Info do perfil
        nome = perfil.get('nome', 'Não definido')
        primeiro_acesso = perfil.get('primeiro_acesso', '')[:10]
        total_msgs = perfil.get('total_mensagens', 0)
        
        return f"""📊 *Seu Status*

👤 *Perfil:*
• Nome: {nome}
• Membro desde: {primeiro_acesso}
• Mensagens: {total_msgs}

━━━━━━━━━━━━━━━━━━━━━

🔐 *Conexões:*
• Google: {google_status}
• Calendar: {calendar_status}
• Gmail: {gmail_status}

━━━━━━━━━━━━━━━━━━━━━

📈 *Resumo:*
• 💰 Gastos do mês: {gastos_mes}
• ✅ Tarefas pendentes: {tarefas_pendentes}
• 🎯 Metas ativas: {metas_ativas}

━━━━━━━━━━━━━━━━━━━━━

⚙️ *Configurações:*
• Notificações: {notif_status}
• Resumo diário: {perfil.get('horario_resumo_diario', '08:00')}
• Fuso horário: {perfil.get('fuso_horario', 'America/Recife')}

━━━━━━━━━━━━━━━━━━━━━

💡 Digite *config* para alterar configurações."""
    
    def get_menu_config(self, user_id: str) -> str:
        """Gera menu de configurações"""
        perfil = self.get_perfil(user_id)
        
        notif = "🔔 Ligadas" if perfil.get('notificacoes_ativas', True) else "🔕 Desligadas"
        
        return f"""⚙️ *Configurações*

Escolha o que deseja alterar:

1️⃣ Nome: {perfil.get('nome', 'Não definido')}
2️⃣ Notificações: {notif}
3️⃣ Resumo diário: {perfil.get('horario_resumo_diario', '08:00')}
4️⃣ Fuso horário: {perfil.get('fuso_horario', 'America/Recife')}
5️⃣ Desconectar Google
6️⃣ Exportar meus dados
7️⃣ Apagar meus dados

━━━━━━━━━━━━━━━━━━━━━

Responda com o número da opção.
Ex: *1* para alterar nome"""
    
    async def handle(self, command: str, args: List[str], user_id: str, **kwargs) -> str:
        """Processa comandos do módulo de perfil"""
        
        if command == 'status':
            return self.get_status_completo(
                user_id,
                google_auth=kwargs.get('google_auth'),
                financas=kwargs.get('financas'),
                tarefas=kwargs.get('tarefas'),
                metas=kwargs.get('metas')
            )
        
        if command == 'config':
            return self.get_menu_config(user_id)
        
        if command == 'config_nome':
            if args:
                nome = ' '.join(args)
                self.atualizar_perfil(user_id, nome=nome)
                return f"✅ Nome atualizado para: {nome}"
            return "Use: config nome [seu nome]"
        
        if command == 'config_notificacoes':
            perfil = self.get_perfil(user_id)
            novo_estado = not perfil.get('notificacoes_ativas', True)
            self.atualizar_perfil(user_id, notificacoes_ativas=novo_estado)
            estado = "ligadas" if novo_estado else "desligadas"
            return f"✅ Notificações {estado}!"
        
        if command == 'config_resumo':
            if args:
                horario = args[0]
                if ':' in horario:
                    self.atualizar_perfil(user_id, horario_resumo_diario=horario)
                    return f"✅ Resumo diário será enviado às {horario}"
            return "Use: config resumo [HH:MM]\nEx: config resumo 08:00"
        
        if command == 'config_fuso':
            if args:
                fuso = args[0]
                self.atualizar_perfil(user_id, fuso_horario=fuso)
                return f"✅ Fuso horário alterado para: {fuso}"
            return """Fusos disponíveis:
• America/Recife
• America/Sao_Paulo
• America/Manaus
• America/Belem

Use: config fuso [fuso]"""
        
        if command == 'exportar':
            return self._exportar_dados(user_id)
        
        if command == 'apagar_dados':
            return self._confirmar_apagar(user_id)
        
        return self.get_menu_config(user_id)
    
    def _exportar_dados(self, user_id: str) -> str:
        """Exporta dados do usuário"""
        perfil = self.get_perfil(user_id)
        
        # Coleta dados de todos os módulos
        dados = {
            "perfil": perfil,
            "exportado_em": datetime.now().isoformat()
        }
        
        # Salva arquivo de export
        export_file = os.path.join(self.data_dir, f"export_{user_id}.json")
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return f"""📦 *Dados Exportados!*

Seus dados foram salvos em:
`export_{user_id}.json`

O arquivo contém:
• Perfil e configurações
• Histórico de uso

Para receber o arquivo, use o comando:
*baixar export*"""
    
    def _confirmar_apagar(self, user_id: str) -> str:
        """Solicita confirmação para apagar dados"""
        return """⚠️ *Atenção!*

Você está prestes a apagar TODOS os seus dados:
• Perfil e configurações
• Histórico de finanças
• Tarefas e lembretes
• Conexão Google

Esta ação é *IRREVERSÍVEL*!

Para confirmar, digite:
*APAGAR TUDO*

Para cancelar, digite qualquer outra coisa."""
    
    def apagar_dados_usuario(self, user_id: str) -> bool:
        """Apaga todos os dados do usuário"""
        if user_id in self.perfis:
            del self.perfis[user_id]
            self._save_data()
        
        # Remove token Google
        token_file = os.path.join(self.data_dir, "google_tokens", f"token_{user_id}.pickle")
        if os.path.exists(token_file):
            os.remove(token_file)
        
        # Remove export se existir
        export_file = os.path.join(self.data_dir, f"export_{user_id}.json")
        if os.path.exists(export_file):
            os.remove(export_file)
        
        return True


    # ========================================
    # 🗣️ MÉTODOS DE PERSONALIZAÇÃO DE LINGUAGEM
    # ========================================
    
    def aprender_linguagem(self, user_id: str, mensagem: str):
        """Aprende com o jeito de falar do usuário"""
        import re
        perfil = self.get_perfil(user_id)
        mensagem_lower = mensagem.lower()
        
        # Analisa formalidade
        palavras_informais = ['blz', 'vlw', 'pô', 'cara', 'mano', 'brother', 'tipo', 'né', 'tá', 'ta']
        palavras_formais = ['senhor', 'senhora', 'por favor', 'poderia', 'gostaria', 'agradeço']
        
        pontos_informal = sum(1 for p in palavras_informais if p in mensagem_lower)
        pontos_formal = sum(1 for p in palavras_formais if p in mensagem_lower)
        
        if pontos_informal > pontos_formal * 2:
            perfil['nivel_formalidade'] = 'informal'
        elif pontos_formal > pontos_informal * 2:
            perfil['nivel_formalidade'] = 'formal'
        else:
            perfil['nivel_formalidade'] = 'neutro'
        
        # Detecta emojis
        emojis = re.findall(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]', mensagem)
        if not isinstance(perfil.get('emojis_usados'), dict):
            perfil['emojis_usados'] = {}
        for emoji in emojis:
            perfil['emojis_usados'][emoji] = perfil['emojis_usados'].get(emoji, 0) + 1
        
        # Aprende saudações
        saudacoes = ['oi', 'olá', 'opa', 'e ai', 'fala', 'salve', 'bom dia', 'boa tarde']
        if not isinstance(perfil.get('saudacoes_preferidas'), list):
            perfil['saudacoes_preferidas'] = []
        for saudacao in saudacoes:
            if saudacao in mensagem_lower and saudacao not in perfil['saudacoes_preferidas']:
                perfil['saudacoes_preferidas'].append(saudacao)
                if len(perfil['saudacoes_preferidas']) > 3:
                    perfil['saudacoes_preferidas'].pop(0)
        
        # Aprende confirmações
        confirmacoes = ['ok', 'blz', 'beleza', 'show', 'massa', 'certo', 'sim', 'dale', 'ta', 'tá']
        if not isinstance(perfil.get('confirmacoes_preferidas'), list):
            perfil['confirmacoes_preferidas'] = []
        for conf in confirmacoes:
            if conf in mensagem_lower and conf not in perfil['confirmacoes_preferidas']:
                perfil['confirmacoes_preferidas'].append(conf)
                if len(perfil['confirmacoes_preferidas']) > 3:
                    perfil['confirmacoes_preferidas'].pop(0)
        
        # Detecta uso de maiúsculas e pontuação
        perfil['usa_maiusculas'] = any(c.isupper() for c in mensagem)
        perfil['usa_pontuacao'] = any(p in mensagem for p in ['.', '!', '?', ','])
        
        self._save_data()
    
    def adaptar_resposta(self, user_id: str, resposta: str) -> str:
        """Adapta resposta para o estilo do usuário"""
        perfil = self.get_perfil(user_id)
        nivel = perfil.get('nivel_formalidade', 'neutro')
        
        # Substitui confirmações genéricas por preferidas
        confirmacoes = perfil.get('confirmacoes_preferidas', [])
        if confirmacoes and any(palavra in resposta for palavra in ['Ok', 'Pronto', 'Feito']):
            palavra_preferida = confirmacoes[-1].capitalize()
            for palavra_original in ['Ok', 'Pronto', 'Feito', 'Concluído']:
                if palavra_original in resposta:
                    resposta = resposta.replace(palavra_original, palavra_preferida, 1)
                    break
        
        # Adapta saudações
        saudacoes = perfil.get('saudacoes_preferidas', [])
        if saudacoes:
            palavra_preferida = saudacoes[-1].capitalize()
            for saudacao_padrao in ['Olá', 'Oi', 'Bom dia', 'Boa tarde']:
                if resposta.startswith(saudacao_padrao):
                    resposta = resposta.replace(saudacao_padrao, palavra_preferida, 1)
                    break
        
        # Remove pontuação excessiva se usuário não usa
        if not perfil.get('usa_pontuacao', True):
            resposta = resposta.replace('!', '').replace('...', '')
        
        return resposta


# Instância global
_perfil_module = None

def get_perfil_module(data_dir: str = "data") -> PerfilModule:
    global _perfil_module
    if _perfil_module is None:
        _perfil_module = PerfilModule(data_dir)
    return _perfil_module
