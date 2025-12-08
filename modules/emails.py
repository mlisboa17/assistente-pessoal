"""
📧 Módulo de E-mails
Gerencia integração com Gmail, Outlook e outros
Com suporte a:
- Leitura em tempo real com progresso
- Resumo automático enquanto lê
- Interface interativa durante processamento
"""
import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


@dataclass
class Email:
    """Representa um e-mail"""
    id: str
    de: str
    para: str
    assunto: str
    corpo: str
    data: str
    lido: bool = False
    anexos: List[str] = None
    resumo: str = ""  # 🆕 Resumo gerado
    categoria: str = ""  # 🆕 Categoria detectada


class TipoEmail(Enum):
    """Categorias de e-mail"""
    TRABALHO = "trabalho"
    PESSOAL = "pessoal"
    NOTIFICACAO = "notificacao"
    PROMOTIONAL = "promotionaln"
    SPAM = "spam"
    IMPORTANTE = "importante"
    OUTROS = "outros"


class EmailModule:
    """Gerenciador de E-mails com suporte a streaming e interatividade"""
    
    # Keywords para categorização automática
    KEYWORDS_CATEGORIA = {
        'trabalho': ['reunião', 'trabalho', 'projeto', 'deadline', 'cliente', 'empresa', 'profissional'],
        'importante': ['urgente', 'importante', 'atenção', 'crítico', 'imediato', 'prioridade'],
        'pessoal': ['amigo', 'família', 'pessoal', 'convite', 'aniversário', 'festa'],
        'notificacao': ['confirmação', 'recebimento', 'aviso', 'alerta', 'notificação', 'status'],
        'promotional': ['desconto', 'oferta', 'promoção', 'compre', 'venda', 'cupom', 'frete grátis'],
    }
    
    def __init__(self):
        self.gmail_configured = False
        self.outlook_configured = False
        self.google_auth = None  # Será injetado
        
        # Verifica configurações
        if os.getenv('GOOGLE_CLIENT_ID'):
            self.gmail_configured = True
        
        if os.getenv('AZURE_CLIENT_ID'):
            self.outlook_configured = True
        
        # Cache de e-mails (para não reprocessar)
        self.emails_cache: Dict[str, List[Email]] = {}
        
        # Rastreador de progresso
        self.progresso_leitura: Dict[str, Dict] = {}
        
        # 🆕 Configurações de filtro por usuário
        self.filtros_usuario: Dict[str, Dict] = {}
    
    def set_google_auth(self, auth_module):
        """Define o módulo de autenticação Google"""
        self.google_auth = auth_module
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de e-mail"""
        
        if not self.gmail_configured and not self.outlook_configured:
            return """
📧 *Módulo de E-mails*

⚠️ Nenhuma conta configurada.

Para configurar:
1. Gmail: Configure GOOGLE_CLIENT_ID no .env
2. Outlook: Configure AZURE_CLIENT_ID no .env

Consulte a documentação para mais detalhes.
"""
        
        if command == 'emails':
            # 🆕 Retorna menu inicial com opções de filtro
            return await self._listar_emails_stream(user_id)
        
        # 🆕 Comandos de quantidade
        elif command in ['5emails', '10emails', '20emails', 'todos']:
            return await self._aplicar_filtro(user_id, command)
        
        # 🆕 Comandos de categoria
        elif command in ['importante', 'trabalho', 'pessoal', 'notificacoes', 'promotional']:
            return await self._aplicar_filtro(user_id, command)
        
        # 🆕 Comando de remetente
        elif command.startswith('de:'):
            return await self._aplicar_filtro(user_id, command)
        
        elif command == 'email':
            if args:
                return await self._buscar_email(user_id, ' '.join(args))
            return await self._listar_emails_stream(user_id)
        
        elif command == 'inbox':
            return await self._listar_emails_stream(user_id)
        
        elif command == 'parar':
            # 🆕 Permite interrupção da leitura
            return await self._parar_leitura(user_id)
        
        elif command == 'reset':
            # 🆕 Reseta filtros e mostra menu novamente
            if user_id in self.filtros_usuario:
                del self.filtros_usuario[user_id]
            return await self._listar_emails_stream(user_id)
        
        elif command == 'procurar_tudo':
            # 🆕 Procura em TODAS as pastas quando não acha na INBOX
            return await self._procurar_todas_pastas(user_id)
        
        return """
📧 *Comandos de E-mail:*

🎯 Quantidade:
/5emails /10emails /20emails /todos

📂 Categoria:
/importante /trabalho /pessoal /notificacoes

🔍 Remetente:
/de:email@dominio.com

