"""
Modulo de Agenda
Gerencia compromissos, lembretes e calendario
Integracao com Google Calendar
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from uuid import uuid4

try:
    from modules.google_auth import get_google_auth, GoogleAuthManager
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


@dataclass
class Evento:
    id: str
    titulo: str
    descricao: str = ""
    data: str = ""
    hora: str = ""
    duracao_min: int = 60
    lembrete_min: int = 30
    recorrente: bool = False
    user_id: str = ""
    criado_em: str = ""
    google_event_id: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Lembrete:
    id: str
    texto: str
    data_hora: str
    user_id: str
    ativo: bool = True
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class AgendaModule:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.eventos_file = os.path.join(data_dir, "eventos.json")
        self.lembretes_file = os.path.join(data_dir, "lembretes.json")
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        self.google_auth = None
        if GOOGLE_AUTH_AVAILABLE:
            self.google_auth = get_google_auth(data_dir)
    
    def _load_data(self):
        if os.path.exists(self.eventos_file):
            with open(self.eventos_file, 'r', encoding='utf-8') as f:
                self.eventos = json.load(f)
        else:
            self.eventos = []
        if os.path.exists(self.lembretes_file):
            with open(self.lembretes_file, 'r', encoding='utf-8') as f:
                self.lembretes = json.load(f)
        else:
            self.lembretes = []
    
    def _save_data(self):
        with open(self.eventos_file, 'w', encoding='utf-8') as f:
            json.dump(self.eventos, f, ensure_ascii=False, indent=2)
        with open(self.lembretes_file, 'w', encoding='utf-8') as f:
            json.dump(self.lembretes, f, ensure_ascii=False, indent=2)
    
    def is_google_connected(self, user_id: str) -> bool:
        if not self.google_auth:
            return False
        return self.google_auth.is_authenticated(user_id)
    
    def get_google_login_url(self, user_id: str):
        if not self.google_auth:
            return None
        return self.google_auth.get_auth_url(user_id)
    
    def complete_google_login(self, user_id: str, code: str) -> bool:
        if not self.google_auth:
            return False
        return self.google_auth.complete_auth(user_id, code)
    
    def disconnect_google(self, user_id: str) -> bool:
        if not self.google_auth:
            return False
        return self.google_auth.revoke_auth(user_id)
    
    async def handle(self, command: str, args: List[str], user_id: str, attachments: list = None) -> str:
        if command in ['login', 'conectar']:
            return await self._handle_login(user_id, args)
        if command in ['logout', 'desconectar']:
            return self._handle_logout(user_id)
        if command == 'agenda':
            return await self._get_agenda(user_id)
        if command == 'lembrete':
            if args:
                return self._criar_lembrete(user_id, ' '.join(args))
            return "Use: /lembrete [texto] [hora]"
        if command == 'compromissos':
            return await self._get_compromissos(user_id)
        if command == 'lembretes':
            return self._get_lembretes(user_id)
        if command in ['cancelar', 'remover']:
            if args:
                return await self._cancelar_item(user_id, args[0])
            return "Use: /cancelar [id]"
        if command == 'agendar':
            if args:
                return await self._criar_evento_comando(user_id, ' '.join(args))
            return "Use: /agendar [titulo] [data] [hora]"
        return "Comandos: /agenda, /agendar, /lembrete, /login"
    
    async def handle_natural(self, message: str, analysis: Any, user_id: str, attachments: list = None) -> str:
        text_lower = message.lower()
        text_strip = message.strip()
        
        # Detecta código do Google OAuth (começa com 4/ ou é um código longo)
        if text_strip.startswith('4/') or (len(text_strip) > 40 and '/' in text_strip):
            return await self._handle_login(user_id, [text_strip])
        
        if any(word in text_lower for word in ['login', 'conectar google', 'logar']):
            return await self._handle_login(user_id, [])
        if any(word in text_lower for word in ['lembrar', 'lembrete', 'avisar']):
            return self._criar_lembrete(user_id, message)
        if any(word in text_lower for word in ['marcar', 'agendar', 'reuniao']):
            return await self._criar_evento(user_id, message, analysis)
        if any(word in text_lower for word in ['agenda', 'hoje', 'compromissos']):
            return await self._get_agenda(user_id)
        return await self._get_agenda(user_id)
    
    async def _handle_login(self, user_id: str, args: List[str]) -> str:
        print(f"[LOGIN] Iniciando login para user: {user_id}, args: {args}")
        
        # Verifica se já está conectado
        if self.is_google_connected(user_id):
            print(f"[LOGIN] Usuário {user_id} já está conectado")
            # Obtém informações do usuário
            user_info = self.google_auth.get_user_info(user_id)
            nome_usuario = ""
            email_usuario = ""
            
            if user_info:
                nome_usuario = user_info.get('name', '')
                email_usuario = user_info.get('email', '')
            
            saudacao = f", *{nome_usuario}*" if nome_usuario else ""
            email_info = f"\n📧 E-mail: {email_usuario}" if email_usuario else ""
            
            return f"""✅ *Você já está conectado ao Google{saudacao}!*
{email_info}
📅 Sua agenda está sincronizada
📧 Gmail está ativo

