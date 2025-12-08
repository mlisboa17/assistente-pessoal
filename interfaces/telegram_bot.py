"""
🤖 Moga Bot - Interface Telegram
Bot Assistente Pessoal Inteligente
"""
import os
import logging
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

logger = logging.getLogger(__name__)

# Importa o Agente de IA Proativo
try:
    from middleware.agente_ia import AgenteProativo, get_agente
    AGENTE_DISPONIVEL = True
except ImportError:
    AGENTE_DISPONIVEL = False
    logger.warning("Agente de IA não disponível")


class TelegramInterface:
    """Interface do Moga Bot - Telegram"""

    # Nomes que ativam o bot em grupos
    BOT_NAMES = ['moga', 'moga_bot', 'mogabot', 'bot', 'assistente']

    def __init__(self, token: str, orchestrator):
        self.token = token
        self.orchestrator = orchestrator
        self.app = None
        self.voz_module = None
        self.condominio_module = None  # Módulo de condomínio/grupos
        self.bot_username = None  # Será preenchido ao iniciar
        self.agente_ia = None  # Agente de IA proativo
        self._setup_condominio_module()
        self._setup_agente_ia()

    def _setup_condominio_module(self):
        """Configura módulo de condomínio"""
        try:
            from modules.condominio import CondominioModule
            self.condominio_module = CondominioModule()
            logger.info("🏢 Módulo de Condomínio configurado")
        except Exception as e:
            logger.warning(f"Módulo de Condomínio não disponível: {e}")

    def _setup_agente_ia(self):
        """Configura agente de IA proativo"""
        if AGENTE_DISPONIVEL:
            try:
                self.agente_ia = get_agente()
                logger.info("🧠 Agente de IA Proativo configurado!")
            except Exception as e:
                logger.warning(f"Agente de IA não disponível: {e}")
                self.agente_ia = None
        else:
            logger.warning("🧠 Agente de IA não importado")

    def set_voz_module(self, voz_module):
        """Define o módulo de voz para transcrição"""
        self.voz_module = voz_module

    def _is_group_chat(self, update: Update) -> bool:
        """Verifica se é chat de grupo"""
        chat_type = update.effective_chat.type
        return chat_type in ['group', 'supergroup']

    def _should_respond_in_group(self, message: str, update: Update) -> bool:
        """Verifica se deve responder no grupo (foi mencionado?)"""
        text_lower = message.lower()
        
        # Verifica se mencionou @bot_username
        if self.bot_username and f'@{self.bot_username.lower()}' in text_lower:
            return True
        
        # Verifica se começou com um dos nomes do bot
        for name in self.BOT_NAMES:
            if text_lower.startswith(name + ',') or text_lower.startswith(name + ' '):
                return True
        
        # Verifica se é resposta a uma mensagem do bot
        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user.is_bot:
                return True
        
        return False

    def _clean_bot_mention(self, message: str) -> str:
        """Remove menção do bot da mensagem"""
        text = message
        
        # Remove @username
        if self.bot_username:
            text = text.replace(f'@{self.bot_username}', '').replace(f'@{self.bot_username.lower()}', '')
        
        # Remove nomes do bot do início
        text_lower = text.lower()
        for name in self.BOT_NAMES:
            if text_lower.startswith(name + ','):
                text = text[len(name)+1:]
                break
            elif text_lower.startswith(name + ' '):
                text = text[len(name)+1:]
                break
        
        return text.strip()

    async def start(self):
        """Inicia o bot"""
        self.app = Application.builder().token(self.token).build()

        # Handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("ajuda", self.cmd_help))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("voz", self.cmd_generic))
        self.app.add_handler(CommandHandler("conectar", self.cmd_conectar_google))

        # Comandos de módulos
        self.app.add_handler(CommandHandler("agenda", self.cmd_generic))
        self.app.add_handler(CommandHandler("lembrete", self.cmd_generic))
        self.app.add_handler(CommandHandler("emails", self.cmd_generic))
        self.app.add_handler(CommandHandler("gastos", self.cmd_generic))
        self.app.add_handler(CommandHandler("despesas", self.cmd_generic))
        self.app.add_handler(CommandHandler("saldo", self.cmd_generic))
        self.app.add_handler(CommandHandler("entrada", self.cmd_generic))
        self.app.add_handler(CommandHandler("tarefa", self.cmd_generic))
        self.app.add_handler(CommandHandler("tarefas", self.cmd_generic))
        self.app.add_handler(CommandHandler("vendas", self.cmd_generic))
        self.app.add_handler(CommandHandler("fatura", self.cmd_generic))
        self.app.add_handler(CommandHandler("concluir", self.cmd_generic))
        
        # Comandos de cancelar/remover
        self.app.add_handler(CommandHandler("cancelar", self.cmd_generic))
        self.app.add_handler(CommandHandler("remover", self.cmd_generic))
        self.app.add_handler(CommandHandler("excluir", self.cmd_generic))
        self.app.add_handler(CommandHandler("deletar", self.cmd_generic))

        #  Handler para ÁUDIO/VOZ
        self.app.add_handler(MessageHandler(
            filters.VOICE | filters.AUDIO,
            self.handle_voice
        ))

        # Mensagens de texto livre
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))

        # Arquivos/Documentos
        self.app.add_handler(MessageHandler(
            filters.Document.ALL | filters.PHOTO,
            self.handle_file
        ))

        # Callbacks de botões inline
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        # Inicia polling
        logger.info("🤖 Moga Bot (Telegram) iniciado!")
        await self.app.initialize()
        await self.app.start()
        
        # Pega o username do bot
        bot_info = await self.app.bot.get_me()
        self.bot_username = bot_info.username
        logger.info(f"🤖 Moga Bot conectado: @{self.bot_username}")
        logger.info(f"📝 Funcionalidades: Texto, Áudio, PDF, Comprovantes")
        
        await self.app.updater.start_polling(drop_pending_updates=True)

        # Mantém rodando
        while True:
            await asyncio.sleep(1)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user

        welcome = f'''
🤖 *Olá, {user.first_name}! Sou o Moga Bot!*

Seu Assistente Pessoal Inteligente.

Posso ajudar você com:
📅 *Agenda* - Compromissos e lembretes
📧 *E-mails* - Ler e gerenciar e-mails
💰 *Finanças* - Gastos e despesas
📄 *Faturas* - Processar boletos (PDF)
🧾 *Comprovantes* - Análise com IA
🛒 *Vendas* - Relatórios e estoque
✅ *Tarefas* - Lista de afazeres
🎤 *Voz* - Envie áudios que eu transcrevo!

Digite /ajuda para ver todos os comandos.

💡 _Você também pode usar linguagem natural!_
Ex: "Me lembra de pagar a conta amanhã"
        '''

        keyboard = [
            [
                InlineKeyboardButton(" Agenda", callback_data="agenda"),
                InlineKeyboardButton(" E-mails", callback_data="emails"),
            ],
            [
                InlineKeyboardButton(" Finanças", callback_data="financas"),
                InlineKeyboardButton(" Tarefas", callback_data="tarefas"),
            ],
            [
                InlineKeyboardButton(" Status", callback_data="status"),
                InlineKeyboardButton(" Ajuda", callback_data="ajuda"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ajuda"""
        response = await self.orchestrator.process("/ajuda", str(update.effective_user.id))
        await update.message.reply_text(response, parse_mode='Markdown')

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        response = await self.orchestrator.process("/status", str(update.effective_user.id))
        await update.message.reply_text(response, parse_mode='Markdown')

    async def cmd_conectar_google(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /conectar - Conecta conta Google"""
        user_id = str(update.effective_user.id)
        
        try:
            from modules.google_auth import GoogleAuthManager
            auth_manager = GoogleAuthManager()
            
            # Verifica se já está autenticado
            if auth_manager.is_authenticated(user_id):
                await update.message.reply_text(
                    "✅ *Você já está conectado ao Google!*\n\n"
                    "Serviços disponíveis:\n"
                    "📅 Google Calendar\n"
                    "📧 Gmail\n"
                    "📁 Google Drive\n\n"
                    "Use `/desconectar` para remover a conexão.",
                    parse_mode='Markdown'
                )
                return
            
            # Gera URL de autorização
            auth_url = auth_manager.get_auth_url(user_id)
            
            if not auth_url:
                await update.message.reply_text(
                    "⚠️ *Erro na configuração*\n\n"
                    "O arquivo `credentials.json` não foi encontrado.\n"
                    "Configure as credenciais do Google Cloud Console.",
                    parse_mode='Markdown'
                )
                return
            
            await update.message.reply_text(
                "🔐 *Conectar com Google*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 *Siga os passos:*\n\n"
                f"*1️⃣ Clique no link para autorizar:*\n\n"
                f"🔗 [Entrar com Google]({auth_url})\n\n"
                "*2️⃣ Escolha sua conta Google*\n\n"
                "*3️⃣ Clique em \"Permitir\"*\n"
                "_(Pode aparecer aviso de app não verificado - clique em \"Avançado\" → \"Acessar\")_\n\n"
                "*4️⃣ Copie o código que aparecer*\n"
                "O código começa com `4/`\n\n"
                "*5️⃣ Cole o código aqui neste chat*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⏰ _O código expira em 10 minutos!_",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Salva estado para aguardar código
            context.user_data['awaiting_google_code'] = True
            
        except Exception as e:
            logger.error(f"Erro ao conectar Google: {e}")
            await update.message.reply_text(
                f"❌ Erro ao iniciar conexão: {str(e)}",
                parse_mode='Markdown'
            )

    async def _process_google_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    code: str, user_id: str):
        """Processa código de autorização do Google"""
        try:
            from modules.google_auth import GoogleAuthManager
            auth_manager = GoogleAuthManager()
            
            # Limpa o código (remove espaços)
            code = code.strip()
            
            # Tenta completar autenticação
            success = auth_manager.complete_auth(user_id, code)
            
            if success:
                context.user_data['awaiting_google_code'] = False
                await update.message.reply_text(
                    "✅ *Conectado com sucesso!*\n\n"
                    "Sua conta Google foi vinculada.\n\n"
                    "Agora posso acessar:\n"
                    "📅 Sua agenda (Google Calendar)\n"
                    "📧 Seus e-mails (Gmail)\n"
                    "📁 Seus arquivos (Google Drive)\n\n"
                    "Experimente perguntar:\n"
                    "• _Quais são meus compromissos de hoje?_\n"
                    "• _Tenho emails novos?_\n"
                    "• _Agende reunião amanhã às 14h_",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *Código inválido ou expirado*\n\n"
                    "Tente novamente com `/conectar`",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar código Google: {e}")
            context.user_data['awaiting_google_code'] = False
            await update.message.reply_text(
                f"❌ Erro ao processar código: {str(e)}\n\n"
                "Tente novamente com `/conectar`",
                parse_mode='Markdown'
            )

    async def cmd_generic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler genérico para comandos"""
        message = update.message.text
        user_id = str(update.effective_user.id)

        await update.message.chat.send_action('typing')
        response = await self.orchestrator.process(message, user_id)
        await update.message.reply_text(response, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto livre com IA proativa"""
        message = update.message.text
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name or "Usuário"
        
        # Verifica se está aguardando código do Google
        if context.user_data.get('awaiting_google_code'):
            await self._process_google_code(update, context, message, user_id)
            return
        
        # Se for grupo
        if self._is_group_chat(update):
            grupo_id = str(update.effective_chat.id)
            grupo_nome = update.effective_chat.title or "Grupo"
            
            # Primeiro: tenta detectar transação automaticamente (sem precisar mencionar)
            if self.condominio_module:
                resultado = await self.condominio_module.handle_natural(
                    message, None, user_id, None,
                    grupo_id=grupo_id, 
                    grupo_nome=grupo_nome,
                    user_name=user_name
                )
                if resultado:
                    logger.info(f"💰 [GRUPO] Transação detectada de {user_name}: {message[:50]}")
                    await update.message.reply_text(resultado, parse_mode='Markdown')
                    return
            
            # Segundo: se mencionou o bot, responde como assistente
            if self._should_respond_in_group(message, update):
                message = self._clean_bot_mention(message)
                logger.info(f"📩 [GRUPO] Comando de {user_id}: {message}")
                
                # Comandos específicos de grupo
                if any(cmd in message.lower() for cmd in ['resumo', 'relatório', 'relatorio', 'caixa', 'saldo']):
                    if self.condominio_module:
                        response = self.condominio_module.get_resumo_grupo(grupo_id)
                        await update.message.reply_text(response, parse_mode='Markdown')
                        return
                
                if any(cmd in message.lower() for cmd in ['transações', 'transacoes', 'histórico', 'historico']):
                    if self.condominio_module:
                        response = self.condominio_module.get_ultimas_transacoes(grupo_id)
                        await update.message.reply_text(response, parse_mode='Markdown')
                        return
            else:
                return  # Ignora mensagem no grupo se não foi mencionado e não é transação
            
            logger.info(f"📩 [GRUPO] Mensagem de {user_id}: {message}")
        else:
            logger.info(f"📩 [PRIVADO] Mensagem de {user_id}: {message}")

        await update.message.chat.send_action('typing')
        
        # 🧠 Usa o agente de IA proativo para entender e agir
        if self.agente_ia:
            try:
                acao = await self.agente_ia.processar(message, user_id, user_name)
                
                # Se o agente detectou uma ação executável
                if acao and acao.tipo not in ["responder", "conversa"]:
                    # Executa a ação detectada
                    response = await self._executar_acao_ia(acao, user_id)
                    
                    await update.message.reply_text(
                        response, 
                        parse_mode='Markdown'
                    )
                    logger.info(f"🧠 Ação IA: {acao.tipo}")
                    return
                
                # Se foi apenas conversa/entendimento
                if acao and acao.resposta:
                    await update.message.reply_text(acao.resposta, parse_mode='Markdown')
                    return
                    
            except Exception as e:
                logger.error(f"Erro no agente IA: {e}")
                # Fallback para orchestrator
        
        # Fallback: usa o orchestrator original
        response = await self.orchestrator.process(message, user_id)
        logger.info(f"📤 Resposta: {response[:100]}...")
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _executar_acao_ia(self, acao, user_id: str) -> str:
        """Executa ação detectada pelo agente de IA"""
        try:
            # Criar Tarefa
            if acao.tipo == "criar_tarefa":
                descricao = acao.parametros.get("descricao", "")
                comando = f"/tarefa adicionar {descricao}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Registrar Gasto/Despesa
            elif acao.tipo == "registrar_gasto":
                valor = acao.parametros.get("valor", 0)
                categoria = acao.parametros.get("categoria", "outros")
                descricao = acao.parametros.get("descricao", "")
                comando = f"/gastos {valor} {categoria} {descricao}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Registrar Receita/Entrada
            elif acao.tipo == "registrar_receita":
                valor = acao.parametros.get("valor", 0)
                descricao = acao.parametros.get("descricao", "")
                comando = f"/entrada {valor} {descricao}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Agendar Evento
            elif acao.tipo == "agendar":
                titulo = acao.parametros.get("titulo", "")
                data = acao.parametros.get("data", "")
                hora = acao.parametros.get("hora", "")
                comando = f"/agenda adicionar {titulo}"
                if data:
                    comando += f" {data}"
                if hora:
                    comando += f" às {hora}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Lembrete
            elif acao.tipo == "criar_lembrete":
                texto = acao.parametros.get("texto", "")
                tempo = acao.parametros.get("tempo", "1 hora")
                comando = f"/lembrete {tempo} {texto}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Registrar Venda
            elif acao.tipo == "registrar_venda":
                produto = acao.parametros.get("produto", "")
                quantidade = acao.parametros.get("quantidade", 1)
                valor = acao.parametros.get("valor", 0)
                comando = f"/vendas registrar {produto} {quantidade} {valor}"
                resposta_modulo = await self.orchestrator.process(comando, user_id)
                return acao.resposta or resposta_modulo
            
            # Cancelar/Remover
            elif acao.tipo == "cancelar":
                item_id = acao.parametros.get("id", "")
                tipo = acao.parametros.get("tipo", "geral")
                descricao = acao.parametros.get("descricao", "")
                
                if item_id:
                    # Tenta cancelar pelo ID
                    comando = f"/cancelar {item_id}"
                    resposta_modulo = await self.orchestrator.process(comando, user_id)
                    return resposta_modulo
                else:
                    # Sem ID - pede para o usuário especificar
                    return f"""
🗑️ *Para cancelar, preciso do ID do item.*

Por favor, informe o ID (código) do que deseja cancelar.

📋 _Use /tarefas ou /agenda para ver os IDs disponíveis._
"""
            
            # Listar Tarefas
            elif acao.tipo == "listar_tarefas":
                comando = "/tarefas listar"
                return await self.orchestrator.process(comando, user_id)
            
            # Listar Agenda
            elif acao.tipo == "listar_agenda":
                data = acao.parametros.get("data", "")
                comando = f"/agenda {data}".strip()
                return await self.orchestrator.process(comando, user_id)
            
            # Ver Finanças
            elif acao.tipo == "ver_financas":
                comando = "/gastos"
                return await self.orchestrator.process(comando, user_id)
            
            # Ver Vendas
            elif acao.tipo == "ver_vendas":
                comando = "/vendas"
                return await self.orchestrator.process(comando, user_id)
            
            # Ação genérica - usa resposta do agente
            else:
                return acao.resposta or "Entendi! Como posso ajudar mais?"
                
        except Exception as e:
            logger.error(f"Erro ao executar ação {acao.tipo}: {e}")
            return acao.resposta or "Desculpe, houve um erro ao processar sua solicitação."

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ Processa mensagens de áudio/voz"""
        user_id = str(update.effective_user.id)

        # Envia "gravando áudio..."
        await update.message.chat.send_action('record_voice')

        # Verifica se módulo de voz está disponível
        if not self.voz_module:
            await update.message.reply_text(
                " Módulo de voz não está configurado.",
                parse_mode='Markdown'
            )
            return

        try:
            # Pega o arquivo de áudio
            if update.message.voice:
                file = await update.message.voice.get_file()
                formato = "ogg"
            elif update.message.audio:
                file = await update.message.audio.get_file()
                formato = update.message.audio.mime_type.split('/')[-1] if update.message.audio.mime_type else "mp3"
            else:
                await update.message.reply_text(" Formato de áudio não suportado.")
                return

            # Baixa o arquivo
            audio_path = f"data/audio_temp/{user_id}_{file.file_id}.{formato}"
            os.makedirs("data/audio_temp", exist_ok=True)
            await file.download_to_drive(audio_path)

            # Transcreve
            await update.message.chat.send_action('typing')
            resultado = await self.voz_module.transcrever_audio(audio_path, formato)

            if resultado['success']:
                texto_transcrito = resultado['text']
                
                # Mostra a transcrição
                await update.message.reply_text(
                    f" *Transcrição:*\n\n\"{texto_transcrito}\"",
                    parse_mode='Markdown'
                )

                # Processa o texto transcrito como comando
                await update.message.chat.send_action('typing')
                response = await self.orchestrator.process(texto_transcrito, user_id)
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    self.voz_module.formatar_resposta_transcricao(resultado),
                    parse_mode='Markdown'
                )

            # Remove arquivo temporário
            try:
                os.remove(audio_path)
            except:
                pass

        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            await update.message.reply_text(
                f" Erro ao processar áudio: {str(e)}",
                parse_mode='Markdown'
            )

    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa arquivos enviados (PDFs, fotos de comprovantes, etc.)"""
        user_id = str(update.effective_user.id)
        
        # Em grupos, só processa se tiver caption mencionando o bot
        if self._is_group_chat(update):
            caption = update.message.caption or ""
            if not self._should_respond_in_group(caption, update):
                return  # Ignora arquivo no grupo se não foi mencionado
            logger.info(f"📎 [GRUPO] Arquivo recebido de {user_id}")
        else:
            logger.info(f"📎 [PRIVADO] Arquivo recebido de {user_id}")

        is_photo = False
        if update.message.document:
            file = await update.message.document.get_file()
            filename = update.message.document.file_name
            mimetype = update.message.document.mime_type or ''
            logger.info(f"   Documento: {filename} ({mimetype})")
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            filename = "photo.jpg"
            mimetype = "image/jpeg"
            is_photo = True
            logger.info(f"   Foto recebida")
        else:
            await update.message.reply_text("❌ Tipo de arquivo não suportado.")
            return

        file_path = f"temp/{user_id}_{filename}"
        os.makedirs("temp", exist_ok=True)
        await file.download_to_drive(file_path)
        logger.info(f"   Salvo em: {file_path}")

        caption = update.message.caption or ""
        caption = self._clean_bot_mention(caption)  # Remove menção do bot
        logger.info(f"   Caption: {caption}")
        
        # 🆕 Processa imagens como comprovantes
        is_image = is_photo or any(x in mimetype.lower() for x in ['image', 'jpeg', 'jpg', 'png'])
        
        if is_image:
            # Processa como comprovante de pagamento
            response = await self._processar_comprovante_telegram(file_path, user_id, caption)
        else:
            # Outros arquivos (PDFs, etc.)
            response = await self.orchestrator.process(
                caption or "Processar arquivo",
                user_id,
                attachments=[file_path]
            )
        
        logger.info(f"📤 Resposta: {response[:100]}...")
        await update.message.reply_text(response, parse_mode='Markdown')

        try:
            os.remove(file_path)
        except:
            pass
    
    async def _processar_comprovante_telegram(self, file_path: str, user_id: str, caption: str) -> str:
        """Processa imagem de comprovante com OCR"""
        try:
            # Tenta importar módulo de comprovantes
            from modules.comprovantes import get_comprovantes_module
            comprovantes_module = get_comprovantes_module()
            
            texto_extraido = ""
            
            # Tenta OCR
            try:
                from PIL import Image
                import pytesseract
                
                image = Image.open(file_path)
                texto_extraido = pytesseract.image_to_string(image, lang='por')
                logger.info(f"[OCR] Texto extraído: {texto_extraido[:200]}...")
                
            except ImportError:
                logger.warning("[OCR] pytesseract não disponível")
                texto_extraido = caption or ""
            except Exception as e:
                logger.error(f"[OCR] Erro: {e}")
                texto_extraido = caption or ""
            
            # Se não conseguiu extrair texto suficiente
            if not texto_extraido or len(texto_extraido.strip()) < 10:
                return f"""📸 *Imagem recebida!*

⚠️ Não consegui ler claramente o texto da imagem.

Por favor, me diga os dados do comprovante:
• Qual o *valor*? (ex: 50,00)
• Para quem foi? (ex: Mercado X)
• Qual a *categoria*? (alimentação, transporte, etc.)

Exemplo: "Gastei 50 no mercado"
"""
            
            # Processa o texto extraído
            comprovante = comprovantes_module.processar_texto_comprovante(texto_extraido, user_id)
            
            # Formata mensagem de confirmação
            return comprovantes_module.formatar_confirmacao(comprovante)
            
        except Exception as e:
            logger.error(f"Erro ao processar comprovante: {e}")
            return f"❌ Erro ao processar comprovante: {str(e)}"

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa cliques em botões inline"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = str(update.effective_user.id)

        command = f"/{data}"
        response = await self.orchestrator.process(command, user_id)

        await query.message.reply_text(response, parse_mode='Markdown')