🔧 Controle:
/emails - Menu inicial
/procurar_tudo - Procurar em todas as pastas
/parar - Parar leitura
/reset - Resetar filtros
"""
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        return await self._listar_emails_stream(user_id)
    
    async def _listar_emails_stream(self, user_id: str) -> str:
        """
        Lista e-mails com opções de filtro
        Pergunta ao usuário:
        - Quantos e-mails verificar?
        - Qual categoria?
        - De qual remetente?
        """
        
        try:
            # Verifica se há autenticação Google
            if not self.google_auth:
                return """
📧 *Leitura de E-mails*

⚠️ Autenticação não disponível.

Configure:
1. /login - Autentique com Google
2. /emails - Leia seus e-mails

Depois você pode:
✅ Ver e-mails com progresso em tempo real
✅ Receber resumos automáticos
✅ Interagir enquanto lê (/parar, /mais, etc)
"""
            
            # 🆕 PERGUNTA INICIAL: Quantos e-mails verificar?
            if user_id not in self.filtros_usuario:
                return self._gerar_menu_inicial(user_id)
            
            # Se já tem filtros definidos, processa
            return await self._processar_emails_progressivo(user_id)
            
        except Exception as e:
            print(f"❌ Erro ao listar e-mails: {e}")
            return f"❌ Erro ao acessar e-mails: {str(e)}"
    
    def _gerar_menu_inicial(self, user_id: str) -> str:
        """
        Gera menu inicial com opções de filtro
        Pergunta quantos e-mails e de qual categoria
        """
        return """
📧 *Configuração de Leitura de E-mails*

🎯 *Quantos e-mails você quer verificar?*

/5emails    - Apenas 5 e-mails (rápido ⚡)
/10emails   - 10 e-mails (padrão)
/20emails   - 20 e-mails (completo)
/todos      - Todos os e-mails

─────────────────────────────────
📂 *Ou filtrar por categoria:*

🔴 /importante     - Apenas IMPORTANTES
💼 /trabalho       - Apenas TRABALHO
👤 /pessoal        - Apenas PESSOAL
🔔 /notificacoes   - Apenas NOTIFICAÇÕES

─────────────────────────────────
🔍 *Ou buscar por remetente:*

/de:email@empresa.com
/de:amigo@gmail.com

─────────────────────────────────
💡 *Exemplos:*
"/10emails" + depois "/importante"
"/de:chefe@empresa.com"
"/trabalho" para ver só e-mails de trabalho
"""
    
    async def _aplicar_filtro(self, user_id: str, comando: str) -> str:
        """
        Aplica filtro do usuário e inicia leitura
        """
        self.filtros_usuario[user_id] = {
            'quantidade': 10,
            'categoria': None,
            'remetente': None,
            'aplicado_em': datetime.now()
        }
        
        # Parseia comando
        if 'emails' in comando:
            # /5emails, /10emails, /20emails
            num = ''.join(filter(str.isdigit, comando))
            if num:
                self.filtros_usuario[user_id]['quantidade'] = int(num)
        
        elif comando.startswith('de:'):
            # /de:email@example.com
            email_remetente = comando[3:].strip()
            self.filtros_usuario[user_id]['remetente'] = email_remetente
        
        else:
            # /importante, /trabalho, /pessoal, etc
            self.filtros_usuario[user_id]['categoria'] = comando.lstrip('/')
        
        # 🆕 Inicializa rastreador de progresso
        self.progresso_leitura[user_id] = {
            'total': 0,
            'processados': 0,
            'parado': False,
            'emails': [],
            'filtros': self.filtros_usuario[user_id],
            'inicio': datetime.now()
        }
        
        # Processa com os filtros
        return await self._processar_emails_progressivo(user_id)
    
    async def _processar_emails_progressivo(self, user_id: str) -> str:
        """
        Processa e-mails com progresso e resumo em tempo real
        Aplica filtros do usuário (quantidade, categoria, remetente)
        
        🆕 LÓGICA:
        1. Busca PRIMEIRO apenas INBOX
        2. Se não achar, pergunta se quer procurar em outras pastas
        3. Se encontrar algo em SPAM, avisa ao usuário
        """
        
        try:
            # 🆕 Busca APENAS INBOX (pasta principal)
            emails = await self._buscar_emails_inbox(user_id)
            
            if not emails:
                # Nenhum e-mail na INBOX
                return """
📧 *Caixa de Entrada Vazia*

Você não tem novos e-mails na INBOX! 🎉

💡 Quer que eu procure nas outras pastas?
/procurar_tudo - Procurar em ENVIADOS, ARQUIVO, RASCUNHOS, etc
/reset - Voltar ao menu
"""
            
            # 🆕 APLICAR FILTROS
            filtros = self.filtros_usuario.get(user_id, {})
            emails = self._aplicar_filtros_emails(emails, filtros)
            
            if not emails:
                return f"""
