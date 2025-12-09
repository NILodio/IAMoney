# Logging Guide - See All Messages

## Quick Setup

### 1. Enable DEBUG Logging

Add to your `.env` file:
```bash
LOG_LEVEL=DEBUG
```

### 2. Restart Your Bot

```bash
python run.py --dev
```

## What You'll See

With `LOG_LEVEL=DEBUG`, you'll see:

### Incoming Messages:
```
[2025-12-09 14:08:24] root.INFO: 📥 INCOMING MESSAGE - Chat ID: 123456789, User: John (@johndoe), Message: Who is Messi?
[2025-12-09 14:08:24] root.INFO: 📥 Processing inbound message: chatId=123456789, type=text, bodyLength=13
[2025-12-09 14:08:24] root.DEBUG: 📥 Full message body: Who is Messi?
```

### Outgoing Messages:
```
[2025-12-09 14:08:25] root.INFO: 📤 OUTGOING MESSAGE - Chat ID: 123456789, Response length: 245
[2025-12-09 14:08:25] root.DEBUG: 📤 Full response: Lionel Messi is an Argentine professional footballer...
[2025-12-09 14:08:25] chatgpt-bot.INFO: ✅ Message sent successfully via Telegram - Chat ID: 123456789, Message ID: 123
[2025-12-09 14:08:25] chatgpt-bot.DEBUG: ✅ Message content: Lionel Messi is an Argentine professional footballer...
```

## Log Levels

- **INFO** (default): Shows basic operations and message summaries
- **DEBUG**: Shows full message content (first 200 chars) and detailed operations

## Log Locations

All logs are printed to **stdout** (console/terminal) where you run the bot.

## Filter Logs

To see only messages:
```bash
python run.py --dev | grep "📥\|📤"
```

To see only errors:
```bash
python run.py --dev | grep "ERROR"
```

## Disable Detailed Logging

Set in `.env`:
```bash
LOG_LEVEL=INFO
```

This will show only summary information without full message content.
