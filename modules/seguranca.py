"""
🔐 Módulo de Segurança
Gerencia autenticação, PIN e lista de números autorizados
"""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Usuario:
    """Representa um usuário autorizado"""
    user_id: str
    nome: str = ""
    telefone: str = ""
    pin_hash: str = ""  # Hash do PIN
    autorizado: bool = False
    nivel: str = "usuario"  # admin, usuario, convidado
    criado_em: str = ""
    ultimo_acesso: str = ""
    tentativas_falhas: int = 0
    bloqueado_ate: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Sessao:
    """Representa uma sessão ativa"""
    user_id: str
    token: str
    criado_em: str
    expira_em: str
    plataforma: str = ""  # telegram, whatsapp
    
    def to_dict(self):
        return asdict(self)


class SegurancaModule:
    """Gerenciador de Segurança"""
    
    # Configurações
    MAX_TENTATIVAS = 5
    TEMPO_BLOQUEIO_MINUTOS = 30
    TEMPO_SESSAO_HORAS = 24
    PIN_MIN_LENGTH = 4
    PIN_MAX_LENGTH = 8
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.usuarios_file = os.path.join(data_dir, "usuarios_autorizados.json")
        self.sessoes_file = os.path.join(data_dir, "sessoes.json")
        self.config_file = os.path.join(data_dir, "config_seguranca.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados"""
        # Usuários
        if os.path.exists(self.usuarios_file):
            with open(self.usuarios_file, 'r', encoding='utf-8') as f:
                self.usuarios = json.load(f)
        else:
            self.usuarios = {}
        
        # Sessões
        if os.path.exists(self.sessoes_file):
            with open(self.sessoes_file, 'r', encoding='utf-8') as f:
                self.sessoes = json.load(f)
        else:
            self.sessoes = {}
        
        # Configurações
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'seguranca_ativa': False,  # Começa desativada
                'requer_pin': False,
                'modo_lista_branca': False,  # Se True, só autorizados podem usar
                'numeros_autorizados': ['558197723921', '8197723921'],
                'admins': ['558197723921', '8197723921'],  # Seu número como admin
                'permitir_auto_registro': True
            }
            self._save_config()
    
    def _save_usuarios(self):
        """Salva usuários"""
        with open(self.usuarios_file, 'w', encoding='utf-8') as f:
            json.dump(self.usuarios, f, ensure_ascii=False, indent=2)
    
    def _save_sessoes(self):
        """Salva sessões"""
        with open(self.sessoes_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessoes, f, ensure_ascii=False, indent=2)
    
    def _save_config(self):
        """Salva configurações"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _hash_pin(self, pin: str) -> str:
        """Gera hash do PIN"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def _gerar_token(self) -> str:
        """Gera token de sessão"""
        return secrets.token_urlsafe(32)
    
    def _extrair_telefone(self, user_id: str) -> str:
        """Extrai número de telefone do user_id"""
        # WhatsApp: 5511999999999@s.whatsapp.net
        # Telegram: número direto
        if '@' in user_id:
            return user_id.split('@')[0]
        return user_id
    
    # ========== VERIFICAÇÕES ==========
    
    def is_seguranca_ativa(self) -> bool:
        """Verifica se a segurança está ativa"""
        return self.config.get('seguranca_ativa', False)
    
    def is_autorizado(self, user_id: str) -> bool:
        """Verifica se usuário está autorizado a usar o bot"""
        if not self.is_seguranca_ativa():
            return True
        
        # Modo lista branca
        if self.config.get('modo_lista_branca', False):
            telefone = self._extrair_telefone(user_id)
            return telefone in self.config.get('numeros_autorizados', [])
        
        # Verifica se está bloqueado
        if self._is_bloqueado(user_id):
            return False
        
        # Se não requer PIN, autoriza
        if not self.config.get('requer_pin', False):
            return True
        
        # Verifica sessão ativa
        return self._tem_sessao_valida(user_id)
    
    def is_admin(self, user_id: str) -> bool:
        """Verifica se usuário é admin"""
        telefone = self._extrair_telefone(user_id)
        return telefone in self.config.get('admins', [])
    
    def _is_bloqueado(self, user_id: str) -> bool:
        """Verifica se usuário está bloqueado"""
        if user_id not in self.usuarios:
            return False
        
        usuario = self.usuarios[user_id]
        bloqueado_ate = usuario.get('bloqueado_ate', '')
        
        if bloqueado_ate:
            try:
                if datetime.fromisoformat(bloqueado_ate) > datetime.now():
                    return True
            except:
                pass
        
        return False
    
    def _tem_sessao_valida(self, user_id: str) -> bool:
        """Verifica se usuário tem sessão válida"""
        if user_id not in self.sessoes:
            return False
        
        sessao = self.sessoes[user_id]
        try:
            expira = datetime.fromisoformat(sessao.get('expira_em', ''))
            return expira > datetime.now()
        except:
            return False
    
    # ========== AUTENTICAÇÃO ==========
    
    def registrar_usuario(self, user_id: str, nome: str = "", telefone: str = "") -> Dict:
        """Registra novo usuário"""
        if not telefone:
            telefone = self._extrair_telefone(user_id)
        
        usuario = Usuario(
            user_id=user_id,
            nome=nome,
            telefone=telefone,
            autorizado=not self.config.get('modo_lista_branca', False),
            criado_em=datetime.now().isoformat()
        )
        
        self.usuarios[user_id] = usuario.to_dict()
        self._save_usuarios()
        
        return usuario.to_dict()
    
    def definir_pin(self, user_id: str, pin: str) -> tuple:
        """Define PIN do usuário"""
        # Valida PIN
        if not pin.isdigit():
            return False, "❌ O PIN deve conter apenas números."
        
        if len(pin) < self.PIN_MIN_LENGTH or len(pin) > self.PIN_MAX_LENGTH:
            return False, f"❌ O PIN deve ter entre {self.PIN_MIN_LENGTH} e {self.PIN_MAX_LENGTH} dígitos."
        
        # Registra se não existe
        if user_id not in self.usuarios:
            self.registrar_usuario(user_id)
        
        # Define PIN
        self.usuarios[user_id]['pin_hash'] = self._hash_pin(pin)
        self._save_usuarios()
        
        return True, "✅ PIN definido com sucesso!"
    
    def verificar_pin(self, user_id: str, pin: str) -> tuple:
        """Verifica PIN e cria sessão"""
        if user_id not in self.usuarios:
            return False, "❌ Usuário não registrado. Use `/pin definir [PIN]`"
        
        usuario = self.usuarios[user_id]
        
        # Verifica bloqueio
        if self._is_bloqueado(user_id):
            bloqueado_ate = datetime.fromisoformat(usuario['bloqueado_ate'])
            minutos = int((bloqueado_ate - datetime.now()).total_seconds() / 60)
            return False, f"🔒 Usuário bloqueado. Tente novamente em {minutos} minutos."
        
        # Verifica se tem PIN
        if not usuario.get('pin_hash'):
            return False, "❌ PIN não definido. Use `/pin definir [PIN]`"
        
        # Verifica PIN
        if self._hash_pin(pin) != usuario['pin_hash']:
            # Incrementa tentativas falhas
            usuario['tentativas_falhas'] = usuario.get('tentativas_falhas', 0) + 1
            
            if usuario['tentativas_falhas'] >= self.MAX_TENTATIVAS:
                # Bloqueia
                usuario['bloqueado_ate'] = (
                    datetime.now() + timedelta(minutes=self.TEMPO_BLOQUEIO_MINUTOS)
                ).isoformat()
                self._save_usuarios()
                return False, f"🔒 Muitas tentativas incorretas. Bloqueado por {self.TEMPO_BLOQUEIO_MINUTOS} minutos."
            
            restantes = self.MAX_TENTATIVAS - usuario['tentativas_falhas']
            self._save_usuarios()
            return False, f"❌ PIN incorreto. {restantes} tentativa(s) restante(s)."
        
        # PIN correto - cria sessão
        usuario['tentativas_falhas'] = 0
        usuario['ultimo_acesso'] = datetime.now().isoformat()
        self._save_usuarios()
        
        # Cria sessão
        token = self._gerar_token()
        sessao = Sessao(
            user_id=user_id,
            token=token,
            criado_em=datetime.now().isoformat(),
            expira_em=(datetime.now() + timedelta(hours=self.TEMPO_SESSAO_HORAS)).isoformat()
        )
        
        self.sessoes[user_id] = sessao.to_dict()
        self._save_sessoes()
        
        return True, "✅ PIN verificado! Acesso liberado."
    
    def encerrar_sessao(self, user_id: str) -> str:
        """Encerra sessão do usuário"""
        if user_id in self.sessoes:
            del self.sessoes[user_id]
            self._save_sessoes()
            return "👋 Sessão encerrada. Use `/pin` para acessar novamente."
        return "ℹ️ Nenhuma sessão ativa."
    
    # ========== ADMINISTRAÇÃO ==========
    
    def adicionar_autorizado(self, telefone: str, admin_id: str) -> str:
        """Adiciona número à lista de autorizados (admin only)"""
        if not self.is_admin(admin_id):
            return "❌ Apenas administradores podem fazer isso."
        
        # Limpa telefone
        telefone = ''.join(filter(str.isdigit, telefone))
        
        if telefone not in self.config['numeros_autorizados']:
            self.config['numeros_autorizados'].append(telefone)
            self._save_config()
            return f"✅ Número {telefone} autorizado!"
        
        return f"ℹ️ Número {telefone} já está autorizado."
    
    def remover_autorizado(self, telefone: str, admin_id: str) -> str:
        """Remove número da lista de autorizados"""
        if not self.is_admin(admin_id):
            return "❌ Apenas administradores podem fazer isso."
        
        telefone = ''.join(filter(str.isdigit, telefone))
        
        if telefone in self.config['numeros_autorizados']:
            self.config['numeros_autorizados'].remove(telefone)
            self._save_config()
            return f"✅ Número {telefone} removido."
        
        return f"ℹ️ Número {telefone} não estava na lista."
    
    def adicionar_admin(self, telefone: str, admin_id: str) -> str:
        """Adiciona admin"""
        if not self.is_admin(admin_id) and self.config.get('admins'):
            return "❌ Apenas administradores podem fazer isso."
        
        telefone = ''.join(filter(str.isdigit, telefone))
        
        if telefone not in self.config['admins']:
            self.config['admins'].append(telefone)
            self._save_config()
            return f"✅ {telefone} agora é administrador!"
        
        return f"ℹ️ {telefone} já é administrador."
    
    def ativar_seguranca(self, admin_id: str) -> str:
        """Ativa sistema de segurança"""
        if not self.is_admin(admin_id) and self.config.get('admins'):
            return "❌ Apenas administradores podem fazer isso."
        
        self.config['seguranca_ativa'] = True
        self._save_config()
        
        return """
🔐 *Segurança Ativada!*

O bot agora requer autenticação.

*Configure as opções:*
• `/seguranca pin on/off` - Exigir PIN
• `/seguranca whitelist on/off` - Modo lista branca
• `/seguranca add [número]` - Autorizar número
• `/seguranca admin [número]` - Adicionar admin
"""
    
    def desativar_seguranca(self, admin_id: str) -> str:
        """Desativa sistema de segurança"""
        if not self.is_admin(admin_id):
            return "❌ Apenas administradores podem fazer isso."
        
        self.config['seguranca_ativa'] = False
        self._save_config()
        
        return "🔓 Segurança desativada. Todos podem usar o bot."
    
    # ========== COMANDOS ==========
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de segurança"""
        
        if command == 'pin':
            if not args:
                return self._ajuda_pin()
            
            if args[0] == 'definir' and len(args) > 1:
                sucesso, msg = self.definir_pin(user_id, args[1])
                return msg
            
            # Assume que é verificação de PIN
            sucesso, msg = self.verificar_pin(user_id, args[0])
            return msg
        
        elif command == 'logout':
            return self.encerrar_sessao(user_id)
        
        elif command == 'seguranca':
            return self._handle_seguranca(args, user_id)
        
        return self._ajuda_seguranca()
    
    def _handle_seguranca(self, args: List[str], user_id: str) -> str:
        """Processa subcomandos de segurança"""
        if not args:
            return self._status_seguranca(user_id)
        
        subcommand = args[0].lower()
        
        if subcommand in ['on', 'ativar']:
            return self.ativar_seguranca(user_id)
        
        elif subcommand in ['off', 'desativar']:
            return self.desativar_seguranca(user_id)
        
        elif subcommand == 'pin':
            if len(args) > 1:
                if args[1] in ['on', 'ativar']:
                    if not self.is_admin(user_id):
                        return "❌ Apenas administradores."
                    self.config['requer_pin'] = True
                    self._save_config()
                    return "✅ PIN obrigatório ativado!"
                elif args[1] in ['off', 'desativar']:
                    if not self.is_admin(user_id):
                        return "❌ Apenas administradores."
                    self.config['requer_pin'] = False
                    self._save_config()
                    return "✅ PIN obrigatório desativado."
            return "Use: `/seguranca pin on/off`"
        
        elif subcommand == 'whitelist':
            if len(args) > 1:
                if args[1] in ['on', 'ativar']:
                    if not self.is_admin(user_id):
                        return "❌ Apenas administradores."
                    self.config['modo_lista_branca'] = True
                    self._save_config()
                    return "✅ Modo lista branca ativado! Apenas números autorizados podem usar."
                elif args[1] in ['off', 'desativar']:
                    if not self.is_admin(user_id):
                        return "❌ Apenas administradores."
                    self.config['modo_lista_branca'] = False
                    self._save_config()
                    return "✅ Modo lista branca desativado."
            return "Use: `/seguranca whitelist on/off`"
        
        elif subcommand in ['add', 'adicionar']:
            if len(args) > 1:
                return self.adicionar_autorizado(args[1], user_id)
            return "Use: `/seguranca add [número]`"
        
        elif subcommand in ['remove', 'remover']:
            if len(args) > 1:
                return self.remover_autorizado(args[1], user_id)
            return "Use: `/seguranca remove [número]`"
        
        elif subcommand == 'admin':
            if len(args) > 1:
                return self.adicionar_admin(args[1], user_id)
            return "Use: `/seguranca admin [número]`"
        
        elif subcommand == 'lista':
            return self._listar_autorizados(user_id)
        
        return self._ajuda_seguranca()
    
    def _status_seguranca(self, user_id: str) -> str:
        """Mostra status da segurança"""
        ativa = "🟢 Ativa" if self.is_seguranca_ativa() else "🔴 Inativa"
        pin = "🟢 Sim" if self.config.get('requer_pin') else "🔴 Não"
        whitelist = "🟢 Sim" if self.config.get('modo_lista_branca') else "🔴 Não"
        
        num_autorizados = len(self.config.get('numeros_autorizados', []))
        num_admins = len(self.config.get('admins', []))
        
        is_admin = "👑 Sim" if self.is_admin(user_id) else "❌ Não"
        
        return f"""
