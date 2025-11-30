"""
MCP Server for Expense Tracking.

This server exposes expense tracking functionality as MCP tools that can be called
by AI assistants and other MCP clients. It uses the shared tool functions from
app.mcp_tools, which call FastAPI REST API endpoints.
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# MCP imports (must be after sys.path modification)
from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import Tool, TextContent  # noqa: E402

# App imports
from app.mcp_tools import call_tool  # noqa: E402

app = Server("expenses-tracker")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="create_expense",
            description="Create a new expense transaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Expense amount"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (default: CAD)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Expense category"
                    },
                    "description": {
                        "type": "string",
                        "description": "Transaction description"
                    },
                },
                "required": ["user_id", "amount"],
            },
        ),
        Tool(
            name="create_income",
            description="Create a new income transaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Income amount"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (default: CAD)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Income category"
                    },
                    "description": {
                        "type": "string",
                        "description": "Transaction description"
                    },
                },
                "required": ["user_id", "amount"],
            },
        ),
        Tool(
            name="get_balance",
            description="Get current balance (income - expenses) for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_transactions",
            description="List transactions for a user with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions (default: 20)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Filter by transaction type"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_daily_summary",
            description="Get daily expense/income summary for a specific date",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in ISO format YYYY-MM-DD (default: today)"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_weekly_summary",
            description="Get weekly summary starting from a specific date",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format YYYY-MM-DD (default: start of current week)"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_monthly_summary",
            description="Get monthly summary for a specific year and month",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Year (default: current year)"
                    },
                    "month": {
                        "type": "integer",
                        "description": "Month 1-12 (default: current month)"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_category_breakdown",
            description="Get category breakdown for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format YYYY-MM-DD (default: 30 days ago)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format YYYY-MM-DD (default: today)"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_spending_trends",
            description="Get spending trends over the last N days",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30)"
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_transaction_stats",
            description="Get general transaction statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool_handler(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle MCP tool calls by delegating to shared tool functions.
    
    This is a thin wrapper that calls the shared tool functions from app.mcp_tools
    and wraps the response in MCP TextContent format.
    """
    try:
        # Handle type_filter parameter for get_transactions
        if name == "get_transactions" and "type" in arguments:
            arguments["type_filter"] = arguments.pop("type")
        
        # Call the shared tool function
        result = await call_tool(name, arguments)
        
        # Wrap response in MCP TextContent format
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
