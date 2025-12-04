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

    def __init__(self, token: str, orchestrator):
        self.token = token
        self.orchestrator = orchestrator
        self.app = None
        self.voz_module = None

    def set_voz_module(self, voz_module):
        """Define o módulo de voz para transcrição"""
        self.voz_module = voz_module

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

        await update.message.chat.send_action('typing')
        response = await self.orchestrator.process(message, user_id)
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

        if update.message.document:
            file = await update.message.document.get_file()
            filename = update.message.document.file_name
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            filename = "photo.jpg"
        else:
            await update.message.reply_text(" Tipo de arquivo não suportado.")
            return

        file_path = f"temp/{user_id}_{filename}"
        os.makedirs("temp", exist_ok=True)
        await file.download_to_drive(file_path)

        caption = update.message.caption or "Processar arquivo"
        response = await self.orchestrator.process(
            caption,
            user_id,
            attachments=[file_path]
        )

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

        command = f"/{data}"
        response = await self.orchestrator.process(command, user_id)

        await query.message.reply_text(response, parse_mode='Markdown')