🔐 *Status de Segurança*

*Sistema:* {ativa}
*Requer PIN:* {pin}
*Modo Lista Branca:* {whitelist}

📊 *Estatísticas:*
• Números autorizados: {num_autorizados}
• Administradores: {num_admins}

👤 *Você:*
• Admin: {is_admin}

*Comandos:*
`/seguranca on/off` - Ativar/desativar
`/seguranca pin on/off` - Exigir PIN
`/seguranca whitelist on/off` - Lista branca
`/seguranca add [num]` - Autorizar
`/seguranca lista` - Ver autorizados
"""
    
    def _listar_autorizados(self, user_id: str) -> str:
        """Lista números autorizados"""
        if not self.is_admin(user_id):
            return "❌ Apenas administradores podem ver a lista."
        
        autorizados = self.config.get('numeros_autorizados', [])
        admins = self.config.get('admins', [])
        
        resposta = "🔐 *Números Autorizados*\n\n"
        
        if admins:
            resposta += "*👑 Administradores:*\n"
            for num in admins:
                resposta += f"  • {num}\n"
        
        if autorizados:
            resposta += "\n*✅ Autorizados:*\n"
            for num in autorizados:
                emoji = "👑" if num in admins else "👤"
                resposta += f"  {emoji} {num}\n"
        else:
            resposta += "\n_Nenhum número na lista branca._"
        
        return resposta
    
    def _ajuda_pin(self) -> str:
        """Ajuda sobre PIN"""
        return """