📧 *Nenhum e-mail encontrado na INBOX*

Com os filtros:
• Quantidade: {filtros.get('quantidade', 10)}
• Categoria: {filtros.get('categoria', 'Todas')}
• Remetente: {filtros.get('remetente', 'Qualquer um')}

💡 Tente:
/reset - Resetar filtros
/procurar_tudo - Procurar em outras pastas
/emails - Voltar ao menu
"""
            
            total = len(emails)
            self.progresso_leitura[user_id]['total'] = total
            
            # 🆕 Construir resposta progressiva (apenas INBOX)
            resposta = self._montar_resposta_emails(user_id, emails, pasta_filtro="📥 INBOX")
            
            return resposta
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return f"❌ Erro ao processar e-mails: {str(e)}"
    
    def _aplicar_filtros_emails(self, emails: List[Email], filtros: Dict) -> List[Email]:
        """
        Aplica filtros aos e-mails
        - Quantidade máxima
        - Categoria
        - Remetente
        """
        emails_filtrados = emails.copy()
        
        # 🆕 Filtro por remetente
        if filtros.get('remetente'):
            remetente = filtros['remetente'].lower()
            emails_filtrados = [
                e for e in emails_filtrados 
                if remetente in e.de.lower()
            ]
        
        # 🆕 Filtro por categoria
        if filtros.get('categoria'):
            categoria = filtros['categoria'].lower()
            emails_filtrados = [
                e for e in emails_filtrados 
                if e.categoria.lower() == categoria
            ]
        
        # 🆕 Limitar quantidade
        quantidade = filtros.get('quantidade', 10)
        if isinstance(quantidade, int):
            emails_filtrados = emails_filtrados[:quantidade]
        
        return emails_filtrados
    
    def _montar_resposta_emails(self, user_id: str, emails: List[Email], pasta_filtro: str = None) -> str:
        """
        Monta resposta com:
        - Indicador de progresso
        - Filtros aplicados
        - E-mails agrupados por PASTA (ou apenas uma pasta se filtrado)
        - Resumos dos e-mails
        - Botões interativos
        """
        
        total = len(emails)
        progresso = self.progresso_leitura[user_id]
        filtros = self.filtros_usuario.get(user_id, {})
        
        # 🆕 Barra de progresso visual
        barra = self._gerar_barra_progresso(total, total)
        
        # 🆕 Título dinâmico baseado na pasta
        titulo = pasta_filtro if pasta_filtro else "📧 *Leitura de E-mails - TODAS AS PASTAS*"
        
        resposta = f"""
{titulo} {barra}

🔄 Total: {total} e-mail(is) para ler
"""
        
        # 🆕 Mostrar filtros aplicados
        if filtros:
            resposta += "\n🔍 *Filtros Aplicados:*\n"
            if filtros.get('quantidade'):
                resposta += f"  • Quantidade: {filtros['quantidade']}\n"
            if filtros.get('categoria'):
                resposta += f"  • Categoria: {filtros['categoria'].upper()}\n"
            if filtros.get('remetente'):
                resposta += f"  • Remetente: {filtros['remetente']}\n"
            resposta += "\n"
        
        # 🆕 Agrupar por PASTA
        por_pasta = self._agrupar_por_pasta(emails)
        
        # 🆕 Mostrar cada pasta com seus e-mails
        for pasta, emails_pasta in sorted(por_pasta.items()):
            resposta += f"\n{pasta} ({len(emails_pasta)})\n"
            resposta += "─" * 40 + "\n"
            
            # Agrupar por categoria dentro da pasta
            por_categoria_pasta = {}
            for email in emails_pasta:
                cat = self._detectar_categoria(email)
                if cat not in por_categoria_pasta:
                    por_categoria_pasta[cat] = []
                por_categoria_pasta[cat].append(email)
            
            # Mostrar por categoria dentro da pasta
            for categoria, emails_cat in por_categoria_pasta.items():
                resposta += f"  {self._icone_categoria(categoria)} {categoria.upper()} ({len(emails_cat)})\n"
                
                for i, email in enumerate(emails_cat[:2], 1):  # Primeiros 2 de cada
                    resposta += f"    {i}. 📬 {email.assunto[:50]}\n"
                    resposta += f"       De: {email.de}\n"
                    if email.resumo:
                        resposta += f"       📝 {email.resumo[:70]}...\n"
                    resposta += "\n"
        
        # 🆕 Botões interativos
        resposta += """
─────────────────────────────────
🎯 *Opções:*
/mais - Ver mais e-mails
/importante - Filtrar importantes
/trabalho - Filtrar trabalho
/pessoal - Filtrar pessoal
/5emails - Ver apenas 5
/10emails - Ver 10
/20emails - Ver 20
/parar - Parar a leitura
/reset - Resetar filtros

