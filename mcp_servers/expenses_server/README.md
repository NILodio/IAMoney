# Expenses MCP Server

This MCP server exposes expense tracking functionality as MCP tools that can be called by AI assistants and other MCP clients. It acts as a lightweight HTTP client wrapper that calls the FastAPI REST API endpoints.

## Architecture

The MCP server **does not** directly access the database. Instead, it:
1. Receives MCP tool calls from AI assistants
2. Makes HTTP requests to the FastAPI REST API
3. Formats and returns responses to the AI assistant

This architecture ensures:
- ✅ Single source of truth (FastAPI handles all business logic)
- ✅ No code duplication
- ✅ FastAPI must be running for MCP server to work
- ✅ Easier to maintain and test

## Features

The server provides the following MCP tools:

- `create_expense` - Create a new expense transaction
- `create_income` - Create a new income transaction
- `get_balance` - Get current balance (income - expenses)
- `get_transactions` - List transactions with optional filters
- `get_daily_summary` - Get daily expense/income summary
- `get_weekly_summary` - Get weekly summary
- `get_monthly_summary` - Get monthly summary
- `get_category_breakdown` - Get category breakdown for a date range
- `get_spending_trends` - Get spending trends over time
- `get_transaction_stats` - Get general transaction statistics

## Prerequisites

**The FastAPI server must be running** before starting the MCP server. The MCP server connects to FastAPI via HTTP.

## Running the Servers

### Step 1: Start FastAPI Server

```bash
# Terminal 1
cd /Users/ddiaz/personal/IAMoney
uv run uvicorn app.main:app --reload --port 8000
```

### Step 2: Start MCP Server

```bash
# Terminal 2
cd /Users/ddiaz/personal/IAMoney
uv run python -m mcp_servers.expenses_server.server
```

## Configuration

The MCP server connects to FastAPI using the `API_BASE_URL` environment variable:

```bash
# Default: http://localhost:8000
export API_BASE_URL=http://localhost:8000

# Or set in .env file
API_BASE_URL=http://localhost:8000
```

## Integration

To use this MCP server with an MCP client (like Claude Desktop), add it to your MCP configuration:

```json
{
  "mcpServers": {
    "expenses-tracker": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_servers.expenses_server.server"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## How It Works

1. **LLM calls MCP tool** (e.g., "create_expense" with amount=50, category="groceries")
2. **MCP server receives tool call** via stdio
3. **MCP server makes HTTP POST** to `http://localhost:8000/api/transactions`
4. **FastAPI processes request** (validates, saves to database)
5. **FastAPI returns JSON response**
6. **MCP server formats response** and returns to LLM
7. **LLM presents result** to user

## Error Handling

The MCP server handles:
- Connection errors (FastAPI not running)
- HTTP errors (4xx, 5xx)
- Timeout errors
- Invalid responses

All errors are returned as user-friendly messages to the LLM.

