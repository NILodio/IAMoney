from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from src.bot.chatbot import ChatBot
from src.config.bot_config import BotConfig
import os
import logging

router = APIRouter()
bot = ChatBot()

@router.get('/')
async def index():
    return {
        'name': 'chatbot',
        'description': 'Telegram ChatGPT powered chatbot',
        'version': '1.0.0',
        'endpoints': {
            'webhook': {'path': '/webhook', 'method': 'POST'},
            'sendMessage': {'path': '/message', 'method': 'POST'},
            'sample': {'path': '/sample', 'method': 'GET'},
        },
    }

async def process_message_async(body):
    try:
        device = await load_device()
        if not device:
            logging.error('No active device found for message processing')
            return
        await bot.process_message(body['data'], device)
    except Exception as e:
        logging.error(f'Failed to process inbound message: {e}')

async def load_device():
    try:
        return await bot.get_telegram_client().load_device()
    except Exception as e:
        logging.error(f'Failed to load device: {e}')
        return None

@router.post('/webhook')
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Telegram webhook updates."""
    try:
        body = await request.json()
        
        # Telegram webhook format
        if 'message' in body:
            message = body['message']
            chat = message.get('chat', {})
            from_user = message.get('from', {})
            
            # Transform Telegram format to internal format
            transformed_data = {
                'event': 'message:in:new',
                'data': {
                    'chat': {
                        'id': str(chat.get('id', '')),
                        'fromNumber': str(from_user.get('id', '')),
                        'type': 'chat',
                    },
                    'fromNumber': str(from_user.get('id', '')),
                    'chat_id': str(chat.get('id', '')),
                    'body': message.get('text', ''),
                    'type': 'text',
                    'message_id': message.get('message_id'),
                }
            }
            
            # Handle different message types
            if message.get('voice'):
                transformed_data['data']['type'] = 'voice'
                transformed_data['data']['media'] = {'id': message['voice']['file_id']}
            elif message.get('audio'):
                transformed_data['data']['type'] = 'audio'
                transformed_data['data']['media'] = {'id': message['audio']['file_id']}
            elif message.get('photo'):
                transformed_data['data']['type'] = 'photo'
                transformed_data['data']['media'] = {'id': message['photo'][-1]['file_id']}
            elif message.get('video'):
                transformed_data['data']['type'] = 'video'
                transformed_data['data']['media'] = {'id': message['video']['file_id']}
            elif message.get('document'):
                transformed_data['data']['type'] = 'document'
                transformed_data['data']['media'] = {'id': message['document']['file_id']}
            
            # Process message in background
            background_tasks.add_task(process_message_async, transformed_data)
            return JSONResponse({'ok': True})
        
        # Handle other Telegram update types (ignored)
        return JSONResponse({'ok': True})
    except Exception as e:
        logging.error(f'Webhook processing failed: {e}')
        return JSONResponse({'message': 'Internal server error'}, status_code=500)

@router.post('/message')
async def send_message(request: Request):
    try:
        body = await request.json()
        # Support both 'chat_id' and 'phone' for compatibility
        if not body or ('chat_id' not in body and 'phone' not in body) or 'message' not in body:
            return JSONResponse({'message': 'Invalid payload body. Required: chat_id (or phone) and message'}, status_code=400)
        # Convert 'phone' to 'chat_id' if needed
        if 'phone' in body and 'chat_id' not in body:
            body['chat_id'] = body['phone']
        result = await bot.get_telegram_client().send_message(body)
        if result:
            return JSONResponse(result)
        else:
            return JSONResponse({'message': 'Failed to send message'}, status_code=500)
    except Exception as e:
        logging.error(f'Send message failed: {e}')
        return JSONResponse({'message': 'Failed to send message'}, status_code=500)

@router.get('/sample')
async def sample(request: Request):
    try:
        chat_id = request.query_params.get('chat_id') or request.query_params.get('phone')
        message = request.query_params.get('message', 'Hello World from Telegram Bot!')
        device = await load_device()
        if not device:
            return JSONResponse({'message': 'Bot not initialized'}, status_code=500)
        # Note: For Telegram, you need to provide a chat_id to send a message
        # This endpoint is mainly for testing with webhook
        if not chat_id:
            return JSONResponse({
                'message': 'chat_id parameter required. Get it from a Telegram message.',
                'bot_info': device.get('bot_info', {})
            }, status_code=400)
        data = {
            'chat_id': chat_id,
            'message': message,
        }
        result = await bot.get_telegram_client().send_message(data)
        if result:
            return JSONResponse(result)
        else:
            return JSONResponse({'message': 'Failed to send sample message'}, status_code=500)
    except Exception as e:
        logging.error(f'Sample message failed: {e}')
        return JSONResponse({'message': 'Failed to send sample message'}, status_code=500)

@router.get('/files/{file_id}')
async def file_download(file_id: str):
    server_config = BotConfig.get_server_config()
    temp_path = server_config.get('tempPath', '.tmp')
    filename = f'{file_id}.mp3'
    filepath = os.path.join(temp_path, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail='Invalid or deleted file')
    file_size = os.path.getsize(filepath)
    if not file_size:
        raise HTTPException(status_code=404, detail='Invalid or deleted file')
    def file_stream():
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
        # Delete file after streaming
        if os.path.exists(filepath):
            os.remove(filepath)
    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(file_size),
        'Content-Disposition': f'attachment; filename="{filename}"',
    }
    return StreamingResponse(file_stream(), headers=headers) 