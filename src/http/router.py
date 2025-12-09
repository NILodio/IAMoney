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
        'description': 'WhatsApp ChatGPT powered chatbot for Wassenger',
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
        return await bot.get_wassenger_client().load_device()
    except Exception as e:
        logging.error(f'Failed to load device: {e}')
        return None

@router.post('/webhook')
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        if not body or 'event' not in body or 'data' not in body:
            logging.warning(f'Invalid webhook payload: {body}')
            return JSONResponse({'message': 'Invalid payload body'}, status_code=400)
        if body['event'] != 'message:in:new':
            logging.debug(f'Ignoring webhook event: {body["event"]}')
            return JSONResponse({'message': 'Ignore webhook event: only message:in:new is accepted'}, status_code=202)
        # Process message in background
        background_tasks.add_task(process_message_async, body)
        return JSONResponse({'ok': True})
    except Exception as e:
        logging.error(f'Webhook processing failed: {e}')
        return JSONResponse({'message': 'Internal server error'}, status_code=500)

@router.post('/message')
async def send_message(request: Request):
    try:
        body = await request.json()
        if not body or 'phone' not in body or 'message' not in body:
            return JSONResponse({'message': 'Invalid payload body'}, status_code=400)
        result = await bot.get_wassenger_client().send_message(body)
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
        phone = request.query_params.get('phone')
        message = request.query_params.get('message', 'Hello World from Wassenger!')
        device = await load_device()
        if not device:
            return JSONResponse({'message': 'No active device found'}, status_code=500)
        data = {
            'phone': phone or device.get('phone'),
            'message': message,
            'device': device.get('id'),
        }
        result = await bot.get_wassenger_client().send_message(data)
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