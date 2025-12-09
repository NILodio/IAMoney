import httpx
import os
from src.config.bot_config import BotConfig
from src.utils import app_logger

class OpenAIClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.base_url = 'https://api.openai.com/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    async def create_chat_completion(self, messages, tools=None, params=None):
        default_params = BotConfig.INFERENCE_PARAMS
        limits = BotConfig.LIMITS
        request_params = {
            **default_params,
            **(params or {}),
            'model': self.model,
            'messages': messages,
            'max_tokens': limits['maxOutputTokens'],
        }
        if tools:
            request_params['tools'] = tools
            request_params['tool_choice'] = 'auto'
        try:
            app_logger.debug(f'Creating chat completion: model={self.model}, messages_count={len(messages)}, tools_count={len(tools) if tools else 0}')
            async with httpx.AsyncClient() as client:
                resp = await client.post(f'{self.base_url}/chat/completions', json=request_params, headers=self.headers)
                resp.raise_for_status()
                result = resp.json()
            app_logger.debug(f'Chat completion created: usage={result.get("usage")}, finish_reason={result.get("choices", [{}])[0].get("finish_reason")}')
            return result
        except Exception as e:
            app_logger.error(f'Failed to create chat completion: {e}, model={self.model}')
            raise

    async def transcribe_audio(self, audio_file_path):
        try:
            app_logger.debug(f'Transcribing audio: {audio_file_path}')
            async with httpx.AsyncClient() as client:
                with open(audio_file_path, 'rb') as f:
                    files = {'file': (audio_file_path, f, 'audio/mpeg')}
                    data = {'model': 'whisper-1', 'response_format': 'text'}
                    resp = await client.post(f'{self.base_url}/audio/transcriptions', headers={'Authorization': f'Bearer {self.api_key}'}, data=data, files=files)
                    resp.raise_for_status()
                    transcription = resp.text.strip()
            app_logger.debug(f'Audio transcribed successfully, length={len(transcription)}')
            return transcription or None
        except Exception as e:
            app_logger.error(f'Failed to transcribe audio: {e}, file={audio_file_path}')
            return None

    async def generate_speech(self, text, voice='echo', speed=1.0):
        try:
            app_logger.debug(f'Generating speech: text_length={len(text)}, voice={voice}, speed={speed}')
            async with httpx.AsyncClient() as client:
                data = {
                    'model': 'tts-1',
                    'input': text,
                    'voice': voice,
                    'speed': speed,
                    'response_format': 'mp3',
                }
                resp = await client.post(f'{self.base_url}/audio/speech', headers={'Authorization': f'Bearer {self.api_key}'}, json=data)
                resp.raise_for_status()
                audio_content = resp.content
            app_logger.debug(f'Speech generated successfully, size={len(audio_content)}')
            return audio_content
        except Exception as e:
            app_logger.error(f'Failed to generate speech: {e}, text_length={len(text)}')
            return None

    async def analyze_image(self, image_url, prompt='Describe this image'):
        try:
            app_logger.debug(f'Analyzing image: url={image_url}')
            async with httpx.AsyncClient() as client:
                data = {
                    'model': 'gpt-4o',
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': prompt},
                                {'type': 'image_url', 'image_url': {'url': image_url}},
                            ],
                        },
                    ],
                    'max_tokens': 300,
                }
                resp = await client.post(f'{self.base_url}/chat/completions', json=data, headers=self.headers)
                resp.raise_for_status()
                result = resp.json()
                description = result['choices'][0]['message']['content'].strip()
            app_logger.debug(f'Image analyzed successfully, description_length={len(description)}')
            return description or None
        except Exception as e:
            app_logger.error(f'Failed to analyze image: {e}, url={image_url}')
            return None

    async def generate_image(self, prompt, **kwargs):
        data = {'prompt': prompt}
        data.update(kwargs)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f'{self.base_url}/images/generations', json=data, headers=self.headers)
            resp.raise_for_status()
            return resp.json() 