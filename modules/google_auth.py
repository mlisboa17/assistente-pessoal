"""
🔐 Módulo de Autenticação Google
Gerencia OAuth2 para Google Calendar, Gmail, Drive
"""
import os
import json
import pickle
import warnings # Importado para lidar com warnings de escopo
from typing import Optional, Dict, List
from datetime import datetime

# Google OAuth
from google.oauth2.credentials import Credentials
# Importação da exceção específica
from google.auth.exceptions import DefaultCredentialsError, RefreshError 
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError # Importação para tratamento de erros de API

# Escopos necessários - ADICIONADO 'openid' e 'drive.readonly'
SCOPES = [
    'openid',                                               # Necessário para OpenID Connect/Userinfo
    'https://www.googleapis.com/auth/calendar',             # Calendário
    'https://www.googleapis.com/auth/calendar.events',      # Eventos
    'https://www.googleapis.com/auth/userinfo.profile',     # Perfil do usuário
    'https://www.googleapis.com/auth/userinfo.email',       # Email do usuário
    'https://www.googleapis.com/auth/gmail.send',           # Gmail (envio)
    'https://www.googleapis.com/auth/gmail.readonly',       # Gmail (leitura)
    'https://www.googleapis.com/auth/drive.readonly',       # Drive (leitura)
]


