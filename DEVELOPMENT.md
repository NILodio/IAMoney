# Development Guide

This guide covers the development workflow and architecture of the WhatsApp ChatGPT Bot Python implementation.

## Architecture Overview

The bot is built using modern Python async/await patterns with FastAPI for HTTP handling and follows a modular architecture:

```
src/
├── main.py              # Main application entry point with initialization logic
├── bot/
│   ├── chatbot.py       # Core bot logic and message processing
│   └── function_handler.py # OpenAI function calling handlers
├── api/
│   ├── openai_client.py # OpenAI API integration
│   └── wassenger_client.py # Wassenger WhatsApp API client
├── config/
│   └── bot_config.py    # Configuration management
├── http/
│   └── router.py        # FastAPI routes and webhook handling
├── storage/
│   └── memory_store.py  # In-memory caching and state management
└── utils/
    ├── app_logger.py    # Logging utilities
    └── ngrok_tunnel.py  # Development tunnel management
```

## Key Components

### Main Application (`main.py`)

The main application handles:
- Configuration validation
- Device loading and status checking
- Webhook registration (with ngrok tunnel for development)
- Labels and team members setup
- Development vs production mode handling

**Key Functions:**
- `validate_config()` - Validates API keys and configuration
- `initialize_bot()` - Loads and validates WhatsApp device
- `setup_webhook()` - Registers webhook endpoint
- `setup_labels_and_members()` - Initializes bot labels and team structure
- `initialize_bot_services()` - Complete one-time setup
- `main()` - Main application entry point

### ChatBot (`bot/chatbot.py`)

Core bot functionality:
- Message processing and filtering
- Chat assignment and human handoff
- Rate limiting and quota management
- Audio transcription and TTS
- Image analysis
- Conversation memory management

### WassengerClient (`api/wassenger_client.py`)

WhatsApp API integration:
- Message sending (text, media, location, etc.)
- Device management
- Contact and chat operations
- Webhook registration
- Labels and metadata management

### Configuration (`config/bot_config.py`)

Centralized configuration management:
- Environment variable handling
- Default values and settings
- API configuration
- Bot behavior settings

## Development Workflow

### 1. Local Development Setup

```bash
# Clone and setup
git clone <repository>
cd whatsapp-chatgpt-bot-python
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys

# Validate configuration
python run.py --validate-config

# Initialize services (one-time setup)
python run.py --init-only

# Start development server
python run.py --dev
```

### 2. Development Mode Features

When running with `--dev` flag:
- Automatic ngrok tunnel creation
- Hot reload capabilities (when using uvicorn)
- Detailed logging
- Error stack traces

### 3. Environment Variables

**Required:**
- `API_KEY` - Wassenger API key
- `OPENAI_API_KEY` - OpenAI API key
- `NGROK_TOKEN` - Ngrok auth token (for development)

**Optional:**
- `OPENAI_MODEL` - OpenAI model (default: gpt-4o)
- `DEVICE` - Specific WhatsApp device ID
- `WEBHOOK_URL` - Production webhook URL
- `PORT` - Server port (default: 8080)
- `LOG_LEVEL` - Logging level (default: INFO)

### 4. Testing

```bash
# Run configuration validation
python run.py --validate-config

# Test API connections
python -m pytest tests/ -v

# Manual testing
curl http://localhost:8080/sample?phone=+1234567890
```

## Code Style and Conventions

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Use async/await for I/O operations
- Proper error handling with try/catch blocks

### Logging
- Use structured logging with context
- Different log levels for different scenarios
- Include relevant context in log messages

```python
AppLogger.info('Device loaded successfully', {
    'device_id': device['id'],
    'phone': device['phone'],
    'status': device['status']
})
```

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors with context
- Graceful degradation where possible

```python
try:
    result = await api_call()
except httpx.HTTPStatusError as e:
    AppLogger.error('API call failed', {
        'status_code': e.response.status_code,
        'error': str(e)
    })
    return None
```

## Adding New Features

### 1. Adding New API Endpoints

Add routes to `src/http/router.py`:

```python
@router.post('/new-endpoint')
async def new_endpoint(request: Request):
    # Implementation here
    pass
```

### 2. Extending Bot Functionality

Add methods to `src/bot/chatbot.py`:

```python
async def new_feature(self, data, device):
    # New bot feature implementation
    pass
```

### 3. Adding Configuration Options

Update `src/config/bot_config.py`:

```python
# Add new configuration constants
NEW_FEATURE_ENABLED = True

@staticmethod
def get_feature_config():
    return {
        'enabled': BotConfig.env('NEW_FEATURE_ENABLED', 'true').lower() == 'true'
    }
```

## Debugging

### 1. Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
python run.py --dev
```

### 2. Common Issues

**Device Not Found:**
- Check API key validity
- Verify device is connected and active
- Check device status in Wassenger dashboard

**Webhook Registration Failed:**
- Verify ngrok token is valid
- Check firewall settings
- Ensure webhook URL is publicly accessible

**OpenAI API Errors:**
- Verify OpenAI API key
- Check account credits/usage limits
- Monitor rate limiting

### 3. Monitoring

- Check logs in real-time: `tail -f bot.log`
- Monitor webhook delivery in Wassenger dashboard
- Use health check endpoint: `GET /health`

## Performance Considerations

### 1. Memory Management
- Use connection pooling for HTTP clients
- Implement proper caching with TTL
- Monitor memory usage in production

### 2. Rate Limiting
- Respect API rate limits
- Implement backoff strategies
- Queue messages during high load

### 3. Scalability
- Use async/await throughout
- Consider horizontal scaling for high volume
- Monitor response times and throughput

## Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] HTTPS webhook URL configured
- [ ] Logging configured for production
- [ ] Error monitoring setup
- [ ] Health checks implemented
- [ ] Backup and recovery plan

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY run.py .

CMD ["python", "run.py"]
```

### Environment-Specific Configuration

**Development:**
```bash
export DEV=true
export LOG_LEVEL=DEBUG
```

**Production:**
```bash
export NODE_ENV=production
export LOG_LEVEL=INFO
export WEBHOOK_URL=https://yourdomain.com/webhook
```