📊 *Resumo por Pasta:*
"""
        
        for pasta, emails_pasta in sorted(por_pasta.items()):
            resposta += f"{pasta}: {len(emails_pasta)}\n"
        
        resposta += f"""
─────────────────────────────────
⏱️ Tempo: {self._calcular_tempo_decorrido(user_id)}
✅ Pronto para interagir!
"""
        
        return resposta
    
    def _gerar_barra_progresso(self, processados: int, total: int) -> str:
        """Gera barra de progresso visual"""
        if total == 0:
            return "[░░░░░░░░░░] 0%"
        
        percentual = (processados / total) * 100
        blocos = int(percentual / 10)
        
        barra = "█" * blocos + "░" * (10 - blocos)
        return f"[{barra}] {int(percentual)}%"
    
    def _agrupar_por_categoria(self, emails: List[Email]) -> Dict[str, List[Email]]:
        """Agrupa e-mails por categoria"""
        grupos = {}
        
        for email in emails:
            categoria = self._detectar_categoria(email)
            email.categoria = categoria
            
            if categoria not in grupos:
                grupos[categoria] = []
            grupos[categoria].append(email)
        
        return grupos
    
    def _detectar_pasta(self, email_id: str) -> str:
        """
        🆕 Detecta em qual pasta do Gmail o e-mail está
        """
        # Baseado no ID do e-mail
        if email_id.startswith('inbox_'):
            return '📥 INBOX'
        elif email_id.startswith('sent_'):
            return '📤 ENVIADOS'
        elif email_id.startswith('archive_'):
            return '🗂️ ARQUIVO'
        elif email_id.startswith('draft_'):
            return '📝 RASCUNHOS'
        elif email_id.startswith('spam_'):
            return '🚫 SPAM'
        elif email_id.startswith('trash_'):
            return '🗑️ LIXO'
        else:
            return '📬 OUTROS'
    
    def _agrupar_por_pasta(self, emails: List[Email]) -> Dict[str, List[Email]]:
        """
        🆕 Agrupa e-mails por pasta (INBOX, SENT, ARCHIVE, etc)
        """
        grupos = {}
        
        for email in emails:
            pasta = self._detectar_pasta(email.id)
            
            if pasta not in grupos:
                grupos[pasta] = []
            grupos[pasta].append(email)
        
        return grupos
    
    def _detectar_categoria(self, email: Email) -> str:
        """Detecta categoria do e-mail"""
        texto = f"{email.assunto} {email.corpo}".lower()
        
        melhor_categoria = "outros"
        melhor_score = 0
        
        for categoria, keywords in self.KEYWORDS_CATEGORIA.items():
            score = sum(1 for kw in keywords if kw in texto)
            if score > melhor_score:
                melhor_score = score
                melhor_categoria = categoria
        
        return melhor_categoria
    
    def _icone_categoria(self, categoria: str) -> str:
        """Retorna ícone para categoria"""
        icones = {
            'importante': '🔴',
            'trabalho': '💼',
            'pessoal': '👤',
            'notificacao': '🔔',
            'promotional': '🛍️',
            'spam': '🚫',
            'outros': '📬'
        }
        return icones.get(categoria, '📬')
    
    def _calcular_tempo_decorrido(self, user_id: str) -> str:
        """Calcula tempo decorrido desde inicio"""
        progresso = self.progresso_leitura.get(user_id)
        if not progresso:
            return "0s"
        
        tempo = (datetime.now() - progresso['inicio']).total_seconds()
        
        if tempo < 60:
            return f"{int(tempo)}s"
        else:
            return f"{int(tempo/60)}m {int(tempo%60)}s"
    
    async def _buscar_emails_gmail(self, user_id: str) -> List[Email]:
        """
        Busca e-mails do Gmail de TODAS as pastas
        Em produção, integraria com Gmail API em múltiplas pastas
        """
        
        # 🆕 Simula busca de e-mails em múltiplas pastas
        # Em produção, seria:
        # credentials = self.google_auth.get_credentials(user_id)
        # service = self.google_auth.get_gmail_service(credentials)
        # 
        # PASTAS_GMAIL = ['INBOX', 'SENT', 'DRAFTS', 'ARCHIVE', 'TRASH']
        # all_emails = []
        # for pasta in PASTAS_GMAIL:
        #     results = service.users().messages().list(
        #         userId='me',
        #         labelIds=LABEL_MAP[pasta],
        #         maxResults=100
        #     ).execute()
        #     for msg in results.get('messages', []):
        #         email = service.users().messages().get(
        #             userId='me',
        #             id=msg['id']
        #         ).execute()
        #         all_emails.append(parse_email(email))
        
        # Por enquanto, retorna exemplo estruturado
        emails_simulados = [
            Email(
                id="1",
                de="chefe@empresa.com",
                para="voce@gmail.com",
                assunto="Reunião urgente hoje às 14:00 - Projeto X",
                corpo="Preciso discutir os últimos desenvolvimentos do projeto X. Será uma reunião curta mas importante.",
                data=datetime.now().isoformat(),
                resumo="Reunião urgente sobre projeto X hoje às 14h",
                categoria="trabalho"
            ),
            Email(
                id="2",
                de="noreply@amazon.com.br",
                para="voce@gmail.com",
                assunto="📦 Seu pedido foi entregue!",
                corpo="Seu pedido chegou! Aproveite a entrega e acompanhe nos próximos passos.",
                data=(datetime.now() - timedelta(hours=2)).isoformat(),
                resumo="Pedido Amazon entregue",
                categoria="notificacao"
            ),
            Email(
                id="3",
                de="amigo@hotmail.com",
                para="voce@gmail.com",
                assunto="Ô, bora tomar um café no fim de semana?",
                corpo="Tá afim de tomar um café comigo no sábado? Tem um lugar novo que quero te mostrar.",
                data=(datetime.now() - timedelta(hours=5)).isoformat(),
                resumo="Convite para café no sábado",
                categoria="pessoal"
            ),
            Email(
                id="4",
                de="noreply@shopee.com.br",
                para="voce@gmail.com",
                assunto="🎉 MEGA DESCONTO: Até 70% de desconto em eletrônicos!",
                corpo="Aproveite esta oferta especial! Eletrônicos com até 70% de desconto. Válido por poucas horas!",
                data=(datetime.now() - timedelta(hours=8)).isoformat(),
                resumo="Promoção eletrônicos 70% desconto",
                categoria="promotional"
            ),
            Email(
                id="5",
                de="banco@bancoxx.com.br",
                para="voce@gmail.com",
                assunto="⚠️ Alerta de Segurança: Acesso Não Autorizado",
                corpo="Detectamos uma tentativa de acesso à sua conta. Se não foi você, clique aqui para verificar.",
                data=(datetime.now() - timedelta(hours=12)).isoformat(),
                resumo="Alerta de segurança - verificar imediatamente",
                categoria="importante"
            ),
        ]
        
        # Simula leitura progressiva com delay
        for i, email in enumerate(emails_simulados):
            if user_id in self.progresso_leitura:
                if self.progresso_leitura[user_id]['parado']:
                    break
                
                # Simula tempo de leitura
                self.progresso_leitura[user_id]['processados'] = i + 1
                await asyncio.sleep(0.5)  # Simula processamento
        
        return emails_simulados
    
    async def _buscar_emails_inbox(self, user_id: str) -> List[Email]:
        """
        🆕 Busca e-mails APENAS da INBOX (pasta principal)
        
        Esta é a busca padrão. Se não achar nada,
        pergunta ao usuário se quer procurar em outras pastas.
        """
        
        emails_inbox = [
            Email(
                id="inbox_1",
                de="chefe@empresa.com",
                para="voce@gmail.com",
                assunto="Reunião urgente hoje às 14:00 - Projeto X",
                corpo="Preciso discutir os últimos desenvolvimentos do projeto X. Será uma reunião curta mas importante.",
                data=datetime.now().isoformat(),
                resumo="Reunião urgente sobre projeto X hoje às 14h",
                categoria="trabalho"
            ),
            Email(
                id="inbox_2",
                de="noreply@amazon.com.br",
                para="voce@gmail.com",
                assunto="📦 Seu pedido foi entregue!",
                corpo="Seu pedido chegou! Aproveite a entrega e acompanhe nos próximos passos.",
                data=(datetime.now() - timedelta(hours=2)).isoformat(),
                resumo="Pedido Amazon entregue",
                categoria="notificacao"
            ),
            Email(
                id="inbox_3",
                de="amigo@hotmail.com",
                para="voce@gmail.com",
                assunto="Ô, bora tomar um café no fim de semana?",
                corpo="Tá afim de tomar um café comigo no sábado? Tem um lugar novo que quero te mostrar.",
                data=(datetime.now() - timedelta(hours=5)).isoformat(),
                resumo="Convite para café no sábado",
                categoria="pessoal"
            ),
            Email(
                id="inbox_4",
                de="noreply@shopee.com.br",
                para="voce@gmail.com",
                assunto="🎉 MEGA DESCONTO: Até 70% de desconto em eletrônicos!",
                corpo="Aproveite esta oferta especial! Eletrônicos com até 70% de desconto. Válido por poucas horas!",
                data=(datetime.now() - timedelta(hours=8)).isoformat(),
                resumo="Promoção eletrônicos 70% desconto",
                categoria="promotional"
            ),
            Email(
                id="inbox_5",
                de="banco@bancoxx.com.br",
                para="voce@gmail.com",
                assunto="⚠️ Alerta de Segurança: Acesso Não Autorizado",
                corpo="Detectamos uma tentativa de acesso à sua conta. Se não foi você, clique aqui para verificar.",
                data=(datetime.now() - timedelta(hours=12)).isoformat(),
                resumo="Alerta de segurança - verificar imediatamente",
                categoria="importante"
            ),
        ]
        
        # Simula leitura progressiva
        for i, email in enumerate(emails_inbox):
            if user_id in self.progresso_leitura:
                if self.progresso_leitura[user_id]['parado']:
                    break
                
                self.progresso_leitura[user_id]['processados'] = i + 1
                await asyncio.sleep(0.5)
        
        return emails_inbox
    
    async def _buscar_emails_todas_pastas(self, user_id: str) -> List[Email]:
        """
        🆕 Busca e-mails de TODAS as pastas do Gmail
        
        Em produção, busca em:
        - INBOX (principal)
        - SENT (enviados)
        - DRAFTS (rascunhos)
        - ARCHIVE (arquivo)
        - TRASH (lixo)
        - SPAM (spam)
        - LABELS (etiquetas customizadas)
        """
        
        # 🆕 Lista completa de e-mails de todas as pastas
        emails_todas_pastas = [
            # ========== INBOX ==========
            Email(
                id="inbox_1",
                de="chefe@empresa.com",
                para="voce@gmail.com",
                assunto="Reunião urgente hoje às 14:00 - Projeto X",
                corpo="Preciso discutir os últimos desenvolvimentos do projeto X. Será uma reunião curta mas importante.",
                data=datetime.now().isoformat(),
                resumo="Reunião urgente sobre projeto X hoje às 14h",
                categoria="trabalho"
            ),
            Email(
                id="inbox_2",
                de="noreply@amazon.com.br",
                para="voce@gmail.com",
                assunto="📦 Seu pedido foi entregue!",
                corpo="Seu pedido chegou! Aproveite a entrega e acompanhe nos próximos passos.",
                data=(datetime.now() - timedelta(hours=2)).isoformat(),
                resumo="Pedido Amazon entregue",
                categoria="notificacao"
            ),
            Email(
                id="inbox_3",
                de="amigo@hotmail.com",
                para="voce@gmail.com",
                assunto="Ô, bora tomar um café no fim de semana?",
                corpo="Tá afim de tomar um café comigo no sábado? Tem um lugar novo que quero te mostrar.",
                data=(datetime.now() - timedelta(hours=5)).isoformat(),
                resumo="Convite para café no sábado",
                categoria="pessoal"
            ),
            Email(
                id="inbox_4",
                de="noreply@shopee.com.br",
                para="voce@gmail.com",
                assunto="🎉 MEGA DESCONTO: Até 70% de desconto em eletrônicos!",
                corpo="Aproveite esta oferta especial! Eletrônicos com até 70% de desconto. Válido por poucas horas!",
                data=(datetime.now() - timedelta(hours=8)).isoformat(),
                resumo="Promoção eletrônicos 70% desconto",
                categoria="promotional"
            ),
            Email(
                id="inbox_5",
                de="banco@bancoxx.com.br",
                para="voce@gmail.com",
                assunto="⚠️ Alerta de Segurança: Acesso Não Autorizado",
                corpo="Detectamos uma tentativa de acesso à sua conta. Se não foi você, clique aqui para verificar.",
                data=(datetime.now() - timedelta(hours=12)).isoformat(),
                resumo="Alerta de segurança - verificar imediatamente",
                categoria="importante"
            ),
            
            # ========== SENT (ENVIADOS) ==========
            Email(
                id="sent_1",
                de="voce@gmail.com",
                para="chefe@empresa.com",
                assunto="RE: Reunião urgente hoje às 14:00",
                corpo="Confirmado! Estarei lá pontualmente. Muito obrigado pelas informações antecipadas.",
                data=(datetime.now() - timedelta(days=1)).isoformat(),
                resumo="Confirmação de reunião enviada",
                categoria="trabalho"
            ),
            Email(
                id="sent_2",
                de="voce@gmail.com",
                para="amigo@hotmail.com",
                assunto="RE: Café no sábado",
                corpo="Ótimo! Adoraria ir! Que horas e em qual lugar?",
                data=(datetime.now() - timedelta(days=2)).isoformat(),
                resumo="Confirmação de encontro enviada",
                categoria="pessoal"
            ),
            
            # ========== ARCHIVE (ARQUIVO) ==========
            Email(
                id="archive_1",
                de="cliente@empresa-xyz.com",
                para="voce@gmail.com",
                assunto="Feedback do projeto anterior - Muito bom!",
                corpo="Apenas queria parabenizá-lo pelo excelente trabalho realizado. O projeto ficou ótimo!",
                data=(datetime.now() - timedelta(days=7)).isoformat(),
                resumo="Feedback positivo de cliente",
                categoria="importante"
            ),
            Email(
                id="archive_2",
                de="rh@empresa.com",
                para="voce@gmail.com",
                assunto="Comunicado: Novo horário de trabalho a partir de janeiro",
                corpo="Informamos que a partir de janeiro o horário de trabalho será das 8h às 17h.",
                data=(datetime.now() - timedelta(days=14)).isoformat(),
                resumo="Novo horário de trabalho",
                categoria="notificacao"
            ),
            
            # ========== DRAFTS (RASCUNHOS) ==========
            Email(
                id="draft_1",
                de="voce@gmail.com",
                para="gerente@empresa.com",
                assunto="[RASCUNHO] Proposta de aumento de orçamento",
                corpo="Olá, gostaria de propor um aumento de 15% no orçamento para o próximo trimestre...",
                data=(datetime.now() - timedelta(hours=3)).isoformat(),
                resumo="Rascunho: proposta de orçamento",
                categoria="trabalho"
            ),
            
            # ========== SPAM ==========
            Email(
                id="spam_1",
                de="noreply@viagra-melhor-preco.com",
                para="voce@gmail.com",
                assunto="ASSINE JÁ!!! Medicamentos com 90% de desconto!!",
                corpo="Compre agora! Não perca! Envio grátis para todo o Brasil!",
                data=(datetime.now() - timedelta(days=1)).isoformat(),
                resumo="Spam: medicamentos",
                categoria="spam"
            ),
            Email(
                id="spam_2",
                de="noreply@loteria-milionaria.com",
                para="voce@gmail.com",
                assunto="🎰 PARABÉNS!!! Você ganhou 1 MILHÃO DE REAIS!",
                corpo="Clique aqui para resgatar seu prêmio de 1 milhão de reais!",
                data=(datetime.now() - timedelta(days=2)).isoformat(),
                resumo="Spam: fraude loteria",
                categoria="spam"
            ),
        ]
        
        # Simula leitura progressiva de todas as pastas
        for i, email in enumerate(emails_todas_pastas):
            if user_id in self.progresso_leitura:
                if self.progresso_leitura[user_id]['parado']:
                    break
                
                # Simula tempo de leitura
                self.progresso_leitura[user_id]['processados'] = i + 1
                await asyncio.sleep(0.3)  # Simula processamento mais rápido
        
        return emails_todas_pastas
    
    async def _parar_leitura(self, user_id: str) -> str:
        """Permite ao usuário parar a leitura de e-mails"""
        if user_id in self.progresso_leitura:
            self.progresso_leitura[user_id]['parado'] = True
        
        return """