class GoogleAuthManager:
    """Gerenciador de autenticação Google OAuth2"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tokens_dir = os.path.join(data_dir, "google_tokens")
        self.credentials_file = os.path.join(data_dir, "credentials.json")
        
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Cache de serviços autenticados
        self._services: Dict[str, Dict] = {}
    
    def _get_token_file(self, user_id: str) -> str:
        """Retorna caminho do arquivo de token do usuário"""
        return os.path.join(self.tokens_dir, f"token_{user_id}.pickle")
    
    def has_credentials_file(self) -> bool:
        """Verifica se o arquivo de credenciais existe"""
        return os.path.exists(self.credentials_file)
    
    def is_authenticated(self, user_id: str) -> bool:
        """Verifica se usuário está autenticado"""
        token_file = self._get_token_file(user_id)
        if not os.path.exists(token_file):
            return False
        
        try:
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)
            return creds and creds.valid
        except:
            return False
    
    def get_auth_url(self, user_id: str, force_consent: bool = False) -> Optional[str]:
        """
        Gera URL de autenticação para o usuário
        (Mesmo código, mas com o 'prompt=consent' condicionalmente ativado)
        """
        if not self.has_credentials_file():
            return None
        
        try:
            # Cria a Flow, mantendo o redirect_uri OOB
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            # Condicionalmente adiciona prompt='consent' para resolver erro de scope
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent' if force_consent else 'select_account' 
                # 'select_account' é o padrão se não for force_consent
            )
            
            # Salva o estado para potencial verificação (OOB simplifica isso)
            # ... (Mantido o código de salvar state)
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            with open(state_file, 'w') as f:
                json.dump({
                    'state': state, 
                    'user_id': user_id,
                    'auth_url': auth_url,
                    'timestamp': datetime.now().isoformat()
                }, f)
            
            print(f"[GOOGLE_AUTH] Estado salvo para user: {user_id}. Consent: {force_consent}")
            return auth_url
            
        except Exception as e:
            # ... (Mantido o tratamento de erro)
            print(f"Erro ao gerar URL de auth: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_auth_code(self, auth_code: str) -> str:
        """
        Remove espaços, quebras de linha e caracteres inválidos do código de autorização
        (Mantido o código original que é muito bom)
        """
        clean_code = auth_code.strip()
        clean_code = clean_code.replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '')
        
        print(f"[GOOGLE_AUTH] Código antes da limpeza: {len(auth_code)} caracteres")
        print(f"[GOOGLE_AUTH] Código depois da limpeza: {len(clean_code)} caracteres")
        
        return clean_code
    
    def complete_auth(self, user_id: str, auth_code: str) -> tuple:
        """
        Completa autenticação com o código fornecido pelo usuário
        (Refatorado o bloco try-except para ser mais limpo e específico)
        """
        if not self.has_credentials_file():
            return False, "credentials.json não encontrado"
        
        try:
            clean_code = self._clean_auth_code(auth_code)
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            print(f"[GOOGLE_AUTH] Trocando código por token...")
            
            # ⚠️ Bloco para capturar o Warning de escopo
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings("always") # Garante que todos os warnings são capturados
                
                try:
                    flow.fetch_token(code=clean_code)
                except Exception as token_error:
                    # Captura erros graves como Invalid Grant (código inválido/expirado)
                    error_str = str(token_error)
                    if 'invalid_grant' in error_str.lower():
                        return False, "EXPIRED"
                    if 'redirect_uri_mismatch' in error_str.lower() or 'invalid_client' in error_str.lower():
                        return False, "CONFIG_ERROR"
                    
                    print(f"[GOOGLE_AUTH] ERRO FATAL na troca de token: {error_str}")
                    return False, "INVALID"
            
            # Verifica se houve o Warning após a troca de token
            for warning_item in w:
                if "Scope has changed" in str(warning_item.message):
                    print(f"[GOOGLE_AUTH] ⚠️ AVISO DE ESCOPO DETECTADO!")
                    print(f"[GOOGLE_AUTH] Necessária reautenticação com consentimento forçado")
                    return False, "SCOPE_CHANGED" 

            print(f"[GOOGLE_AUTH] Token obtido com sucesso!")
            
            # Salva credenciais (código original mantido)
            creds = flow.credentials
            token_file = self._get_token_file(user_id)
            with open(token_file, 'wb') as f:
                pickle.dump(creds, f)
            
            # Remove arquivos temporários (código original mantido)
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            if os.path.exists(state_file):
                os.remove(state_file)
            
            return True, None
            
        except Exception as e:
            print(f"[GOOGLE_AUTH] Erro inesperado ao completar auth: {e}")
            import traceback
            traceback.print_exc()
            return False, "UNKNOWN"
    
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Obtém credenciais do usuário (refresh automático se necessário)
        (Melhorado com exceções mais específicas)
        """
        token_file = self._get_token_file(user_id)
        
        if not os.path.exists(token_file):
            return None
        
        try:
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)
            
            # Refresh se expirado
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_file, 'wb') as f:
                    pickle.dump(creds, f)
            
            return creds if creds and creds.valid else None
            
        except (RefreshError, DefaultCredentialsError) as e:
            # Captura erros específicos de refresh ou credenciais inválidas
            print(f"[GOOGLE_AUTH] Erro de Refresh de Token. Token inválido: {e}")
            self.revoke_auth(user_id) # Revoga e força novo login
            return None
        except Exception as e:
            print(f"Erro ao obter credentials: {e}")
            return None
    
    def get_calendar_service(self, user_id: str):
        """Obtém serviço do Google Calendar autenticado"""
        cache_key = f"calendar_{user_id}"
        
        if cache_key in self._services:
            return self._services[cache_key]
        
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            self._services[cache_key] = service
            return service
        except Exception as e:
            print(f"Erro ao criar serviço calendar: {e}")
            return None
    
    def get_gmail_service(self, user_id: str):
        """Obtém serviço do Gmail autenticado"""
        cache_key = f"gmail_{user_id}"
        
        if cache_key in self._services:
            return self._services[cache_key]
        
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('gmail', 'v1', credentials=creds)
            self._services[cache_key] = service
            return service
        except Exception as e:
            print(f"Erro ao criar serviço gmail: {e}")
            return None
    
    # Adicionado get_drive_service
    def get_drive_service(self, user_id: str):
        """Obtém serviço do Google Drive autenticado"""
        cache_key = f"drive_{user_id}"
        
        if cache_key in self._services:
            return self._services[cache_key]
        
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('drive', 'v3', credentials=creds)
            self._services[cache_key] = service
            return service
        except Exception as e:
            print(f"Erro ao criar serviço drive: {e}")
            return None
    
    def listar_eventos_calendar(self, user_id: str, max_results: int = 10):
        """Lista os próximos eventos do Google Calendar do usuário"""
        service = self.get_calendar_service(user_id)
        if not service:
            return None
        try:
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indica UTC
            events_result = service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            print(f"Erro ao listar eventos do Calendar: {e}")
            return None

    def criar_evento_calendar(self, user_id: str, titulo: str, data_inicio: str, data_fim: str = None, descricao: str = '', cor: str = None, recorrencia: list = None, lembretes: list = None):
        """Cria um evento no Google Calendar do usuário
        data_inicio e data_fim: formato ISO 8601 (ex: '2025-12-07T09:00:00-03:00')
        cor: string (ID da cor do Google Calendar)
        recorrencia: lista de strings RRULE (ex: ['RRULE:FREQ=MONTHLY;BYMONTHDAY=10'])
        lembretes: lista de dicts (ex: [{'method': 'popup', 'minutes': 60}])
        """
        service = self.get_calendar_service(user_id)
        if not service:
            return None
        event = {
            'summary': titulo,
            'description': descricao,
            'start': {'dateTime': data_inicio},
            'end': {'dateTime': data_fim or data_inicio},
        }
        if cor:
            event['colorId'] = cor
        if recorrencia:
            event['recurrence'] = recorrencia
        if lembretes:
            event['reminders'] = {'useDefault': False, 'overrides': lembretes}
        try:
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            return created_event
        except Exception as e:
            print(f"Erro ao criar evento no Calendar: {e}")
            return None
    
    def revoke_auth(self, user_id: str) -> bool:
        """Revoga autenticação do usuário"""
        token_file = self._get_token_file(user_id)
        
        try:
            if os.path.exists(token_file):
                os.remove(token_file)
            
            # Remove do cache
            for key in list(self._services.keys()):
                if user_id in key:
                    del self._services[key]
            
            return True
        except:
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Obtém informações do usuário logado"""
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info
        except:
            return None


# Singleton
_google_auth: Optional[GoogleAuthManager] = None

def get_google_auth(data_dir: str = "data") -> GoogleAuthManager:
    """Retorna instância singleton do GoogleAuthManager"""
    global _google_auth
    if _google_auth is None:
        _google_auth = GoogleAuthManager(data_dir)
    return _google_auth
