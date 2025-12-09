# Telegram Bot Setup and Testing Guide

## Quick Setup (5 minutes!)

### Step 1: Get Your Telegram Bot Token

1. Open Telegram app on your phone or desktop
2. Search for **@BotFather** (official Telegram bot)
3. Send `/newbot` command
4. Follow the prompts:
   - Choose a name for your bot (e.g., "My AI Assistant")
   - Choose a username (e.g., "my_ai_assistant_bot")
5. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
# Required: Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_key_here

# Optional: OpenAI Model (default: gpt-4o)
OPENAI_MODEL=gpt-4o

# Optional: Server Port (default: 8080)
PORT=8080
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or if using uv/rye:

```bash
uv sync
```

### Step 4: Run the Bot

**Option A: Using Polling (Recommended - Simplest)**

The bot will automatically poll Telegram for new messages. No webhook setup needed!

```bash
python run.py --dev
```

**Option B: Using Webhook (For Production)**

1. Deploy your bot to a server with a public URL
2. Set `WEBHOOK_URL` environment variable
3. Telegram will send updates to your webhook endpoint

## Testing Your Bot

### Method 1: Test via Telegram App

1. Open Telegram app
2. Search for your bot username (e.g., `@my_ai_assistant_bot`)
3. Click "Start" or send `/start`
4. Send a message like "Hello!" or "What can you do?"
5. Your bot should reply with AI-generated responses!

### Method 2: Test via API Endpoint

If you're running the webhook server, you can test sending messages:

```bash
# Send a test message (replace CHAT_ID with your Telegram chat ID)
curl -X POST http://localhost:8080/message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID",
    "message": "Hello from API!"
  }'
```

**How to get your chat_id:**
- Send a message to your bot
- Check the webhook logs or polling logs
- The chat_id will be logged when your bot receives the message

### Method 3: Test Sample Endpoint

```bash
# Get bot info
curl http://localhost:8080/sample?chat_id=YOUR_CHAT_ID&message=Hello
```

## Features Supported

✅ **Text Messages** - Full AI conversation support
✅ **Voice Messages** - Transcribed and processed
✅ **Images** - Analyzed with vision models
✅ **Videos** - Supported
✅ **Documents** - Supported
✅ **Audio Files** - Supported

## Troubleshooting

### Bot Not Responding

1. **Check Bot Token:**
   ```bash
   # Validate config
   python run.py --validate-config
   ```

2. **Check Logs:**
   - Look for error messages in the console
   - Check if bot token is valid

3. **Verify Bot is Running:**
   - Check that the bot process is running
   - Verify no errors in startup logs

### "Invalid Bot Token" Error

- Make sure `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Token should start with numbers and contain a colon
- Get a new token from @BotFather if needed

### "OpenAI API Error"

- Verify `OPENAI_API_KEY` is set correctly
- Check your OpenAI account has credits
- Ensure the API key has proper permissions

### Bot Not Receiving Messages

**If using polling:**
- Make sure polling service is started
- Check logs for connection errors
- Verify bot token is correct

**If using webhook:**
- Ensure webhook URL is publicly accessible
- Check webhook is registered with Telegram
- Verify `/webhook` endpoint is working

## Using Polling Service (Recommended)

The polling service automatically receives messages without webhook setup:

```python
from src.services.telegram_polling import TelegramPollingService
from src.bot.chatbot import ChatBot
import asyncio

async def main():
    bot = ChatBot()
    polling = TelegramPollingService(bot)
    await polling.start_polling()
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await polling.stop_polling()

asyncio.run(main())
```

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Bot token from @BotFather |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key |
| `OPENAI_MODEL` | ❌ No | Model to use (default: gpt-4o) |
| `PORT` | ❌ No | Server port (default: 8080) |

## Next Steps

- Customize bot behavior in `src/config/bot_config.py`
- Add custom functions in `src/bot/function_handler.py`
- Customize AI instructions in `BOT_INSTRUCTIONS`
- Deploy to production (Railway, Render, Fly.io, etc.)

## Support

- Telegram Bot API Docs: https://core.telegram.org/bots/api
- python-telegram-bot Docs: https://python-telegram-bot.org/
- OpenAI API Docs: https://platform.openai.com/docs

Enjoy your FREE Telegram bot! 🚀
