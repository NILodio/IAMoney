#!/usr/bin/env python3

"""
WhatsApp ChatGPT Bot Startup Script

This script provides an easy way to start the ChatGPT WhatsApp bot with proper
initialization and error handling.

Usage:
    python run.py                    # Start in production mode
    python run.py --dev              # Start in development mode
    python run.py --init-only        # Initialize services only (no server)
    python run.py --validate-config  # Validate configuration only
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main, initialize_bot_services, validate_config
from src.config.bot_config import BotConfig
from src.utils.app_logger import AppLogger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="WhatsApp ChatGPT Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--dev',
        action='store_true',
        help='Start in development mode with ngrok tunnel'
    )

    parser.add_argument(
        '--init-only',
        action='store_true',
        help='Initialize bot services only (no server)'
    )

    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration only'
    )

    parser.add_argument(
        '--port',
        type=int,
        help='Port to run the server on (overrides config)'
    )

    return parser.parse_args()

async def validate_config_only():
    """Validate configuration and exit."""
    try:
        print("🔧 Loading configuration...")
        config = BotConfig.get_all()

        print("✅ Validating configuration...")
        validate_config(config['api'])

        print("✅ Configuration is valid!")

        # Show configuration summary
        api_config = config['api']
        server_config = config['server']

        print("\n📋 Configuration Summary:")
        print(f"  • API Key: {'✅ Set' if api_config.get('apiKey') and len(api_config['apiKey']) > 60 else '❌ Missing or invalid'}")
        print(f"  • OpenAI Key: {'✅ Set' if api_config.get('openaiKey') and len(api_config['openaiKey']) > 45 else '❌ Missing or invalid'}")
        print(f"  • OpenAI Model: {api_config.get('openaiModel', 'Not set')}")
        print(f"  • Server Port: {server_config.get('port', 'Not set')}")
        print(f"  • Production Mode: {'Yes' if server_config.get('production') else 'No'}")
        print(f"  • Webhook URL: {server_config.get('webhookUrl', 'Not set (will use ngrok)')}")
        print(f"  • Ngrok Token: {'✅ Set' if server_config.get('ngrokToken') else '❌ Not set'}")

    except Exception as e:
        AppLogger.error('Configuration validation failed', {'error': str(e)})
        sys.exit(1)

async def init_services_only():
    """Initialize bot services only."""
    try:
        print("🔧 Initializing bot services...")
        await initialize_bot_services()
        print("✅ Bot services initialized successfully!")
        print("ℹ️ Services are ready. You can now start the server separately.")
    except Exception as e:
        AppLogger.error('Service initialization failed', {'error': str(e)})
        sys.exit(1)

def main_cli():
    """Main CLI entry point."""
    args = parse_arguments()

    # Set environment variables based on arguments
    if args.dev:
        os.environ['DEV'] = 'true'

    if args.port:
        os.environ['PORT'] = str(args.port)

    try:
        if args.validate_config:
            asyncio.run(validate_config_only())
        elif args.init_only:
            asyncio.run(init_services_only())
        else:
            # Run the main application
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)
    except Exception as e:
        AppLogger.error('Application failed', {'error': str(e)})
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_cli()
