import os
import re
import asyncio
import logging
import tempfile
import datetime
from src.api.openai_client import OpenAIClient
from src.api.telegram_client import TelegramClient
from src.bot.function_handler import FunctionHandler
from src.config.bot_config import BotConfig
from src.storage import memory_store

# Configure logging to respect LOG_LEVEL environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='[%(asctime)s] %(name)s.%(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChatBot:
    def __init__(self):
        self.config = BotConfig.get_all()
        api_config = self.config['api']
        self.openai_client = OpenAIClient(api_config['openaiKey'], api_config['openaiModel'])
        self.telegram_client = TelegramClient(api_config['telegramBotToken'])
        self.function_handler = FunctionHandler()
        # Optionally set up cache TTL
        # memory_store.cache.ttl = self.config.get('cacheTTL', 3600)

    def can_reply(self, data, device):
        """Check if bot can reply to this message. Simplified for Telegram."""
        # Telegram bots can always reply (no agent assignment, labels, etc.)
        # Only check basic message validity
        chat = data.get('chat', {})
        if not chat or not chat.get('id'):
            logging.debug("Invalid chat data")
            return False
        # Check if message has content
        if not data.get('body') and not data.get('type'):
            logging.debug("Message has no content")
            return False
        return True

    def has_chat_metadata_quota_exceeded(self, chat):
        metadata = chat.get('contact', {}).get('metadata', [])
        for item in metadata:
            if item.get('key') == 'bot:chatgpt:status' and item.get('value') == 'too_many_messages':
                return True
        return False

    def has_chat_messages_quota(self, chat):
        limits = self.config['limits']
        chat_id = chat['id']
        # Use a separate key for message count to avoid conflict with conversation history
        message_count_key = f"msg_count_{chat_id}"
        message_count = memory_store.get(message_count_key, 0)
        # Ensure it's an integer (in case it was stored as something else)
        if not isinstance(message_count, int):
            message_count = 0
        return message_count < limits['maxMessagesPerChat']

    async def update_chat_on_messages_quota(self, data, device):
        """Handle message quota exceeded. Simplified for Telegram."""
        chat = data['chat']
        chat_id = chat['id']
        logging.info(f'Chat quota exceeded: {chat_id}')
        # Send a message informing user about quota
        await self.send_message({
            'chat_id': chat_id,
            'message': 'You have reached the maximum number of messages. Please try again later.',
        })

    async def assign_chat_to_agent(self, data, device, force=False):
        """Assign chat to agent. Not applicable to Telegram, but kept for compatibility."""
        # Telegram doesn't support agent assignment
        # Just send a message that human help was requested
        chat_id = data.get('chat', {}).get('id') or data.get('chat_id')
        if chat_id:
            await self.send_message({
                'chat_id': chat_id,
                'message': self.config['templateMessages']['chatAssigned'],
            })

    def filter_eligible_members(self, members):
        eligible = []
        for member in members:
            if member.get('status') != 'active':
                continue
            if self.config['skipTeamRolesFromAssignment'] and member.get('role') in self.config['skipTeamRolesFromAssignment']:
                continue
            if self.config['teamWhitelist'] and member.get('id') not in self.config['teamWhitelist']:
                continue
            if self.config['teamBlacklist'] and member.get('id') in self.config['teamBlacklist']:
                continue
            if self.config['assignOnlyToOnlineMembers'] and member.get('presence', 'offline') != 'online':
                continue
            eligible.append(member)
        return eligible

    async def send_message(self, data):
        """Send message via Telegram. Supports both 'chat_id' and 'phone' for compatibility."""
        # Convert 'phone' to 'chat_id' if needed for backward compatibility
        if 'phone' in data and 'chat_id' not in data:
            data['chat_id'] = data['phone']
        return await self.telegram_client.send_message(data)

    async def process_message(self, data, device):
        try:
            if not self.can_reply(data, device):
                return
            chat = data['chat']
            chat_id = chat['id']
            if not self.has_chat_messages_quota(chat):
                await self.update_chat_on_messages_quota(data, device)
                logging.info(f'Chat quota exceeded: {chat_id}')
                return
            if self.has_chat_metadata_quota_exceeded(chat):
                logging.info(f'Chat quota previously exceeded: {chat_id}')
                return
            # Use separate key for message count
            message_count_key = f"msg_count_{chat_id}"
            current_count = memory_store.get(message_count_key, 0)
            if not isinstance(current_count, int):
                current_count = 0
            memory_store.set(message_count_key, current_count + 1)
            body = await self.extract_message_body(data)
            logging.info(f'📥 Processing inbound message: chatId={chat_id}, type={data.get("type")}, bodyLength={len(body)}')
            logging.debug(f'📥 Full message body: {body[:200]}')  # Log first 200 chars
            await self.telegram_client.send_typing_state(data, device)
            if re.match(r'^(human|person|help|stop)$', body.strip(), re.I):
                await self.assign_chat_to_agent(data, device)
                return
            use_audio = data.get('type') == 'audio'
            await self.generate_and_send_response(data, device, body, use_audio)
        except Exception as e:
            logging.error(f'Failed to process message: {e}, chatId={data.get("chat", {}).get("id", "unknown")}')

    async def extract_message_body(self, data):
        """Extract message body from Telegram update."""
        body = data.get('body', '')
        
        # Handle Telegram message types
        msg_type = data.get('type', '')
        
        # Handle audio/voice messages
        if msg_type in ['audio', 'voice'] and data.get('media', {}).get('id'):
            body = await self.transcribe_audio(data)
        
        # Handle other media types
        if not body:
            body = {
                'image': 'User sent an image',
                'photo': 'User sent an image',
                'video': 'User sent a video',
                'document': 'User sent a document',
                'location': 'User sent a location',
                'contact': 'User sent contact information',
                'voice': 'User sent a voice message',
                'audio': 'User sent an audio file',
            }.get(msg_type, 'User sent a message')
        
        max_length = min(self.config['limits']['maxInputCharacters'], 10000)
        return body[:max_length].strip()

    async def transcribe_audio(self, data):
        try:
            media_id = data.get('media', {}).get('id')
            if not media_id:
                return ''
            audio_content = await self.telegram_client.download_media(media_id)
            if not audio_content:
                return ''
            temp_dir = self.config['server'].get('tempPath', '.tmp')
            os.makedirs(temp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix='.mp3') as tmp:
                tmp.write(audio_content)
                temp_file = tmp.name
            transcription = await self.openai_client.transcribe_audio(temp_file)
            os.remove(temp_file)
            return transcription or ''
        except Exception as e:
            logging.error(f'Failed to transcribe audio: {e}')
            return ''

    async def generate_and_send_response(self, data, device, body, use_audio):
        if not body:
            chat_id = data.get('chat', {}).get('id') or data.get('chat_id')
            await self.send_message({
                'chat_id': chat_id,
                'message': self.config['unknownCommandMessage'],
            })
            return
        chat_id = data['chat']['id']
        chat_messages = memory_store.get(chat_id, {})
        if chat_messages is None or not isinstance(chat_messages, dict):
            chat_messages = {}
        previous_messages = self.build_conversation_context(chat_messages)
        messages = [
            {'role': 'system', 'content': self.config['botInstructions']},
        ]
        if previous_messages is None:
            previous_messages = []
        messages.extend(previous_messages)
        messages.append({'role': 'user', 'content': body})
        self.store_message(chat_id, 'user', body)
        tools = self.function_handler.get_functions_for_openai()
        try:
            response = await self.generate_response_with_functions(messages, tools, data, device)
            if not response:
                response = self.config['unknownCommandMessage']
            logging.info(f'📤 OUTGOING MESSAGE - Chat ID: {chat_id}, Response length: {len(response)}')
            logging.debug(f'📤 Full response: {response[:200]}')  # Log first 200 chars
            self.store_message(chat_id, 'assistant', response)
            await self.send_response(data, device, response, use_audio)
            await self.update_chat_metadata(data, device)
        except Exception as e:
            error_msg = str(e)
            logging.error(f'Failed to generate response: {e}')
            chat_id = data.get('chat', {}).get('id') or data.get('chat_id')
            
            # Handle rate limiting specifically
            if '429' in error_msg or 'Too Many Requests' in error_msg:
                error_message = "I'm receiving too many requests right now. Please try again in a moment."
            else:
                error_message = self.config['unknownCommandMessage']
            
            await self.send_message({
                'chat_id': chat_id,
                'message': error_message,
            })

    async def generate_response_with_functions(self, messages, tools, data, device):
        max_calls = 5
        count = 0
        while count < max_calls:
            count += 1
            response = await self.openai_client.create_chat_completion(messages, tools)
            choice = response.get('choices', [{}])[0]
            if not choice:
                break
            message = choice.get('message', {})
            messages.append(message)
            if message.get('tool_calls'):
                for tool_call in message['tool_calls']:
                    if tool_call.get('type') == 'function':
                        function_name = tool_call['function']['name']
                        import json
                        arguments = json.loads(tool_call['function']['arguments']) if tool_call['function']['arguments'] else {}
                        context = {'data': data, 'device': device, 'messages': messages}
                        function_result = self.function_handler.execute_function(function_name, arguments, context)
                        messages.append({
                            'role': 'tool',
                            'tool_call_id': tool_call['id'],
                            'content': function_result,
                        })
                continue
            return (message.get('content') or '').strip()
        return ''

    def build_conversation_context(self, chat_messages):
        messages = []
        limit = self.config['limits']['chatHistoryLimit']
        # Sort by date, limit, and reverse
        if chat_messages is None:
            chat_messages = []
        if isinstance(chat_messages, dict):
            chat_messages = list(chat_messages.values())
        chat_messages = sorted(chat_messages, key=lambda m: m.get('date', ''), reverse=True)[:limit]
        chat_messages = list(reversed(chat_messages))
        for msg in chat_messages:
            if msg.get('content'):
                messages.append({'role': msg['role'], 'content': msg['content']})
        return messages

    def store_message(self, chat_id, role, content):
        messages = memory_store.get(chat_id, {})
        if messages is None or not isinstance(messages, dict):
            messages = {}
        import uuid
        message_id = str(uuid.uuid4())
        messages[message_id] = {
            'role': role,
            'content': content,
            'date': datetime.datetime.now().isoformat(),
        }
        memory_store.set(chat_id, messages)

    async def send_response(self, data, device, response, use_audio):
        chat_id = data.get('chat', {}).get('id') or data.get('chat_id')
        message_data = {
            'chat_id': chat_id,
        }
        if use_audio and self.config['features']['audioOutput']:
            audio_content = await self.openai_client.generate_speech(
                response,
                self.config['features']['voice'],
                self.config['features']['voiceSpeed']
            )
            if audio_content:
                temp_dir = self.config['server'].get('tempPath', '.tmp')
                os.makedirs(temp_dir, exist_ok=True)
                with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix='.mp3') as tmp:
                    tmp.write(audio_content)
                    audio_file = tmp.name
                message_data['media'] = audio_file
                message_data['message'] = ''
            else:
                message_data['message'] = response
        else:
            message_data['message'] = response
        await self.send_message(message_data)

    async def update_chat_metadata(self, data, device):
        """Update chat metadata. Not applicable to Telegram, but kept for compatibility."""
        # Telegram doesn't support chat metadata/labels
        # This is a no-op for Telegram
        pass

    def get_wassenger_client(self):
        """Backward compatibility method. Returns Telegram client."""
        return self.telegram_client
    
    def get_telegram_client(self):
        """Get Telegram client."""
        return self.telegram_client

    # Add more methods as needed
