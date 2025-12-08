"""
🔐 Módulo de Autenticação Google com Gemini
Gerencia OAuth2 para Google Calendar, Gmail, Drive usando integração Gemini
"""
import os
import json
import pickle
import warnings
from typing import Optional, Dict, List
from datetime import datetime

# Google OAuth
from google.oauth2.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, RefreshError 
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gemini API
import google.generativeai as genai

# Escopos necessários
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]


class GeminiAuthManager:
    """Gerenciador de autenticação Google OAuth2 com integração Gemini"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tokens_dir = os.path.join(data_dir, "google_tokens")
        self.credentials_file = os.path.join(data_dir, "credentials.json")
        
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Cache de serviços autenticados
        self._services: Dict[str, Dict] = {}
        
        # Cache de instâncias Gemini
        self._gemini_models: Dict[str, any] = {}
        
        # Inicializa Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            print("[GEMINI_AUTH] Gemini API configurada!")
        else:
            print("[GEMINI_AUTH] ⚠️ GEMINI_API_KEY não configurada!")
    
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
        """
        if not self.has_credentials_file():
            return None
        
        try:
            # Cria a Flow com redirect_uri OOB
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            # Adiciona prompt='consent' se necessário
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent' if force_consent else 'select_account'
            )
            
            # Salva o estado
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            with open(state_file, 'w') as f:
                json.dump({
                    'state': state, 
                    'user_id': user_id,
                    'auth_url': auth_url,
                    'timestamp': datetime.now().isoformat()
                }, f)
            
            print(f"[GEMINI_AUTH] Estado salvo para user: {user_id}. Consent: {force_consent}")
            return auth_url
            
        except Exception as e:
            print(f"[GEMINI_AUTH] Erro ao gerar URL de auth: {e}")
            return None

    def _clean_auth_code(self, auth_code: str) -> str:
        """
        Remove espaços, quebras de linha e caracteres inválidos do código de autorização
        """
        clean_code = auth_code.strip()
        clean_code = clean_code.replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '')
        
        print(f"[GEMINI_AUTH] Código antes da limpeza: {len(auth_code)} caracteres")
        print(f"[GEMINI_AUTH] Código depois da limpeza: {len(clean_code)} caracteres")
        
        return clean_code

    def complete_auth(self, user_id: str, auth_code: str) -> tuple:
        """
        Completa autenticação com o código fornecido pelo usuário
        Retorna (sucesso, erro_type)
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
            
            print(f"[GEMINI_AUTH] Trocando código por token...")
            
            # Captura warnings de escopo
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings("always")
                
                try:
                    flow.fetch_token(code=clean_code)
                except Exception as token_error:
                    # Captura erros específicos
                    error_str = str(token_error)
                    if 'invalid_grant' in error_str.lower():
                        print(f"[GEMINI_AUTH] Erro: Código expirado")
                        return False, "EXPIRED"
                    if 'redirect_uri_mismatch' in error_str.lower() or 'invalid_client' in error_str.lower():
                        print(f"[GEMINI_AUTH] Erro: Configuração incorreta")
                        return False, "CONFIG_ERROR"
                    
                    print(f"[GEMINI_AUTH] ERRO FATAL na troca de token: {error_str}")
                    return False, "INVALID"
            
            # Verifica warnings de escopo
            for warning_item in w:
                if "Scope has changed" in str(warning_item.message):
                    print(f"[GEMINI_AUTH] ⚠️ AVISO DE ESCOPO DETECTADO!")
                    return False, "SCOPE_CHANGED"

            print(f"[GEMINI_AUTH] Token obtido com sucesso!")
            
            # Salva credenciais
            creds = flow.credentials
            token_file = self._get_token_file(user_id)
            with open(token_file, 'wb') as f:
                pickle.dump(creds, f)
            
            # Remove arquivos temporários
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            if os.path.exists(state_file):
                os.remove(state_file)
            
            print(f"[GEMINI_AUTH] Credenciais salvas para user: {user_id}")
            return True, None
            
        except Exception as e:
            print(f"[GEMINI_AUTH] Erro inesperado ao completar auth: {e}")
            import traceback
            traceback.print_exc()
            return False, "UNKNOWN"

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Obtém credenciais do usuário (refresh automático se necessário)
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
            print(f"[GEMINI_AUTH] Erro de Refresh de Token: {e}")
            self.revoke_auth(user_id)
            return None
        except Exception as e:
            print(f"[GEMINI_AUTH] Erro ao obter credentials: {e}")
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
            print(f"[GEMINI_AUTH] Erro ao criar serviço calendar: {e}")
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
            print(f"[GEMINI_AUTH] Erro ao criar serviço gmail: {e}")
            return None
    
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
            print(f"[GEMINI_AUTH] Erro ao criar serviço drive: {e}")
            return None
    
    def get_gemini_model(self, user_id: str, model: str = "gemini-1.5-flash"):
        """
        🆕 Obtém modelo Gemini para análise com contexto do usuário autenticado
        """
        cache_key = f"gemini_{user_id}_{model}"
        
        if cache_key in self._gemini_models:
            return self._gemini_models[cache_key]
        
        try:
            # Obtém informações do usuário para contexto
            user_info = self.get_user_info(user_id)
            email = user_info.get('email', 'usuário') if user_info else 'usuário'
            
            # Cria modelo Gemini
            gemini_model = genai.GenerativeModel(model)
            
            # Armazena em cache
            self._gemini_models[cache_key] = gemini_model
            
            print(f"[GEMINI_AUTH] Modelo Gemini {model} carregado para {email}")
            return gemini_model
            
        except Exception as e:
            print(f"[GEMINI_AUTH] Erro ao obter modelo Gemini: {e}")
            return None
    
    def analyze_with_gemini(self, user_id: str, content: str, context: str = "", 
                           model: str = "gemini-1.5-flash") -> str:
        """
        🆕 Analisa conteúdo usando Gemini com contexto da conta Google do usuário
        """
        try:
            gemini_model = self.get_gemini_model(user_id, model)
            if not gemini_model:
                return "❌ Gemini não disponível"
            
            # Obtém informações do usuário para contexto
            user_info = self.get_user_info(user_id)
            user_context = ""
            if user_info:
                user_context = f"\nContexto do usuário: {user_info.get('name', 'Usuário')} ({user_info.get('email', '')})"
            
            # Monta prompt com contexto
            prompt = f"{context}{user_context}\n\nAnálise: {content}"
            
            # Chama Gemini
            response = gemini_model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            print(f"[GEMINI_AUTH] Erro ao analisar com Gemini: {e}")
            return f"❌ Erro na análise: {str(e)}"
    
    def listar_eventos_calendar(self, user_id: str, max_results: int = 10):
        """Lista próximos eventos do calendário"""
        service = self.get_calendar_service(user_id)
        if not service:
            return None
        
        try:
            now = datetime.now().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except HttpError as error:
            print(f'[GEMINI_AUTH] Erro ao listar eventos: {error}')
            return None
    
    def criar_evento_calendar(self, user_id: str, titulo: str, data_inicio: str, 
                             data_fim: str = None, descricao: str = '', 
                             cor: str = None, recorrencia: list = None, 
                             lembretes: list = None):
        """Cria novo evento no calendário"""
        service = self.get_calendar_service(user_id)
        if not service:
            return False
        
        try:
            event = {
                'summary': titulo,
                'description': descricao,
                'start': {'dateTime': data_inicio},
                'end': {'dateTime': data_fim or data_inicio},
                'colorId': cor
            }
            
            if recorrencia:
                event['recurrence'] = recorrencia
            
            if lembretes:
                event['reminders'] = {'useDefault': False, 'overrides': lembretes}
            
            service.events().insert(calendarId='primary', body=event).execute()
            return True
        except Exception as e:
            print(f'[GEMINI_AUTH] Erro ao criar evento: {e}')
            return False
    
    def revoke_auth(self, user_id: str) -> bool:
        """Revoga autenticação do usuário"""
        try:
            token_file = self._get_token_file(user_id)
            if os.path.exists(token_file):
                os.remove(token_file)
            
            # Limpa cache
            keys_to_delete = [k for k in self._services.keys() if user_id in k]
            for key in keys_to_delete:
                del self._services[key]
            
            keys_to_delete = [k for k in self._gemini_models.keys() if user_id in k]
            for key in keys_to_delete:
                del self._gemini_models[key]
            
            print(f"[GEMINI_AUTH] Autenticação revogada para user: {user_id}")
            return True
        except Exception as e:
            print(f'[GEMINI_AUTH] Erro ao revogar autenticação: {e}')
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Obtém informações do usuário autenticado"""
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            print(f'[GEMINI_AUTH] Erro ao obter informações do usuário: {e}')
            return None


# Singleton
_gemini_auth: Optional[GeminiAuthManager] = None

def get_gemini_auth(data_dir: str = "data") -> GeminiAuthManager:
    """Retorna instância singleton do GeminiAuthManager"""
    global _gemini_auth
    if _gemini_auth is None:
        _gemini_auth = GeminiAuthManager(data_dir)
    return _gemini_auth
