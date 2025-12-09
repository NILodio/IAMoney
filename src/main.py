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
from src.utils.ngrok_tunnel import NgrokTunnel

app = FastAPI(
    title="WhatsApp ChatGPT Bot",
    description="WhatsApp ChatGPT-powered Chatbot for Wassenger",
    version="1.0.0"
)

@app.get('/')
def index():
    return {
        'name': 'chatbot',
        'description': 'WhatsApp ChatGPT-powered Chatbot for Wassenger',
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
    if not api_config.get('apiKey') or len(api_config['apiKey']) < 60:
        AppLogger.critical('Please sign up in Wassenger and obtain your API key: https://app.wassenger.com/apikeys')

    if not api_config.get('openaiKey') or len(api_config['openaiKey']) < 45:
        AppLogger.critical('Missing required OpenAI API key: please sign up for free and obtain your API key: https://platform.openai.com/account/api-keys')

async def create_tunnel(server_config: dict) -> str:
    """Create Ngrok tunnel for development."""
    if not server_config.get('ngrokToken'):
        AppLogger.critical('Ngrok token is required for development mode. Get one from: https://ngrok.com/signup')

    ngrok = NgrokTunnel(server_config['ngrokToken'])
    return ngrok.create(server_config['port'])

async def initialize_bot(bot: ChatBot, server_config: dict) -> dict:
    """Initialize device and validate its status."""
    wassenger_client = bot.get_wassenger_client()

    try:
        device = await wassenger_client.load_device(server_config.get('device'))

        if not device or device.get('status') != 'operative':
            AppLogger.critical('No active WhatsApp numbers in your account. Please connect a WhatsApp number in your Wassenger account: https://app.wassenger.com/create')

        if device.get('session', {}).get('status') != 'online':
            AppLogger.critical(f"WhatsApp number ({device.get('alias')}) is not online. Please make sure the WhatsApp number in your Wassenger account is properly connected: https://app.wassenger.com/{device.get('id')}/scan")

        billing_product = device.get('billing', {}).get('subscription', {}).get('product')
        if billing_product != 'io':
            AppLogger.critical(f"WhatsApp number plan ({device.get('alias')}) does not support inbound messages. Please upgrade the plan here: https://app.wassenger.com/{device.get('id')}/plan?product=io")

        AppLogger.info('Using WhatsApp connected number', {
            'phone': device.get('phone'),
            'alias': device.get('alias'),
            'id': device.get('id')
        })

        return device

    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg:
            AppLogger.critical('Unauthorized API key. Please check your Wassenger API key and make sure it is valid: https://app.wassenger.com/apikeys')
        if '404' in error_msg:
            AppLogger.critical('API endpoint not found. Please check the API base URL configuration')
        AppLogger.critical(f'Failed to load WhatsApp number: {error_msg}')

async def setup_webhook(bot: ChatBot, device: dict, server_config: dict) -> None:
    """Setup webhook for message reception."""
    wassenger_client = bot.get_wassenger_client()

    if server_config.get('production'):
        AppLogger.info('Validating webhook endpoint...')

        webhook_url = server_config.get('webhookUrl')
        if not webhook_url:
            AppLogger.critical('Webhook URL is required for production mode. Please set WEBHOOK_URL environment variable')

        webhook = await wassenger_client.register_webhook(webhook_url, device)
        if not webhook:
            AppLogger.critical('Failed to register webhook in production mode')

        AppLogger.info('Using webhook endpoint in production mode', {'url': webhook.get('url')})
    else:
        AppLogger.info('Registering webhook tunnel...')

        tunnel_url = server_config.get('webhookUrl')
        if not tunnel_url:
            tunnel_url = await create_tunnel(server_config)

        webhook_url = f"{tunnel_url}/webhook"
        webhook = await wassenger_client.register_webhook(webhook_url, device)
        if not webhook:
            AppLogger.critical('Failed to register webhook tunnel')

        AppLogger.info('Webhook tunnel registered', {'url': webhook_url})

def create_temp_directory(temp_path: str) -> None:
    """Create temporary directory if it doesn't exist."""
    if not os.path.exists(temp_path):
        try:
            os.makedirs(temp_path, mode=0o755, exist_ok=True)
        except Exception as e:
            AppLogger.critical(f"Failed to create temporary directory: {temp_path} - {e}")

async def setup_labels_and_members(bot: ChatBot, device: dict) -> None:
    """Setup labels and members for the bot."""
    wassenger_client = bot.get_wassenger_client()
    config = BotConfig.get_all()

    try:
        # Pre-load device labels and team members
        await wassenger_client.pull_members(device)
        await wassenger_client.pull_labels(device)

        # Create labels if they don't exist
        required_labels = []
        required_labels.extend(config.get('setLabelsOnBotChats', []))
        required_labels.extend(config.get('setLabelsOnUserAssignment', []))

        if required_labels:
            await wassenger_client.create_labels(device, required_labels)

        AppLogger.info('Labels and members setup completed')

    except Exception as e:
        AppLogger.error('Failed to setup labels and members', {'error': str(e)})

async def initialize_bot_services() -> None:
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

    print("📱 Loading WhatsApp device...")
    device = await initialize_bot(bot, server_config)

    print("🏷️ Setting up labels and members...")
    await setup_labels_and_members(bot, device)

    print("🔗 Setting up webhook...")
    await setup_webhook(bot, device, server_config)

    AppLogger.info('Bot services initialized successfully')
    print("✅ Bot services initialization completed!")

def start_dev_server(port: int) -> None:
    """Start development server using uvicorn."""
    AppLogger.info(f"Starting development server on port {port}")
    print(f"🚀 Starting development server on http://localhost:{port}")
    print("📋 Server logs will appear below. Press Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

async def main() -> None:
    """Main application logic."""
    # Check if running in development mode
    if os.getenv('DEV') == 'true':
        print("🚀 Starting ChatGPT WhatsApp Bot in development mode...")

        # Register shutdown handler for Ngrok cleanup
        NgrokTunnel.register_shutdown_handler()

        print("📋 Initializing bot services...")

        # Initialize the bot services first
        await initialize_bot_services()

        print("🎯 Bot services initialized successfully!")

        # Now start the development server (this will block and keep running)
        config = BotConfig.get_all()
        start_dev_server(config['server']['port'])
        return

    # Production mode or other scenarios
    config = BotConfig.get_all()
    AppLogger.info("For production use, please configure a web server to serve the application")
    AppLogger.info(f"Make sure the web server can handle POST requests to /webhook on port {config['server']['port']}")

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