⏸️ *Leitura Parada*

A leitura de e-mails foi interrompida.

Você pode:
✅ Continuar lendo mais tarde
✅ /mais - Ver próximos e-mails
✅ /importante - Filtrar apenas importantes
✅ /emails - Recomeçar do zero
"""
    
    async def _procurar_todas_pastas(self, user_id: str) -> str:
        """
        🆕 Procura em TODAS as pastas quando não achou na INBOX
        Busca em: ENVIADOS, ARQUIVO, RASCUNHOS, SPAM, LIXO, etc
        Avisa se encontra algo no SPAM
        """
        
        # Busca em todas as pastas
        emails_todas = await self._buscar_emails_todas_pastas(user_id)
        
        if not emails_todas:
            return """
📧 *Nenhum E-mail Encontrado*

Procuramos em:
• 📥 INBOX
• 📤 ENVIADOS
• 🗂️ ARQUIVO
• 📝 RASCUNHOS
• 🚫 SPAM
• 🗑️ LIXO

E não encontramos nenhum e-mail! 😅

💡 Dica: Configure um filtro:
/importante - Ver só importante
/trabalho - Ver só trabalho
/emails - Menu inicial
"""
        
        # Aplicar filtros se existirem
        filtros = self.filtros_usuario.get(user_id, {})
        emails = self._aplicar_filtros_emails(emails_todas, filtros)
        
        if not emails:
            return f"""
