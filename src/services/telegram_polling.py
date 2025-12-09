"""
Telegram polling service - runs in background to receive messages.
This is simpler than webhooks and works great for development and production.

Usage:
    from src.services.telegram_polling import TelegramPollingService
    from src.bot.chatbot import ChatBot
    
    bot = ChatBot()
    polling_service = TelegramPollingService(bot)
    await polling_service.start_polling()
"""
import asyncio``
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.ext.filters import Document
from src.bot.chatbot import ChatBot

# Configure logging to respect LOG_LEVEL environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='[%(asctime)s] %(name)s.%(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class TelegramPollingService:
    """Telegram polling service for receiving messages."""
    
    def __init__(self, bot: ChatBot):
        """
        Initialize Telegram polling service.
        
        Args:
            bot: ChatBot instance
        """
        self.bot = bot
        self.telegram_client = bot.get_telegram_client()
        self.app = None
        self._running = False
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram message."""
        try:
            if not update.message:
                return
            
            # Transform to internal format
            chat = update.message.chat
            from_user = update.message.from_user
            
            # Log incoming message
            message_text = update.message.text or '[Media/Non-text message]'
            logging.info(f'📥 INCOMING MESSAGE - Chat ID: {chat.id}, User: {from_user.first_name} (@{from_user.username or "N/A"}), Message: {message_text[:100]}')
            
            data = {
                'event': 'message:in:new',
                'data': {
                    'chat': {
                        'id': str(chat.id),
                        'fromNumber': str(from_user.id),
                        'type': 'chat',
                    },
                    'fromNumber': str(from_user.id),
                    'chat_id': str(chat.id),
                    'body': update.message.text or '',
                    'type': 'text',
                    'message_id': update.message.message_id,
                }
            }
            
            # Handle different message types
            if update.message.voice:
                data['data']['type'] = 'voice'
                data['data']['media'] = {'id': update.message.voice.file_id}
                data['data']['body'] = ''  # Will be transcribed
            elif update.message.audio:
                data['data']['type'] = 'audio'
                data['data']['media'] = {'id': update.message.audio.file_id}
                data['data']['body'] = ''
            elif update.message.photo:
                data['data']['type'] = 'photo'
                data['data']['media'] = {'id': update.message.photo[-1].file_id}
                data['data']['body'] = 'User sent an image'
            elif update.message.video:
                data['data']['type'] = 'video'
                data['data']['media'] = {'id': update.message.video.file_id}
                data['data']['body'] = 'User sent a video'
            elif update.message.document:
                data['data']['type'] = 'document'
                data['data']['media'] = {'id': update.message.document.file_id}
                data['data']['body'] = 'User sent a document'
            
            # Load device (bot info)
            device = await self.telegram_client.load_device()
            
            # Process message
            await self.bot.process_message(data['data'], device)
        except Exception as e:
            logging.error(f'Failed to handle Telegram message: {e}')
    
    async def start_polling(self):
        """Start Telegram polling."""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN is required")
            
            # Build application
            self.app = ApplicationBuilder().token(bot_token).build()
            
            # Add message handlers - handle all message types except commands
            # Use a catch-all filter that excludes commands, then check message type in handler
            # This is more reliable than trying to match all filter types
            self.app.add_handler(MessageHandler(~filters.COMMAND, self.handle_message))
            
            # Start polling
            logging.info("Starting Telegram polling...")
            self._running = True
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)
            
            logging.info("Telegram polling started successfully!")
        except Exception as e:
            logging.error(f'Failed to start Telegram polling: {e}')
            self._running = False
            raise
    
    async def stop_polling(self):
        """Stop Telegram polling."""
        if self.app and self._running:
            try:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                self._running = False
                logging.info("Telegram polling stopped")
            except Exception as e:
                logging.error(f'Error stopping polling: {e}')
    
    def is_running(self):
        """Check if polling is running."""
        return self._running