🔐 *Sistema de PIN*

*Comandos:*
• `/pin definir [PIN]` - Define seu PIN
• `/pin [PIN]` - Verifica PIN e acessa
• `/logout` - Encerra sessão

*Regras do PIN:*
• Apenas números
• Entre 4 e 8 dígitos
• Após 5 tentativas erradas, bloqueio de 30min

*Exemplo:*
`/pin definir 1234`
`/pin 1234`
"""
    
    def _ajuda_seguranca(self) -> str:
        """Ajuda sobre segurança"""
        return """
🔐 *Sistema de Segurança*

*Comandos de Usuário:*
• `/pin definir [PIN]` - Define PIN
• `/pin [PIN]` - Verifica e acessa
• `/logout` - Encerra sessão

*Comandos de Admin:*
• `/seguranca on/off` - Ativar/desativar
• `/seguranca pin on/off` - Exigir PIN
• `/seguranca whitelist on/off` - Modo lista branca
• `/seguranca add [número]` - Autorizar número
• `/seguranca remove [número]` - Remover número
• `/seguranca admin [número]` - Adicionar admin
• `/seguranca lista` - Ver autorizados

*Modos:*
• *PIN:* Usuários precisam de PIN para acessar
• *Lista Branca:* Apenas números cadastrados podem usar
"""
    
    # ========== MIDDLEWARE ==========
    
    def verificar_acesso(self, user_id: str, comando: str = "") -> tuple:
        """
        Middleware para verificar acesso antes de processar comandos
        Retorna: (autorizado: bool, mensagem: str ou None)
        """
        # Comandos sempre permitidos
        comandos_livres = ['pin', 'start', 'ajuda', 'help']
        if comando in comandos_livres:
            return True, None
        
        # Se segurança inativa, permite tudo
        if not self.is_seguranca_ativa():
            return True, None
        
        # Verifica bloqueio
        if self._is_bloqueado(user_id):
            usuario = self.usuarios.get(user_id, {})
            bloqueado_ate = usuario.get('bloqueado_ate', '')
            try:
                dt = datetime.fromisoformat(bloqueado_ate)
                minutos = int((dt - datetime.now()).total_seconds() / 60)
                return False, f"🔒 Acesso bloqueado. Tente em {minutos} minutos."
            except:
                pass
            return False, "🔒 Acesso bloqueado temporariamente."
        
        # Modo lista branca
        if self.config.get('modo_lista_branca'):
            telefone = self._extrair_telefone(user_id)
            if telefone not in self.config.get('numeros_autorizados', []):
                return False, """
🔒 *Acesso Restrito*

Este bot está em modo privado.
Entre em contato com o administrador para solicitar acesso.
"""
        
        # Verifica PIN
        if self.config.get('requer_pin'):
            if not self._tem_sessao_valida(user_id):
                return False, """
🔐 *Autenticação Necessária*

Use `/pin [seu-pin]` para acessar.

Se não tem PIN, use `/pin definir [PIN]` primeiro.
"""
        
        return True, None


# Singleton
_seguranca_instance = None

def get_seguranca(data_dir: str = "data") -> SegurancaModule:
    """Retorna instância singleton do módulo de segurança"""
    global _seguranca_instance
    if _seguranca_instance is None:
        _seguranca_instance = SegurancaModule(data_dir)
    return _seguranca_instance