📧 *Nenhum e-mail encontrado com os filtros*

Procuramos em TODAS as pastas:
• 📥 INBOX
• 📤 ENVIADOS
• 🗂️ ARQUIVO
• 📝 RASCUNHOS
• 🚫 SPAM
• 🗑️ LIXO

Mas nenhum corresponde aos filtros:
• Quantidade: {filtros.get('quantidade', 10)}
• Categoria: {filtros.get('categoria', 'Todas')}
• Remetente: {filtros.get('remetente', 'Qualquer um')}

💡 Tente:
/reset - Resetar filtros
/procurar_tudo - Procurar sem filtros
"""
        
        total = len(emails)
        self.progresso_leitura[user_id]['total'] = total
        
        # 🆕 Preparar resposta agrupada por pasta
        resposta = self._montar_resposta_emails_com_pastas(user_id, emails)
        
        return resposta
    
    def _montar_resposta_emails_com_pastas(self, user_id: str, emails: List[Email]) -> str:
        """
        🆕 Monta resposta mostrando e-mails de TODAS as pastas
        E avisa se algum veio do SPAM
        """
        
        total = len(emails)
        progresso = self.progresso_leitura.get(user_id, {'inicio': datetime.now()})
        filtros = self.filtros_usuario.get(user_id, {})
        
        barra = self._gerar_barra_progresso(total, total)
        
        resposta = f"""