Para desconectar, digite: *logout*"""
        
        # Se recebeu código, tenta completar login
        if args and len(args[0]) > 10:
            code = args[0].strip()
            print(f"[LOGIN] Tentando completar auth para user {user_id} com código: {code[:20]}...")
            
            if self.complete_google_login(user_id, code):
                # Obtém informações do usuário do Google
                user_info = self.google_auth.get_user_info(user_id)
                nome_usuario = ""
                email_usuario = ""
                
                if user_info:
                    nome_usuario = user_info.get('name', '')
                    email_usuario = user_info.get('email', '')
                
                # Atualiza perfil se disponível
                try:
                    from modules.perfil import PerfilModule
                    perfil_mod = PerfilModule()
                    perfil_mod.atualizar_perfil(
                        user_id, 
                        google_conectado=True, 
                        google_email=email_usuario,
                        nome=nome_usuario if nome_usuario else None,
                        onboarding_completo=True
                    )
                except Exception as e:
                    print(f"[LOGIN] Erro ao atualizar perfil: {e}")
                
                # Monta mensagem de sucesso com nome
                saudacao = f", *{nome_usuario}*" if nome_usuario else ""
                email_info = f"\n📧 E-mail: {email_usuario}" if email_usuario else ""
                
                return f"""🎉 *Login realizado com sucesso{saudacao}!*

✅ Sua conta Google foi conectada!{email_info}

Agora posso:
📅 Acessar seu Google Calendar
📧 Ler seus e-mails

Experimente digitar: *agenda*"""
            else:
                return """❌ *Código inválido ou expirado*

O código do Google expira em poucos minutos.

🔄 Tente novamente:
1. Digite *login*
2. Clique no novo link
3. Cole o código rapidamente"""
        
        # Verifica se tem credenciais configuradas
        print(f"[LOGIN] Verificando google_auth: {self.google_auth is not None}")
        if not self.google_auth:
            print("[LOGIN] google_auth não disponível!")
            return """⚠️ *Módulo Google não disponível*

Entre em contato com o administrador."""
        
        print(f"[LOGIN] Verificando credentials file: {self.google_auth.has_credentials_file()}")
        if not self.google_auth.has_credentials_file():
            print("[LOGIN] credentials.json não encontrado!")
            return """⚠️ *Configuração Necessária*

O arquivo credentials.json não foi encontrado.

📋 Para configurar:
1. Acesse: console.cloud.google.com
2. Crie um projeto
3. Ative as APIs: Calendar, Gmail
4. Crie credenciais OAuth2
5. Baixe o credentials.json
6. Coloque na pasta data/

