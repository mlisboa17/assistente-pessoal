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
        """
        
        try:
            # Simula busca de e-mails (em produção, usa Gmail API)
            emails = await self._buscar_emails_gmail(user_id)
            
            if not emails:
                return """
📧 *Caixa de Entrada Vazia*

Você não tem novos e-mails! 🎉

Quando receber novos e-mails, execute /emails
e verei em tempo real para você.
"""
            
            # 🆕 APLICAR FILTROS
            filtros = self.filtros_usuario.get(user_id, {})
            emails = self._aplicar_filtros_emails(emails, filtros)
            
            if not emails:
                return f"""
📧 *Nenhum e-mail encontrado*

Com os filtros:
• Quantidade: {filtros.get('quantidade', 10)}
• Categoria: {filtros.get('categoria', 'Todas')}
• Remetente: {filtros.get('remetente', 'Qualquer um')}

💡 Tente:
/reset - Resetar filtros
/emails - Voltar ao menu
"""
            
            total = len(emails)
            self.progresso_leitura[user_id]['total'] = total
            
            # 🆕 Construir resposta progressiva
            resposta = self._montar_resposta_emails(user_id, emails)
            
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
    
    def _montar_resposta_emails(self, user_id: str, emails: List[Email]) -> str:
        """
        Monta resposta com:
        - Indicador de progresso
        - Filtros aplicados
        - Resumos dos e-mails
        - Botões interativos
        """
        
        total = len(emails)
        progresso = self.progresso_leitura[user_id]
        filtros = self.filtros_usuario.get(user_id, {})
        
        # 🆕 Barra de progresso visual
        barra = self._gerar_barra_progresso(total, total)
        
        resposta = f"""
📧 *Leitura de E-mails* {barra}

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
        
        # Agrupar por categoria
        por_categoria = self._agrupar_por_categoria(emails)
        
        # 🆕 Mostrar cada categoria com resumos
        for categoria, emails_cat in por_categoria.items():
            resposta += f"\n{self._icone_categoria(categoria)} *{categoria.upper()}* ({len(emails_cat)})\n"
            
            for i, email in enumerate(emails_cat[:3], 1):  # Primeiros 3 de cada
                resposta += f"{i}. 📬 {email.assunto[:50]}\n"
                resposta += f"   De: {email.de}\n"
                if email.resumo:
                    resposta += f"   📝 {email.resumo[:80]}...\n"
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

📊 *Resumo por categoria:*
"""
        
        for categoria, emails_cat in por_categoria.items():
            resposta += f"• {categoria}: {len(emails_cat)}\n"
        
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
        Busca e-mails do Gmail com progresso
        Em produção, integraria com Gmail API
        """
        
        # 🆕 Simula busca de e-mails
        # Em produção, seria:
        # credentials = self.google_auth.get_credentials(user_id)
        # service = self.google_auth.get_gmail_service(credentials)
        # results = service.users().messages().list(userId='me', maxResults=10).execute()
        
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