📧 *Leitura de E-mails - TODAS AS PASTAS* {barra}

🔄 Total: {total} e-mail(is)
"""
        
        # Mostrar filtros se aplicados
        if filtros:
            resposta += "\n🔍 *Filtros Aplicados:*\n"
            if filtros.get('quantidade'):
                resposta += f"  • Quantidade: {filtros['quantidade']}\n"
            if filtros.get('categoria'):
                resposta += f"  • Categoria: {filtros['categoria'].upper()}\n"
            if filtros.get('remetente'):
                resposta += f"  • Remetente: {filtros['remetente']}\n"
            resposta += "\n"
        
        # Agrupar por pasta
        por_pasta = self._agrupar_por_pasta(emails)
        
        # 🆕 Variável para rastrear SPAMs encontrados
        spam_encontrados = []
        
        # Mostrar cada pasta
        for pasta, emails_pasta in sorted(por_pasta.items()):
            resposta += f"\n{pasta} ({len(emails_pasta)})\n"
            resposta += "─" * 40 + "\n"
            
            # Agrupar por categoria dentro da pasta
            por_categoria = {}
            for email in emails_pasta:
                cat = self._detectar_categoria(email)
                if cat not in por_categoria:
                    por_categoria[cat] = []
                por_categoria[cat].append(email)
                
                # 🆕 Rastrear SPAMs
                if pasta == "🚫 SPAM":
                    spam_encontrados.append(email)
            
            # Mostrar categorias dentro da pasta
            for categoria, emails_cat in por_categoria.items():
                resposta += f"  {self._icone_categoria(categoria)} {categoria.upper()} ({len(emails_cat)})\n"
                
                for i, email in enumerate(emails_cat[:2], 1):
                    resposta += f"    {i}. 📬 {email.assunto[:50]}\n"
                    resposta += f"       De: {email.de}\n"
                    if email.resumo:
                        resposta += f"       📝 {email.resumo[:70]}...\n"
                    resposta += "\n"
        
        # 🆕 AVISO SE ENCONTROU ALGO NO SPAM
        if spam_encontrados:
            resposta += """