📖 Tutorial: https://developers.google.com/calendar/quickstart/python"""
        
        # Gera URL de login
        print(f"[LOGIN] Gerando URL de login para user: {user_id}")
        auth_url = self.get_google_login_url(user_id)
        print(f"[LOGIN] URL gerada: {auth_url[:50] if auth_url else 'NENHUMA'}...")
        if not auth_url:
            print("[LOGIN] Falha ao gerar URL!")
            return """❌ *Erro ao gerar link de login*

Tente novamente em alguns segundos."""
        
        print(f"[LOGIN] Retornando mensagem com link!")
        return f"""🔐 *Conectar com Google*

━━━━━━━━━━━━━━━━━━━━━

📌 *Siga os passos:*

*1️⃣ Clique no link abaixo:*
{auth_url}

*2️⃣ Escolha sua conta Google*

*3️⃣ Clique em "Permitir"*
(Pode aparecer aviso de app não verificado - clique em "Avançado" e depois "Acessar")

*4️⃣ Copie o código que aparecer*
O código começa com 4/

*5️⃣ Cole o código aqui neste chat*

━━━━━━━━━━━━━━━━━━━━━

⏰ O código expira em 10 minutos!
Se demorar, digite *login* novamente."""
    
    def _handle_logout(self, user_id: str) -> str:
        if self.disconnect_google(user_id):
            return "Conta Google desconectada!\n\nUse /login para conectar novamente."
        return "Erro ao desconectar."
    
    async def _get_google_events(self, user_id: str, time_min: datetime = None, time_max: datetime = None, max_results: int = 10) -> List[Dict]:
        if not self.google_auth:
            return []
        service = self.google_auth.get_calendar_service(user_id)
        if not service:
            return []
        try:
            if not time_min:
                time_min = datetime.now()
            if not time_max:
                time_max = time_min + timedelta(days=7)
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"Erro Google Calendar: {e}")
            return []
    
    async def _create_google_event(self, user_id: str, titulo: str, data: str, hora: str, duracao_min: int = 60):
        if not self.google_auth:
            return None
        service = self.google_auth.get_calendar_service(user_id)
        if not service:
            return None
        try:
            start_dt = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=duracao_min)
            event = {
                'summary': titulo,
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 30}]}
            }
            result = service.events().insert(calendarId='primary', body=event).execute()
            return result.get('id')
        except Exception as e:
            print(f"Erro criar evento: {e}")
            return None
    
    async def _delete_google_event(self, user_id: str, event_id: str) -> bool:
        if not self.google_auth:
            return False
        service = self.google_auth.get_calendar_service(user_id)
        if not service:
            return False
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except:
            return False
    
    async def _get_agenda(self, user_id: str) -> str:
        hoje = datetime.now()
        hoje_str = hoje.strftime('%Y-%m-%d')
        response = f"Agenda de Hoje ({hoje.strftime('%d/%m/%Y')})\n\n"
        eventos_hoje = []
        if self.is_google_connected(user_id):
            response += "Conectado ao Google Calendar\n\n"
            google_events = await self._get_google_events(user_id, time_min=hoje.replace(hour=0, minute=0), time_max=hoje.replace(hour=23, minute=59))
            for event in google_events:
                start = event.get('start', {})
                hora = ""
                if 'dateTime' in start:
                    dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    hora = dt.strftime('%H:%M')
                elif 'date' in start:
                    hora = "Dia todo"
                eventos_hoje.append({'hora': hora, 'titulo': event.get('summary', 'Sem titulo'), 'fonte': 'google'})
        else:
            response += "Modo local (use /login para conectar ao Google)\n\n"
        for evento in self.eventos:
            if evento.get('user_id') == user_id and evento.get('data') == hoje_str:
                eventos_hoje.append({'hora': evento.get('hora', '--:--'), 'titulo': evento.get('titulo', 'Sem titulo'), 'fonte': 'local', 'id': evento.get('id')})
        lembretes_hoje = [l for l in self.lembretes if l.get('user_id') == user_id and l.get('ativo') and l.get('data_hora', '').startswith(hoje_str)]
        if not eventos_hoje and not lembretes_hoje:
            response += "Nenhum compromisso para hoje.\n\nDiga 'agendar reuniao amanha as 10h' para criar."
            return response
        if eventos_hoje:
            response += "Compromissos:\n"
            for ev in sorted(eventos_hoje, key=lambda x: x.get('hora', '')):
                icone = "[G]" if ev.get('fonte') == 'google' else "[L]"
                response += f"  {icone} {ev['hora']} - {ev['titulo']}\n"
        if lembretes_hoje:
            response += "\nLembretes:\n"
            for lembrete in lembretes_hoje:
                response += f"  - {lembrete.get('texto', '')}\n"
        return response
    
    async def _get_compromissos(self, user_id: str) -> str:
        hoje = datetime.now()
        response = "Proximos Compromissos:\n\n"
        compromissos = []
        if self.is_google_connected(user_id):
            google_events = await self._get_google_events(user_id, time_min=hoje, time_max=hoje + timedelta(days=30), max_results=15)
            for event in google_events:
                start = event.get('start', {})
                if 'dateTime' in start:
                    dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    compromissos.append({'data': dt.strftime('%d/%m'), 'hora': dt.strftime('%H:%M'), 'titulo': event.get('summary', 'Sem titulo'), 'fonte': 'google'})
        for evento in self.eventos:
            if evento.get('user_id') != user_id:
                continue
            try:
                data = datetime.strptime(evento.get('data', ''), '%Y-%m-%d')
                if data >= hoje:
                    compromissos.append({'data': data.strftime('%d/%m'), 'hora': evento.get('hora', ''), 'titulo': evento.get('titulo', ''), 'fonte': 'local'})
            except:
                pass
        if not compromissos:
            return "Nenhum compromisso agendado."
        for c in compromissos[:15]:
            icone = "[G]" if c.get('fonte') == 'google' else "[L]"
            hora = f" {c['hora']}" if c.get('hora') else ""
            response += f"{icone} {c['data']}{hora} - {c['titulo']}\n"
        return response
    
    def _get_lembretes(self, user_id: str) -> str:
        ativos = [l for l in self.lembretes if l.get('user_id') == user_id and l.get('ativo')]
        if not ativos:
            return "Nenhum lembrete ativo."
        response = "Lembretes Ativos:\n\n"
        for lembrete in ativos:
            response += f"  - [{lembrete.get('id', '')}] {lembrete.get('texto', '')} ({lembrete.get('data_hora', '')[:10]})\n"
        return response
    
    def _criar_lembrete(self, user_id: str, texto: str) -> str:
        hora_match = re.search(r'(\d{1,2})[h:](\d{2})?', texto)
        if hora_match:
            hora = int(hora_match.group(1))
            minuto = int(hora_match.group(2) or 0)
            data_hora = datetime.now().replace(hour=hora, minute=minuto)
            texto_limpo = re.sub(r'as?\s*\d{1,2}[h:]\d{0,2}', '', texto).strip()
        else:
            data_hora = datetime.now() + timedelta(hours=1)
            texto_limpo = texto
        for word in ['lembrete', 'lembrar', 'me', 'de', 'para', 'avisar']:
            texto_limpo = re.sub(rf'\b{word}\b', '', texto_limpo, flags=re.IGNORECASE)
        texto_limpo = texto_limpo.strip()
        if not texto_limpo:
            return "Por favor, informe o texto do lembrete."
        lembrete = Lembrete(id=str(uuid4())[:8], texto=texto_limpo, data_hora=data_hora.isoformat(), user_id=user_id, ativo=True, criado_em=datetime.now().isoformat())
        self.lembretes.append(lembrete.to_dict())
        self._save_data()
        return f"Lembrete Criado!\n\n{texto_limpo}\n{data_hora.strftime('%d/%m/%Y as %H:%M')}\nID: {lembrete.id}"
    
    async def _criar_evento(self, user_id: str, texto: str, analysis: Any) -> str:
        entities = analysis.entities if analysis else {}
        datetime_info = entities.get('datetime', {})
        amanha = any(word in texto.lower() for word in ['amanha'])
        data = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d') if amanha else datetime.now().strftime('%Y-%m-%d')
        hora_match = re.search(r'(\d{1,2})[h:](\d{2})?', texto)
        hora = f"{int(hora_match.group(1)):02d}:{hora_match.group(2) or '00'}" if hora_match else datetime_info.get('time', '09:00')
        titulo = texto
        for word in ['agendar', 'marcar', 'criar', 'amanha', 'hoje', 'as']:
            titulo = re.sub(rf'\b{word}\b', '', titulo, flags=re.IGNORECASE)
        if hora_match:
            titulo = titulo.replace(hora_match.group(0), '')
        titulo = titulo.strip()[:50] or "Compromisso"
        google_event_id = None
        if self.is_google_connected(user_id):
            google_event_id = await self._create_google_event(user_id, titulo, data, hora)
        evento = Evento(id=str(uuid4())[:8], titulo=titulo, data=data, hora=hora, user_id=user_id, criado_em=datetime.now().isoformat(), google_event_id=google_event_id or "")
        self.eventos.append(evento.to_dict())
        self._save_data()
        data_fmt = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        if google_event_id:
            return f"Evento Criado no Google Calendar!\n\n{titulo}\n{data_fmt}\n{hora}\nSincronizado"
        return f"Evento Agendado!\n\n{titulo}\n{data_fmt}\n{hora}\nModo local\n\nUse /login para sincronizar"
    
    async def _criar_evento_comando(self, user_id: str, args_str: str) -> str:
        class FakeAnalysis:
            entities = {}
        return await self._criar_evento(user_id, args_str, FakeAnalysis())
    
    async def _cancelar_item(self, user_id: str, item_id: str) -> str:
        for i, evento in enumerate(self.eventos):
            if evento.get('id') == item_id and evento.get('user_id') == user_id:
                titulo = evento.get('titulo', '')[:50]
                google_id = evento.get('google_event_id')
                if google_id and self.is_google_connected(user_id):
                    await self._delete_google_event(user_id, google_id)
                self.eventos.pop(i)
                self._save_data()
                return f"Evento Cancelado!\n\n{titulo}"
        for i, lembrete in enumerate(self.lembretes):
            if lembrete.get('id') == item_id and lembrete.get('user_id') == user_id:
                texto = lembrete.get('texto', '')[:50]
                self.lembretes.pop(i)
                self._save_data()
                return f"Lembrete Cancelado!\n\n{texto}"
        return f"Item {item_id} nao encontrado."
    
    async def _criar_lembrete_interno(self, user_id: str, texto: str, data_hora: str, extra: dict = None) -> str:
        lembrete = Lembrete(id=str(uuid4())[:8], texto=texto, data_hora=data_hora, user_id=user_id, ativo=True, criado_em=datetime.now().isoformat())
        lembrete_dict = lembrete.to_dict()
        if extra:
            lembrete_dict['extra'] = extra
        self.lembretes.append(lembrete_dict)
        self._save_data()
        return lembrete.id

