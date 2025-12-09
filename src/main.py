import asyncio
import os
import sys
import tempfile
import atexit
from pathlib import Path
from fastapi import FastAPI
from src.config.bot_config import BotConfig
from src.utils.app_logger import AppLogger
from src.http.router import router as bot_router
from src.bot.chatbot import ChatBot

app = FastAPI(
    title="Telegram ChatGPT Bot",
    description="Telegram ChatGPT-powered Chatbot",
    version="1.0.0"
)

@app.get('/')
def index():
    return {
        'name': 'chatbot',
        'description': 'Telegram ChatGPT-powered Chatbot',
        'version': '1.0.0',
        'endpoints': {
            'webhook': {'path': '/webhook', 'method': 'POST'},
            'sendMessage': {'path': '/message', 'method': 'POST'},
            'sample': {'path': '/sample', 'method': 'GET'},
        },
    }

app.include_router(bot_router)

def validate_config(api_config: dict) -> None:
    """Validate required configuration parameters."""
    if not api_config.get('telegramBotToken'):
        AppLogger.critical('Missing required Telegram bot token. Get one from @BotFather on Telegram and set TELEGRAM_BOT_TOKEN environment variable.')

    if not api_config.get('openaiKey') or len(api_config['openaiKey']) < 45:
        AppLogger.critical('Missing required OpenAI API key: please sign up for free and obtain your API key: https://platform.openai.com/account/api-keys')

async def initialize_bot(bot: ChatBot, server_config: dict) -> dict:
    """Initialize Telegram bot and validate its status."""
    telegram_client = bot.get_telegram_client()

    try:
        device = await telegram_client.load_device()

        if not device:
            AppLogger.critical('Failed to load Telegram bot information. Please check your TELEGRAM_BOT_TOKEN.')

        AppLogger.info('Telegram bot initialized', {
            'bot_id': device.get('id'),
            'username': device.get('bot_info', {}).get('username'),
            'name': device.get('name')
        })

        return device

    except Exception as e:
        error_msg = str(e)
        if '401' in error_msg or 'Unauthorized' in error_msg:
            AppLogger.critical('Invalid Telegram bot token. Please check your TELEGRAM_BOT_TOKEN and make sure it is valid.')
        AppLogger.critical(f'Failed to load Telegram bot: {error_msg}')

def create_temp_directory(temp_path: str) -> None:
    """Create temporary directory if it doesn't exist."""
    if not os.path.exists(temp_path):
        try:
            os.makedirs(temp_path, mode=0o755, exist_ok=True)
        except Exception as e:
            AppLogger.critical(f"Failed to create temporary directory: {temp_path} - {e}")

async def initialize_bot_services() -> ChatBot:
    """Initialize bot services (one-time setup)."""
    print("🔧 Loading configuration...")
    config = BotConfig.get_all()
    server_config = config['server']
    api_config = config['api']

    print("✅ Validating configuration...")
    validate_config(api_config)

    print("📁 Creating temporary directory...")
    create_temp_directory(server_config['tempPath'])

    print("🤖 Initializing ChatBot...")
    bot = ChatBot()

    print("📱 Loading Telegram bot...")
    device = await initialize_bot(bot, server_config)

    AppLogger.info('Bot services initialized successfully')
    print("✅ Bot services initialization completed!")
    print(f"🤖 Bot is ready! Username: @{device.get('bot_info', {}).get('username', 'N/A')}")
    print("💡 Starting polling service to receive messages...")
    
    return bot

async def start_dev_server(port: int) -> None:
    """Start development server using uvicorn."""
    AppLogger.info(f"Starting development server on port {port}")
    print(f"🚀 Starting development server on http://localhost:{port}")
    print("📋 Server logs will appear below. Press Ctrl+C to stop.\n")

    import uvicorn
    config = uvicorn.Config(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main() -> None:
    """Main application logic."""
    # Check if running in development mode
    if os.getenv('DEV') == 'true':
        print("🚀 Starting Telegram ChatGPT Bot in development mode...")

        print("📋 Initializing bot services...")

        # Initialize the bot services first
        bot = await initialize_bot_services()

        print("🎯 Bot services initialized successfully!")

        # Start Telegram polling service
        try:
            from src.services.telegram_polling import TelegramPollingService
            polling_service = TelegramPollingService(bot)
            # Start polling in background
            asyncio.create_task(polling_service.start_polling())
            print("✅ Telegram polling service started!")
        except Exception as e:
            AppLogger.error(f'Failed to start polling service: {e}')
            print(f"⚠️  Warning: Polling service failed to start: {e}")
            print("💡 You can still use webhooks by setting up a webhook URL.")

        # Now start the development server (this will block and keep running)
        config = BotConfig.get_all()
        await start_dev_server(config['server']['port'])
        return

    # Production mode or other scenarios
    config = BotConfig.get_all()
    AppLogger.info("For production use, please configure a web server to serve the application")
    AppLogger.info(f"Make sure the web server can handle POST requests to /webhook on port {config['server']['port']}")
    AppLogger.info("Or use the Telegram polling service for simpler setup.")

# CLI entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)
    except Exception as e:
        AppLogger.error('Application failed', {'error': str(e)})
        print(f"Error: {e}")
        sys.exit(1)