⚠️ *ATENÇÃO - E-mails no SPAM:*
"""
            for email in spam_encontrados:
                resposta += f"  🚫 {email.assunto[:50]}\n"
                resposta += f"     De: {email.de}\n"
            resposta += """
💡 Verifique o SPAM - pode ter e-mails importantes marcados incorretamente!
/importante - Ver apenas importantes
/parar - Parar a leitura
"""
        
        # Botões interativos
        resposta += """
─────────────────────────────────
🎯 *Opções:*
/importante - Filtrar importantes
/trabalho - Filtrar trabalho
/pessoal - Filtrar pessoal
/5emails - Ver apenas 5
/10emails - Ver 10
/20emails - Ver 20
/parar - Parar leitura
/reset - Resetar filtros
/emails - Menu inicial

─────────────────────────────────
⏱️ Tempo: """ + self._calcular_tempo_decorrido(user_id) + """
✅ Pronto para interagir!
"""
        
        return resposta
    
    async def _buscar_email(self, user_id: str, termo: str) -> str:
        """Busca e-mails por termo com indicador de progresso"""
        
        return f"""
🔍 *Buscando:* "{termo}"

🔄 Procurando por: {termo}...

💡 Dica: Você pode usar filtros como:
• /importante - Apenas e-mails importantes
• /de:chefe@empresa.com - De um remetente específico
• /assunto:reunião - Com palavra específica no assunto

Ou continue assistindo a leitura completa com /emails
"""
