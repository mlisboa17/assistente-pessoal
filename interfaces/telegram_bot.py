"""
 Interface Telegram
Bot para Telegram usando python-telegram-bot
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


class TelegramInterface:
    """Interface do bot Telegram"""

    # Nomes que ativam o bot em grupos
    BOT_NAMES = ['bot', 'assistente', 'jarvis', 'alexa', 'siri']

    def __init__(self, token: str, orchestrator):
        self.token = token
        self.orchestrator = orchestrator
        self.app = None
        self.voz_module = None
        self.condominio_module = None  # Módulo de condomínio/grupos
        self.bot_username = None  # Será preenchido ao iniciar
        self._setup_condominio_module()

    def _setup_condominio_module(self):
        """Configura módulo de condomínio"""
        try:
            from modules.condominio import CondominioModule
            self.condominio_module = CondominioModule()
            logger.info("🏢 Módulo de Condomínio configurado")
        except Exception as e:
            logger.warning(f"Módulo de Condomínio não disponível: {e}")

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
        logger.info(" Telegram Bot iniciado!")
        await self.app.initialize()
        await self.app.start()
        
        # Pega o username do bot
        bot_info = await self.app.bot.get_me()
        self.bot_username = bot_info.username
        logger.info(f"🤖 Bot username: @{self.bot_username}")
        
        await self.app.updater.start_polling(drop_pending_updates=True)

        # Mantém rodando
        while True:
            await asyncio.sleep(1)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user

        welcome = f'''
 *Olá, {user.first_name}!*

Sou seu Assistente Pessoal Inteligente.

Posso ajudar você com:
 *Agenda* - Compromissos e lembretes
 *E-mails* - Ler e gerenciar e-mails
 *Finanças* - Gastos e despesas
 *Faturas* - Processar faturas e boletos
 *Vendas* - Relatórios e estoque
 *Tarefas* - Lista de afazeres
 *Voz* - Envie áudios que eu transcrevo!

Digite /ajuda para ver todos os comandos.
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

    async def cmd_generic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler genérico para comandos"""
        message = update.message.text
        user_id = str(update.effective_user.id)

        await update.message.chat.send_action('typing')
        response = await self.orchestrator.process(message, user_id)
        await update.message.reply_text(response, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto livre"""
        message = update.message.text
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name or "Usuário"
        
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
        response = await self.orchestrator.process(message, user_id)
        logger.info(f"📤 Resposta: {response[:100]}...")

        # Garante que a resposta seja uma string
        if isinstance(response, dict):
            response = str(response)
        elif not isinstance(response, str):
            response = str(response)

        # Verifica se é uma resposta estruturada (com botões)
        if isinstance(response, dict) and response.get('tipo') == 'confirmacao_extrato':
            # Cria botões para confirmação do extrato
            keyboard = [
                [
                    InlineKeyboardButton("✅ SIM", callback_data="extrato_confirmar_sim"),
                    InlineKeyboardButton("🔄 REVISAR", callback_data="extrato_confirmar_revisar")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                response['mensagem'],
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(response, parse_mode='Markdown')

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
        """Processa arquivos enviados"""
        user_id = str(update.effective_user.id)
        
        # Em grupos, só processa se tiver caption mencionando o bot
        if self._is_group_chat(update):
            caption = update.message.caption or ""
            if not self._should_respond_in_group(caption, update):
                return  # Ignora arquivo no grupo se não foi mencionado
            logger.info(f"📎 [GRUPO] Arquivo recebido de {user_id}")
        else:
            logger.info(f"📎 [PRIVADO] Arquivo recebido de {user_id}")

        if update.message.document:
            file = await update.message.document.get_file()
            filename = update.message.document.file_name
            logger.info(f"   Documento: {filename}")
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            filename = "photo.jpg"
            logger.info(f"   Foto recebida")
        else:
            await update.message.reply_text(" Tipo de arquivo não suportado.")
            return

        file_path = f"temp/{user_id}_{filename}"
        os.makedirs("temp", exist_ok=True)
        await file.download_to_drive(file_path)
        logger.info(f"   Salvo em: {file_path}")

        caption = update.message.caption or "Processar arquivo"
        caption = self._clean_bot_mention(caption)  # Remove menção do bot
        logger.info(f"   Caption: {caption}")
        
        response = await self.orchestrator.process(
            caption,
            user_id,
            attachments=[file_path]
        )
        logger.info(f"📤 Resposta: {response[:100]}...")

        await update.message.reply_text(response, parse_mode='Markdown')

        try:
            os.remove(file_path)
        except:
            pass

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa cliques em botões inline"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = str(update.effective_user.id)

        # Processa callbacks especiais de confirmação de extrato
        if data.startswith('extrato_confirmar_'):
            acao = data.replace('extrato_confirmar_', '')
            if acao == 'sim':
                command = "SIM"
            elif acao == 'revisar':
                command = "REVISAR"
            else:
                command = f"/{data}"
        else:
            command = f"/{data}"

        response = await self.orchestrator.process(command, user_id)

        # Garante que a resposta seja uma string
        if isinstance(response, dict):
            response = str(response)
        elif not isinstance(response, str):
            response = str(response)

        await query.message.reply_text(response, parse_mode='Markdown')
