"""
☁️ Cloud Storage Manager
Integração com Google Drive e OneDrive para armazenamento de arquivos
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, BinaryIO
from dataclasses import dataclass

# Google Drive
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# OneDrive (Microsoft Graph)
try:
    import msal
    import requests as http_requests
    ONEDRIVE_AVAILABLE = True
except ImportError:
    ONEDRIVE_AVAILABLE = False


@dataclass
class ArquivoCloud:
    """Representa um arquivo na nuvem"""
    id: str
    nome: str
    tipo: str  # 'arquivo' ou 'pasta'
    tamanho: int = 0
    mime_type: str = ""
    criado_em: str = ""
    modificado_em: str = ""
    url: str = ""
    provider: str = ""  # 'google' ou 'onedrive'


class GoogleDriveManager:
    """Gerenciador do Google Drive"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_file: str = "credentials.json", 
                 token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
    
    def conectar(self) -> bool:
        """Conecta ao Google Drive"""
        if not GOOGLE_AVAILABLE:
            print("⚠️ Bibliotecas do Google não instaladas.")
            print("   pip install google-api-python-client google-auth-oauthlib")
            return False
        
        try:
            # Verifica se tem token salvo
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # Se não tem credenciais ou estão inválidas
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        print(f"⚠️ Arquivo {self.credentials_file} não encontrado.")
                        print("   Baixe do Google Cloud Console.")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Salva token para próximas execuções
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('drive', 'v3', credentials=self.creds)
            print("✅ Conectado ao Google Drive!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def listar_arquivos(self, pasta_id: str = None, limite: int = 20) -> List[ArquivoCloud]:
        """Lista arquivos do Drive"""
        if not self.service:
            if not self.conectar():
                return []
        
        try:
            query = ""
            if pasta_id:
                query = f"'{pasta_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=limite,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            arquivos = []
            for item in results.get('files', []):
                arquivo = ArquivoCloud(
                    id=item['id'],
                    nome=item['name'],
                    tipo='pasta' if 'folder' in item.get('mimeType', '') else 'arquivo',
                    tamanho=int(item.get('size', 0)),
                    mime_type=item.get('mimeType', ''),
                    criado_em=item.get('createdTime', ''),
                    modificado_em=item.get('modifiedTime', ''),
                    provider='google'
                )
                arquivos.append(arquivo)
            
            return arquivos
            
        except Exception as e:
            print(f"❌ Erro ao listar arquivos: {e}")
            return []
    
    def upload(self, arquivo_local: str, nome: str = None, 
               pasta_id: str = None) -> Optional[str]:
        """Faz upload de arquivo para o Drive"""
        if not self.service:
            if not self.conectar():
                return None
        
        if not os.path.exists(arquivo_local):
            print(f"❌ Arquivo não encontrado: {arquivo_local}")
            return None
        
        try:
            nome = nome or os.path.basename(arquivo_local)
            
            file_metadata = {'name': nome}
            if pasta_id:
                file_metadata['parents'] = [pasta_id]
            
            # Detecta tipo MIME
            import mimetypes
            mime_type = mimetypes.guess_type(arquivo_local)[0] or 'application/octet-stream'
            
            media = MediaFileUpload(arquivo_local, mimetype=mime_type)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            print(f"✅ Upload concluído: {nome}")
            return file.get('id')
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return None
    
    def download(self, arquivo_id: str, destino: str) -> bool:
        """Baixa arquivo do Drive"""
        if not self.service:
            if not self.conectar():
                return False
        
        try:
            request = self.service.files().get_media(fileId=arquivo_id)
            
            with open(destino, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            print(f"✅ Download concluído: {destino}")
            return True
            
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return False
    
    def criar_pasta(self, nome: str, pasta_pai_id: str = None) -> Optional[str]:
        """Cria uma pasta no Drive"""
        if not self.service:
            if not self.conectar():
                return None
        
        try:
            file_metadata = {
                'name': nome,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if pasta_pai_id:
                file_metadata['parents'] = [pasta_pai_id]
            
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            print(f"❌ Erro ao criar pasta: {e}")
            return None
    
    def deletar(self, arquivo_id: str) -> bool:
        """Deleta arquivo ou pasta"""
        if not self.service:
            if not self.conectar():
                return False
        
        try:
            self.service.files().delete(fileId=arquivo_id).execute()
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar: {e}")
            return False
    
    def compartilhar(self, arquivo_id: str, email: str, 
                     permissao: str = "reader") -> bool:
        """Compartilha arquivo com usuário"""
        if not self.service:
            if not self.conectar():
                return False
        
        try:
            permission = {
                'type': 'user',
                'role': permissao,  # reader, writer, commenter
                'emailAddress': email
            }
            
            self.service.permissions().create(
                fileId=arquivo_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao compartilhar: {e}")
            return False


class OneDriveManager:
    """Gerenciador do OneDrive"""
    
    SCOPES = ['Files.ReadWrite', 'User.Read']
    GRAPH_URL = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv('AZURE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('AZURE_CLIENT_SECRET')
        self.token = None
        self.app = None
    
    def conectar(self) -> bool:
        """Conecta ao OneDrive"""
        if not ONEDRIVE_AVAILABLE:
            print("⚠️ Bibliotecas do OneDrive não instaladas.")
            print("   pip install msal requests")
            return False
        
        if not self.client_id:
            print("⚠️ AZURE_CLIENT_ID não configurado no .env")
            return False
        
        try:
            self.app = msal.PublicClientApplication(
                self.client_id,
                authority="https://login.microsoftonline.com/common"
            )
            
            # Tenta obter token do cache
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.SCOPES, account=accounts[0])
                if result and 'access_token' in result:
                    self.token = result['access_token']
                    print("✅ Conectado ao OneDrive (cache)!")
                    return True
            
            # Login interativo
            result = self.app.acquire_token_interactive(scopes=self.SCOPES)
            
            if 'access_token' in result:
                self.token = result['access_token']
                print("✅ Conectado ao OneDrive!")
                return True
            else:
                print(f"❌ Erro: {result.get('error_description')}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def _headers(self) -> Dict:
        """Headers para requisições"""
        return {'Authorization': f'Bearer {self.token}'}
    
    def listar_arquivos(self, pasta: str = "/", limite: int = 20) -> List[ArquivoCloud]:
        """Lista arquivos do OneDrive"""
        if not self.token:
            if not self.conectar():
                return []
        
        try:
            if pasta == "/":
                url = f"{self.GRAPH_URL}/me/drive/root/children"
            else:
                url = f"{self.GRAPH_URL}/me/drive/root:{pasta}:/children"
            
            params = {'$top': limite}
            response = http_requests.get(url, headers=self._headers(), params=params)
            
            if response.status_code != 200:
                print(f"❌ Erro: {response.text}")
                return []
            
            arquivos = []
            for item in response.json().get('value', []):
                arquivo = ArquivoCloud(
                    id=item['id'],
                    nome=item['name'],
                    tipo='pasta' if 'folder' in item else 'arquivo',
                    tamanho=item.get('size', 0),
                    criado_em=item.get('createdDateTime', ''),
                    modificado_em=item.get('lastModifiedDateTime', ''),
                    url=item.get('webUrl', ''),
                    provider='onedrive'
                )
                arquivos.append(arquivo)
            
            return arquivos
            
        except Exception as e:
            print(f"❌ Erro ao listar: {e}")
            return []
    
    def upload(self, arquivo_local: str, destino: str = "/") -> Optional[str]:
        """Faz upload para OneDrive"""
        if not self.token:
            if not self.conectar():
                return None
        
        if not os.path.exists(arquivo_local):
            print(f"❌ Arquivo não encontrado: {arquivo_local}")
            return None
        
        try:
            nome = os.path.basename(arquivo_local)
            
            if destino == "/":
                url = f"{self.GRAPH_URL}/me/drive/root:/{nome}:/content"
            else:
                url = f"{self.GRAPH_URL}/me/drive/root:{destino}/{nome}:/content"
            
            with open(arquivo_local, 'rb') as f:
                response = http_requests.put(
                    url,
                    headers=self._headers(),
                    data=f
                )
            
            if response.status_code in [200, 201]:
                print(f"✅ Upload concluído: {nome}")
                return response.json().get('id')
            else:
                print(f"❌ Erro: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return None
    
    def download(self, arquivo_id: str, destino: str) -> bool:
        """Baixa arquivo do OneDrive"""
        if not self.token:
            if not self.conectar():
                return False
        
        try:
            url = f"{self.GRAPH_URL}/me/drive/items/{arquivo_id}/content"
            response = http_requests.get(url, headers=self._headers())
            
            if response.status_code == 200:
                with open(destino, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Download concluído: {destino}")
                return True
            else:
                print(f"❌ Erro: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return False
    
    def criar_pasta(self, nome: str, pasta_pai: str = "/") -> Optional[str]:
        """Cria pasta no OneDrive"""
        if not self.token:
            if not self.conectar():
                return None
        
        try:
            if pasta_pai == "/":
                url = f"{self.GRAPH_URL}/me/drive/root/children"
            else:
                url = f"{self.GRAPH_URL}/me/drive/root:{pasta_pai}:/children"
            
            data = {
                'name': nome,
                'folder': {},
                '@microsoft.graph.conflictBehavior': 'rename'
            }
            
            response = http_requests.post(
                url,
                headers={**self._headers(), 'Content-Type': 'application/json'},
                json=data
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                print(f"❌ Erro: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar pasta: {e}")
            return None


class CloudStorageManager:
    """Gerenciador unificado de armazenamento em nuvem"""
    
    def __init__(self):
        self.google = GoogleDriveManager()
        self.onedrive = OneDriveManager()
        self.provider_padrao = 'google'  # Provider padrão
    
    def set_provider_padrao(self, provider: str):
        """Define provider padrão (google ou onedrive)"""
        if provider in ['google', 'onedrive']:
            self.provider_padrao = provider
    
    def listar(self, pasta: str = None, provider: str = None) -> List[ArquivoCloud]:
        """Lista arquivos"""
        provider = provider or self.provider_padrao
        
        if provider == 'google':
            return self.google.listar_arquivos(pasta)
        else:
            return self.onedrive.listar_arquivos(pasta or "/")
    
    def upload(self, arquivo_local: str, destino: str = None, 
               provider: str = None) -> Optional[str]:
        """Faz upload de arquivo"""
        provider = provider or self.provider_padrao
        
        if provider == 'google':
            return self.google.upload(arquivo_local, pasta_id=destino)
        else:
            return self.onedrive.upload(arquivo_local, destino or "/")
    
    def download(self, arquivo_id: str, destino: str, 
                 provider: str = None) -> bool:
        """Baixa arquivo"""
        provider = provider or self.provider_padrao
        
        if provider == 'google':
            return self.google.download(arquivo_id, destino)
        else:
            return self.onedrive.download(arquivo_id, destino)
    
    def criar_pasta(self, nome: str, pasta_pai: str = None,
                    provider: str = None) -> Optional[str]:
        """Cria pasta"""
        provider = provider or self.provider_padrao
        
        if provider == 'google':
            return self.google.criar_pasta(nome, pasta_pai)
        else:
            return self.onedrive.criar_pasta(nome, pasta_pai or "/")
    
    def status(self) -> Dict:
        """Retorna status das conexões"""
        return {
            'google_drive': GOOGLE_AVAILABLE,
            'onedrive': ONEDRIVE_AVAILABLE,
            'provider_padrao': self.provider_padrao
        }


# Instância global
_cloud_manager = None

def get_cloud_storage() -> CloudStorageManager:
    """Retorna instância singleton do CloudStorageManager"""
    global _cloud_manager
    if _cloud_manager is None:
        _cloud_manager = CloudStorageManager()
    return _cloud_manager
