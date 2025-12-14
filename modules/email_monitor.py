"""
📧 Módulo de Monitoramento de Emails
Monitora emails por palavras-chave e notifica via WhatsApp
"""
import json
import os
import re
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class PalavraChave:
    """Palavra-chave para monitoramento"""
    id: str
    palavra: str
    user_id: str
    ativo: bool = True
    criado_em: str = ""
    ultima_verificacao: str = ""
    emails_encontrados: int = 0


@dataclass 
class EmailEncontrado:
    """Email encontrado com palavra-chave"""
    id: str
    user_id: str
    palavra_chave: str
    remetente: str
    assunto: str
    trecho: str  # 3 linhas com a palavra
    data_email: str
    notificado: bool = False
    encontrado_em: str = ""


class EmailMonitorModule:
    """Monitora emails por palavras-chave e notifica usuários"""
    
    INTERVALO_VERIFICACAO = 24 * 60 * 60  # 24 horas em segundos
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "email_monitor_config.json")
        self.encontrados_file = os.path.join(data_dir, "emails_encontrados.json")
        
        self._palavras_chave: Dict[str, List[PalavraChave]] = {}  # user_id -> lista
        self._emails_encontrados: List[EmailEncontrado] = []
        self._notificacao_callback = None  # Callback para enviar notificação
        self._monitor_thread = None
        self._running = False
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega configurações e emails encontrados"""
        # Palavras-chave
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, palavras in data.items():
                        self._palavras_chave[user_id] = [
                            PalavraChave(**p) for p in palavras
                        ]
            except:
                self._palavras_chave = {}
        
        # Emails encontrados
        if os.path.exists(self.encontrados_file):
            try:
                with open(self.encontrados_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._emails_encontrados = [
                        EmailEncontrado(**e) for e in data
                    ]
            except:
                self._emails_encontrados = []
    
    def _save_data(self):
        """Salva configurações"""
        # Palavras-chave
        data = {}
        for user_id, palavras in self._palavras_chave.items():
            data[user_id] = [asdict(p) for p in palavras]
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Emails encontrados
        with open(self.encontrados_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(e) for e in self._emails_encontrados], f, ensure_ascii=False, indent=2)
    
    # ==================== GERENCIAMENTO DE PALAVRAS-CHAVE ====================
    
    def adicionar_palavra(self, user_id: str, palavra: str) -> PalavraChave:
        """Adiciona palavra-chave para monitoramento"""
        if user_id not in self._palavras_chave:
            self._palavras_chave[user_id] = []
        
        # Verifica se já existe
        palavra_lower = palavra.lower().strip()
        for p in self._palavras_chave[user_id]:
            if p.palavra.lower() == palavra_lower:
                p.ativo = True
                self._save_data()
                return p
        
        # Cria nova
        nova = PalavraChave(
            id=f"pk_{int(datetime.now().timestamp())}",
            palavra=palavra.strip(),
            user_id=user_id,
            ativo=True,
            criado_em=datetime.now().isoformat()
        )
        
        self._palavras_chave[user_id].append(nova)
        self._save_data()
        return nova
    
    def remover_palavra(self, user_id: str, palavra_ou_id: str) -> bool:
        """Remove ou desativa palavra-chave"""
        if user_id not in self._palavras_chave:
            return False
        
        palavra_lower = palavra_ou_id.lower().strip()
        for p in self._palavras_chave[user_id]:
            if p.id == palavra_ou_id or p.palavra.lower() == palavra_lower:
                p.ativo = False
                self._save_data()
                return True
        
        return False
    
    def listar_palavras(self, user_id: str, apenas_ativas: bool = True) -> List[PalavraChave]:
        """Lista palavras-chave do usuário"""
        if user_id not in self._palavras_chave:
            return []
        
        if apenas_ativas:
            return [p for p in self._palavras_chave[user_id] if p.ativo]
        return self._palavras_chave[user_id]
    
    # ==================== VERIFICAÇÃO DE EMAILS ====================
    
    async def verificar_emails_usuario(self, user_id: str, gmail_service) -> List[EmailEncontrado]:
        """Verifica emails de um usuário por palavras-chave"""
        palavras = self.listar_palavras(user_id)
        if not palavras:
            return []
        
        encontrados = []
        
        for palavra_config in palavras:
            try:
                # Busca emails com a palavra-chave em todas as pastas
                query = palavra_config.palavra
                
                # Busca nos últimos 7 dias para não sobrecarregar
                results = gmail_service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=10
                ).execute()
                
                messages = results.get('messages', [])
                
                for msg_info in messages:
                    msg_id = msg_info['id']
                    
                    # Verifica se já foi processado
                    if any(e.id == msg_id and e.palavra_chave == palavra_config.palavra 
                           for e in self._emails_encontrados):
                        continue
                    
                    # Busca detalhes do email
                    msg = gmail_service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()
                    
                    # Extrai informações
                    headers = msg.get('payload', {}).get('headers', [])
                    
                    remetente = ""
                    assunto = ""
                    data_email = ""
                    
                    for header in headers:
                        name = header.get('name', '').lower()
                        if name == 'from':
                            remetente = header.get('value', '')
                        elif name == 'subject':
                            assunto = header.get('value', '')
                        elif name == 'date':
                            data_email = header.get('value', '')
                    
                    # Extrai corpo e encontra trecho com a palavra
                    corpo = self._extrair_corpo_email(msg)
                    trecho = self._extrair_trecho_com_palavra(corpo, palavra_config.palavra)
                    
                    if trecho:
                        email_encontrado = EmailEncontrado(
                            id=msg_id,
                            user_id=user_id,
                            palavra_chave=palavra_config.palavra,
                            remetente=remetente,
                            assunto=assunto,
                            trecho=trecho,
                            data_email=data_email,
                            notificado=False,
                            encontrado_em=datetime.now().isoformat()
                        )
                        
                        encontrados.append(email_encontrado)
                        self._emails_encontrados.append(email_encontrado)
                
                # Atualiza última verificação
                palavra_config.ultima_verificacao = datetime.now().isoformat()
                palavra_config.emails_encontrados += len(encontrados)
                
            except Exception as e:
                print(f"Erro ao verificar emails para '{palavra_config.palavra}': {e}")
                continue
        
        self._save_data()
        return encontrados
    
    def _extrair_corpo_email(self, msg: dict) -> str:
        """Extrai o corpo do email"""
        import base64
        
        corpo = ""
        payload = msg.get('payload', {})
        
        # Tenta extrair do body
        if 'body' in payload and payload['body'].get('data'):
            corpo = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        # Tenta extrair das parts
        if not corpo and 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        corpo = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif part.get('mimeType') == 'text/html':
                    if part.get('body', {}).get('data'):
                        html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        # Remove tags HTML básicas
                        corpo = re.sub(r'<[^>]+>', ' ', html)
                        corpo = re.sub(r'\s+', ' ', corpo)
        
        return corpo
    
    def _extrair_trecho_com_palavra(self, texto: str, palavra: str, linhas_contexto: int = 3) -> str:
        """Extrai trecho do texto contendo a palavra-chave com contexto"""
        if not texto or not palavra:
            return ""
        
        # Divide em linhas
        linhas = texto.split('\n')
        linhas = [l.strip() for l in linhas if l.strip()]
        
        palavra_lower = palavra.lower()
        
        for i, linha in enumerate(linhas):
            if palavra_lower in linha.lower():
                # Pega linhas de contexto
                inicio = max(0, i - 1)
                fim = min(len(linhas), i + linhas_contexto)
                
                trecho_linhas = linhas[inicio:fim]
                trecho = '\n'.join(trecho_linhas)
                
                # Limita tamanho
                if len(trecho) > 500:
                    trecho = trecho[:500] + "..."
                
                return trecho
        
        # Se não encontrou em linhas, busca no texto corrido
        pos = texto.lower().find(palavra_lower)
        if pos != -1:
            inicio = max(0, pos - 100)
            fim = min(len(texto), pos + len(palavra) + 200)
            trecho = texto[inicio:fim]
            if inicio > 0:
                trecho = "..." + trecho
            if fim < len(texto):
                trecho = trecho + "..."
            return trecho
        
        return ""
    
    # ==================== NOTIFICAÇÕES ====================
    
    def get_emails_nao_notificados(self, user_id: str) -> List[EmailEncontrado]:
        """Retorna emails encontrados ainda não notificados"""
        return [e for e in self._emails_encontrados 
                if e.user_id == user_id and not e.notificado]
    
    def marcar_como_notificado(self, email_id: str):
        """Marca email como notificado"""
        for e in self._emails_encontrados:
            if e.id == email_id:
                e.notificado = True
                break
        self._save_data()
    
    def formatar_notificacao(self, email: EmailEncontrado) -> str:
        """Formata notificação de email encontrado"""
        # Limpa o remetente
        remetente = email.remetente
        if '<' in remetente:
            # Extrai nome se tiver formato "Nome <email@x.com>"
            match = re.match(r'^([^<]+)', remetente)
            if match:
                remetente = match.group(1).strip()
        
        return f"""📧 *Email Encontrado!*

