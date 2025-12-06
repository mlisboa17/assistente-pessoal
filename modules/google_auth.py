"""
🔐 Módulo de Autenticação Google
Gerencia OAuth2 para Google Calendar, Gmail, Drive
"""
import os
import json
import pickle
from typing import Optional, Dict, List
from datetime import datetime

# Google OAuth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/calendar',           # Calendário
    'https://www.googleapis.com/auth/calendar.events',    # Eventos
    'https://www.googleapis.com/auth/gmail.readonly',     # Gmail (leitura)
    'https://www.googleapis.com/auth/gmail.send',         # Gmail (envio)
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
    
    def get_auth_url(self, user_id: str) -> Optional[str]:
        """
        Gera URL de autenticação para o usuário
        
        Returns:
            URL para o usuário clicar e autorizar, ou None se não houver credentials.json
        """
        if not self.has_credentials_file():
            return None
        
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Modo "copiar código"
            )
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id  # Guarda user_id no state
            )
            
            # Salva apenas o state para referência (não precisa do flow completo)
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            with open(state_file, 'w') as f:
                json.dump({'state': state, 'user_id': user_id}, f)
            
            return auth_url
            
        except Exception as e:
            print(f"Erro ao gerar URL de auth: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def complete_auth(self, user_id: str, auth_code: str) -> bool:
        """
        Completa autenticação com o código fornecido pelo usuário
        
        Args:
            user_id: ID do usuário
            auth_code: Código de autorização do Google
            
        Returns:
            True se autenticação bem sucedida
        """
        print(f"[GOOGLE_AUTH] Tentando completar auth para user: {user_id}")
        print(f"[GOOGLE_AUTH] Código recebido: {auth_code[:30]}...")
        
        if not self.has_credentials_file():
            print(f"[GOOGLE_AUTH] ERRO: credentials.json não encontrado!")
            return False
        
        try:
            print(f"[GOOGLE_AUTH] Criando flow e trocando código por token...")
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            token_file = self._get_token_file(user_id)
            with open(token_file, 'wb') as f:
                pickle.dump(creds, f)
            
            print(f"[GOOGLE_AUTH] Token salvo em: {token_file}")
            print(f"[GOOGLE_AUTH] Login completo com sucesso!")
            
            # Remove state file se existir
            state_file = os.path.join(self.tokens_dir, f"state_{user_id}.json")
            if os.path.exists(state_file):
                os.remove(state_file)
            
            return True
            
        except Exception as e:
            print(f"[GOOGLE_AUTH] Erro ao completar auth: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
