"""
Telegram Bot API client - COMPLETELY FREE!
Telegram Bot API is free and doesn't require any paid services.

Setup:
1. Talk to @BotFather on Telegram
2. Create a new bot with /newbot
3. Copy the bot token
4. That's it! No webhook setup needed (we use polling)

Documentation: https://core.telegram.org/bots/api
"""
import os
import asyncio
from typing import Dict, Optional, List, Any
from src.utils import app_logger

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    app_logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")


class TelegramClient:
    """Telegram Bot API client - 100% FREE."""
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram Bot client.
        
        Args:
            bot_token: Telegram bot token from @BotFather
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "python-telegram-bot is required. Install with: pip install python-telegram-bot"
            )
        
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not self.bot_token:
            raise ValueError(
                "Telegram bot token is required. "
                "Get one from @BotFather on Telegram. Set TELEGRAM_BOT_TOKEN environment variable."
            )
        
        self.bot = Bot(token=self.bot_token)
        self._bot_info = None
        
        app_logger.info("Telegram Bot client initialized (FREE)")
    
    async def send_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a Telegram message.
        
        Args:
            data: Dictionary with 'chat_id' (or 'phone' for compatibility) and 'message'
                  Optional: 'media' for file path
        """
        try:
            # Support both 'chat_id' and 'phone' for compatibility
            chat_id = data.get('chat_id') or data.get('phone')
            message = data.get('message', '')
            media_path = data.get('media')
            
            if not chat_id:
                app_logger.error("chat_id or phone is required")
                return None
            
            if media_path and os.path.exists(media_path):
                # Send media message
                ext = os.path.splitext(media_path)[1].lower()
                
                with open(media_path, 'rb') as f:
                    if ext in ['.mp3', '.ogg', '.wav', '.m4a']:
                        result = await self.bot.send_audio(
                            chat_id=chat_id,
                            audio=f,
                            caption=message if message else None,
                        )
                    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        result = await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=f,
                            caption=message if message else None,
                        )
                    elif ext in ['.mp4', '.mov', '.avi']:
                        result = await self.bot.send_video(
                            chat_id=chat_id,
                            video=f,
                            caption=message if message else None,
                        )
                    else:
                        result = await self.bot.send_document(
                            chat_id=chat_id,
                            document=f,
                            caption=message if message else None,
                        )
            else:
                # Send text message
                result = await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                )
            
            app_logger.info(f'✅ Message sent successfully via Telegram - Chat ID: {chat_id}, Message ID: {result.message_id}')
            app_logger.debug(f'✅ Message content: {message[:100]}')
            return {
                'id': str(result.message_id),
                'chat_id': str(result.chat.id),
                'status': 'sent'
            }
        except TelegramError as e:
            app_logger.error(f'Failed to send Telegram message: {e}')
            return None
    
    async def load_device(self, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load Telegram bot information."""
        try:
            if not self._bot_info:
                self._bot_info = await self.bot.get_me()
            
            # Format to match WhatsApp device structure for compatibility
            device = {
                'id': str(self._bot_info.id),
                'name': self._bot_info.username or self._bot_info.first_name,
                'phone': f'@{self._bot_info.username}' if self._bot_info.username else None,
                'status': 'operative',
                'session': {
                    'status': 'online',  # Telegram bots are always online
                },
                'billing': {
                    'subscription': {
                        'product': 'io',  # Telegram is free
                    }
                },
                'bot_info': {
                    'id': self._bot_info.id,
                    'username': self._bot_info.username,
                    'first_name': self._bot_info.first_name,
                    'is_bot': self._bot_info.is_bot,
                }
            }
            return device
        except TelegramError as e:
            app_logger.error(f'Failed to load Telegram bot info: {e}')
            raise
    
    async def register_webhook(self, webhook_url: str, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Register webhook with Telegram (optional).
        For polling mode, webhooks are not needed.
        """
        app_logger.info("Using polling mode - webhook not needed for Telegram")
        return {'mode': 'polling', 'status': 'active'}
    
    async def download_media(self, file_id: str) -> Optional[bytes]:
        """Download media from Telegram."""
        try:
            file = await self.bot.get_file(file_id)
            # Download file content
            file_content = await file.download_as_bytearray()
            return bytes(file_content)
        except TelegramError as e:
            app_logger.error(f'Failed to download media from Telegram: {e}')
            return None
    
    async def send_typing_state(self, data: Dict[str, Any], device: Dict[str, Any], action: str = 'typing') -> None:
        """Send typing indicator via Telegram."""
        try:
            chat_id = data.get('chat_id') or data.get('fromNumber') or data.get('phone')
            if action == 'typing':
                await self.bot.send_chat_action(chat_id=chat_id, action='typing')
        except TelegramError as e:
            app_logger.debug(f'Failed to send typing state via Telegram: {e}')
    
    # Optional methods for compatibility (not applicable to Telegram)
    async def pull_members(self, device: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pull team members (not applicable to Telegram)."""
        return []
    
    async def pull_labels(self, device: Dict[str, Any], force: bool = False) -> List[Dict[str, Any]]:
        """Pull chat labels (not applicable to Telegram)."""
        return []
    
    async def create_labels(self, device: Dict[str, Any], required_labels: List[str]) -> None:
        """Create labels (not applicable to Telegram)."""
        pass
    
    async def update_chat_labels(self, data: Dict[str, Any], device: Dict[str, Any], labels: List[str]) -> None:
        """Update chat labels (not applicable to Telegram)."""
        pass
    
    async def update_chat_metadata(self, data: Dict[str, Any], device: Dict[str, Any], metadata: List[Dict[str, str]]) -> None:
        """Update chat metadata (not applicable to Telegram)."""
        pass
    
    async def assign_chat_to_agent(self, data: Dict[str, Any], device: Dict[str, Any], agent_id: str) -> None:
        """Assign chat to agent (not applicable to Telegram)."""
        pass