🔑 *Palavra-chave:* {email.palavra_chave}

━━━━━━━━━━━━━━━━━━━━━

👤 *De:* {remetente}
📌 *Assunto:* {email.assunto}

━━━━━━━━━━━━━━━━━━━━━

📝 *Trecho:*
_{email.trecho}_

━━━━━━━━━━━━━━━━━━━━━

📅 Recebido: {email.data_email[:25] if email.data_email else 'N/A'}

💡 _Use *emails* para ver mais detalhes_"""
    
    # ==================== MONITOR AUTOMÁTICO ====================
    
    def set_notificacao_callback(self, callback):
        """Define callback para enviar notificações
        callback(user_id: str, mensagem: str)
        """
        self._notificacao_callback = callback
    
    def iniciar_monitor(self, get_gmail_service_func):
        """Inicia thread de monitoramento
        get_gmail_service_func(user_id) -> gmail_service ou None
        """
        if self._running:
            return
        
        self._running = True
        self._get_gmail_service = get_gmail_service_func
        
        self._monitor_thread = threading.Thread(
            target=self._loop_monitor,
            daemon=True
        )
        self._monitor_thread.start()
        print("📧 Monitor de emails iniciado (verificação a cada 24h)")
    
    def parar_monitor(self):
        """Para o monitor"""
        self._running = False
    
    def _loop_monitor(self):
        """Loop principal do monitor"""
        while self._running:
            try:
                self._executar_verificacao()
            except Exception as e:
                print(f"Erro no monitor de emails: {e}")
            
            # Aguarda 24 horas
            for _ in range(self.INTERVALO_VERIFICACAO):
                if not self._running:
                    break
                time.sleep(1)
    
    def _executar_verificacao(self):
        """Executa verificação para todos os usuários"""
        print(f"📧 Iniciando verificação de emails... {datetime.now()}")
        
        for user_id in self._palavras_chave.keys():
            palavras = self.listar_palavras(user_id)
            if not palavras:
                continue
            
            try:
                # Obtém serviço Gmail do usuário
                gmail_service = self._get_gmail_service(user_id)
                if not gmail_service:
                    continue
                
                # Executa verificação async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                encontrados = loop.run_until_complete(
                    self.verificar_emails_usuario(user_id, gmail_service)
                )
                loop.close()
                
                # Envia notificações
                if encontrados and self._notificacao_callback:
                    for email in encontrados:
                        mensagem = self.formatar_notificacao(email)
                        self._notificacao_callback(user_id, mensagem)
                        self.marcar_como_notificado(email.id)
                
                print(f"  ✓ {user_id}: {len(encontrados)} emails encontrados")
                
            except Exception as e:
                print(f"  ✗ Erro para {user_id}: {e}")
        
        print(f"📧 Verificação concluída. Próxima em 24h.")
    
    def verificar_agora(self, user_id: str, gmail_service) -> str:
        """Força verificação imediata para um usuário"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        encontrados = loop.run_until_complete(
            self.verificar_emails_usuario(user_id, gmail_service)
        )
        loop.close()
        
        if not encontrados:
            return "✅ Nenhum novo email encontrado com suas palavras-chave."
        
        resposta = f"📧 *{len(encontrados)} email(s) encontrado(s)!*\n\n"
        
        for email in encontrados[:5]:  # Máximo 5
            resposta += f"🔑 *{email.palavra_chave}*\n"
            resposta += f"👤 {email.remetente[:30]}...\n" if len(email.remetente) > 30 else f"👤 {email.remetente}\n"
            resposta += f"📌 {email.assunto[:40]}...\n\n" if len(email.assunto) > 40 else f"📌 {email.assunto}\n\n"
        
        if len(encontrados) > 5:
            resposta += f"_...e mais {len(encontrados) - 5} email(s)_"
        
        return resposta
    
    # ==================== COMANDOS ====================
    
    async def handle(self, command: str, args: List[str], user_id: str,
                     gmail_service=None, is_group: bool = False) -> str:
        """Processa comandos de monitoramento de email"""
        
        # BLOQUEIA EM GRUPOS
        if is_group:
            return "🔒 *Monitoramento de emails não disponível em grupos*\n\n_Por privacidade, essa função só funciona em conversas privadas._"
        
        if command in ['monitorar', 'monitor', 'alertar']:
            if not args:
                return self._menu_monitor(user_id)
            
            sub_cmd = args[0].lower()
            
            if sub_cmd in ['add', 'adicionar', '+']:
                if len(args) < 2:
                    return "❌ Use: *monitorar add [palavra ou frase]*"
                palavra = ' '.join(args[1:])
                return self._adicionar_palavra_cmd(user_id, palavra)
            
            elif sub_cmd in ['rem', 'remover', 'del', '-']:
                if len(args) < 2:
                    return "❌ Use: *monitorar remover [palavra]*"
                palavra = ' '.join(args[1:])
                return self._remover_palavra_cmd(user_id, palavra)
            
            elif sub_cmd in ['lista', 'listar', 'ver']:
                return self._listar_palavras_cmd(user_id)
            
            elif sub_cmd in ['verificar', 'check', 'agora']:
                if not gmail_service:
                    return "❌ Você precisa estar conectado ao Google.\n\nDigite *login* primeiro."
                return self.verificar_agora(user_id, gmail_service)
            
            else:
                # Assume que é uma palavra para adicionar
                palavra = ' '.join(args)
                return self._adicionar_palavra_cmd(user_id, palavra)
        
        elif command in ['palavras', 'keywords']:
            return self._listar_palavras_cmd(user_id)
        
        return self._menu_monitor(user_id)
    
    def _menu_monitor(self, user_id: str) -> str:
        """Menu de monitoramento de emails"""
        palavras = self.listar_palavras(user_id)
        
        if palavras:
            lista = "\n".join([f"  • {p.palavra}" for p in palavras[:10]])
            palavras_info = f"📋 *Suas palavras-chave:*\n{lista}"
        else:
            palavras_info = "📋 _Nenhuma palavra-chave cadastrada_"
        
        return f"""📧 *MONITOR DE EMAILS*

━━━━━━━━━━━━━━━━━━━━━

{palavras_info}

━━━━━━━━━━━━━━━━━━━━━

🔔 *Como funciona:*
Verifico seus emails a cada 24h procurando 
as palavras-chave que você definir.

Quando encontrar, envio uma notificação aqui 
com o remetente e um trecho do email!

━━━━━━━━━━━━━━━━━━━━━

*Comandos:*

📌 *monitorar add [palavra]*
   → Adiciona palavra-chave
   Ex: monitorar add fatura vencida

📌 *monitorar remover [palavra]*
   → Remove monitoramento

📌 *monitorar verificar*
   → Verifica emails agora

📌 *monitorar listar*
   → Ver palavras cadastradas

━━━━━━━━━━━━━━━━━━━━━

💡 _Dica: Use frases específicas como "cobrança", "vencimento", "reunião amanhã"_"""
    
    def _adicionar_palavra_cmd(self, user_id: str, palavra: str) -> str:
        """Comando para adicionar palavra"""
        if len(palavra) < 3:
            return "❌ A palavra deve ter pelo menos 3 caracteres."
        
        if len(palavra) > 100:
            return "❌ A palavra deve ter no máximo 100 caracteres."
        
        palavras_existentes = self.listar_palavras(user_id)
        if len(palavras_existentes) >= 20:
            return "❌ Limite de 20 palavras-chave atingido.\n\nRemova alguma antes de adicionar nova."
        
        nova = self.adicionar_palavra(user_id, palavra)
        
        return f"""✅ *Palavra-chave adicionada!*

🔑 *{nova.palavra}*

━━━━━━━━━━━━━━━━━━━━━

Vou verificar seus emails a cada 24h 
procurando por essa palavra.

Quando encontrar, te notifico aqui! 📱

━━━━━━━━━━━━━━━━━━━━━

💡 _Use *monitorar verificar* para buscar agora_"""
    
    def _remover_palavra_cmd(self, user_id: str, palavra: str) -> str:
        """Comando para remover palavra"""
        if self.remover_palavra(user_id, palavra):
            return f"✅ Palavra-chave *{palavra}* removida do monitoramento."
        return f"❌ Palavra-chave *{palavra}* não encontrada."
    
    def _listar_palavras_cmd(self, user_id: str) -> str:
        """Comando para listar palavras"""
        palavras = self.listar_palavras(user_id)
        
        if not palavras:
            return """📋 *Nenhuma palavra-chave cadastrada*

Use *monitorar add [palavra]* para começar!

💡 _Exemplos: "fatura", "cobrança", "reunião"_"""
        
        texto = "📋 *Suas Palavras-Chave*\n\n"
        
        for i, p in enumerate(palavras, 1):
            status = "🟢" if p.ativo else "🔴"
            encontrados = f" ({p.emails_encontrados} encontrados)" if p.emails_encontrados else ""
            texto += f"{status} {i}. *{p.palavra}*{encontrados}\n"
        
        texto += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        texto += f"Total: {len(palavras)} palavra(s)\n"
        texto += f"\n💡 _monitorar remover [palavra]_ para remover"
        
        return texto


# Singleton
_email_monitor: Optional[EmailMonitorModule] = None

def get_email_monitor(data_dir: str = "data") -> EmailMonitorModule:
    """Retorna instância singleton"""
    global _email_monitor
    if _email_monitor is None:
        _email_monitor = EmailMonitorModule(data_dir)
    return _email_monitor
