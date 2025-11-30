"""
MCP Tool Functions - Reusable tool implementations.

These functions can be called directly by the bot or via MCP server.
Each function calls FastAPI endpoints and returns formatted string responses.
"""
import os
from typing import Any, Optional

import httpx
from app.config import settings

# Get API base URL from config or environment
API_BASE_URL = os.getenv("API_BASE_URL", getattr(settings, "API_BASE_URL", "http://localhost:8000"))


async def api_request(
    method: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make HTTP request to FastAPI endpoint."""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise Exception(
            f"Could not connect to FastAPI server at {API_BASE_URL}. "
            "Make sure the FastAPI server is running."
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        raise Exception(f"API error: {e.response.status_code} - {error_detail}")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")


async def create_expense(
    user_id: str,
    amount: float,
    currency: str = "CAD",
    category: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Create a new expense transaction."""
    tx_data = {
        "user_id": user_id,
        "type": "expense",
        "amount": float(amount),
        "currency": currency,
        "category": category,
        "description": description,
    }
    result = await api_request("POST", "/api/transactions", json_data=tx_data)
    return (
        f"✅ Created expense: {result['amount']} {result['currency']} "
        f"({result.get('category') or 'no category'})"
    )


async def create_income(
    user_id: str,
    amount: float,
    currency: str = "CAD",
    category: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Create a new income transaction."""
    tx_data = {
        "user_id": user_id,
        "type": "income",
        "amount": float(amount),
        "currency": currency,
        "category": category,
        "description": description,
    }
    result = await api_request("POST", "/api/transactions", json_data=tx_data)
    return (
        f"✅ Created income: {result['amount']} {result['currency']} "
        f"({result.get('category') or 'no category'})"
    )


async def get_balance(user_id: str) -> str:
    """Get current balance (income - expenses)."""
    result = await api_request("GET", f"/balance/{user_id}")
    balance = result["balance"]
    return f"Balance: {balance:.2f} CAD"


async def get_transactions(
    user_id: str,
    limit: int = 20,
    type_filter: Optional[str] = None,
) -> str:
    """List transactions for a user."""
    params = {"limit": limit}
    result = await api_request("GET", f"/transactions/{user_id}", params=params)

    if type_filter:
        result = [t for t in result if t["type"] == type_filter]

    if not result:
        return "No transactions found."

    lines = ["Transactions:\n"]
    for tx in result:
        created_at = tx["created_at"]
        if isinstance(created_at, str):
            dt_str = created_at.split("T")[0] + " " + created_at.split("T")[1][:5]
        else:
            dt_str = str(created_at)
        lines.append(
            f"- {tx['type']}: {tx['amount']} {tx['currency']} "
            f"({tx.get('category') or 'no category'}) - {dt_str}"
        )
    return "\n".join(lines)


async def get_daily_summary(
    user_id: str,
    date: Optional[str] = None,
) -> str:
    """Get daily expense/income summary."""
    params = {}
    if date:
        params["target_date"] = date
    result = await api_request(
        "GET",
        f"/api/summaries/{user_id}/daily",
        params=params
    )
    return (
        f"📅 Daily Summary ({result['date']}):\n"
        f"Income: {result['income']:.2f} CAD\n"
        f"Expenses: {result['expenses']:.2f} CAD\n"
        f"Net: {result['net']:.2f} CAD"
    )


async def get_weekly_summary(
    user_id: str,
    start_date: Optional[str] = None,
) -> str:
    """Get weekly summary."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    result = await api_request(
        "GET",
        f"/api/summaries/{user_id}/weekly",
        params=params
    )
    return (
        f"📅 Weekly Summary ({result['start_date']} to {result['end_date']}):\n"
        f"Income: {result['income']:.2f} CAD\n"
        f"Expenses: {result['expenses']:.2f} CAD\n"
        f"Net: {result['net']:.2f} CAD"
    )


async def get_monthly_summary(
    user_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """Get monthly summary."""
    params = {}
    if year:
        params["year"] = year
    if month:
        params["month"] = month
    result = await api_request(
        "GET",
        f"/api/summaries/{user_id}/monthly",
        params=params
    )
    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_name = month_names[result["month"]]
    return (
        f"📅 Monthly Summary ({month_name} {result['year']}):\n"
        f"Income: {result['income']:.2f} CAD\n"
        f"Expenses: {result['expenses']:.2f} CAD\n"
        f"Net: {result['net']:.2f} CAD"
    )


async def get_category_breakdown(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Get category breakdown for a date range."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    result = await api_request(
        "GET",
        f"/api/summaries/{user_id}/by-category",
        params=params
    )

    if not result:
        return "No transactions found in this period."

    lines = ["📊 Category Breakdown:\n"]
    for item in result[:10]:
        cat = item["category"]
        income = item["income"]
        expenses = item["expenses"]
        count = item["count"]
        net = income - expenses
        lines.append(
            f"{cat}: Income {income:.2f}, Expenses {expenses:.2f}, "
            f"Net {net:.2f} ({count} transactions)"
        )

    return "\n".join(lines)


async def get_spending_trends(
    user_id: str,
    days: int = 30,
) -> str:
    """Get spending trends over the last N days."""
    params = {"days": days}
    result = await api_request(
        "GET",
        f"/api/summaries/{user_id}/trends",
        params=params
    )

    if not result:
        return f"No transaction data found for the last {days} days."

    total_income = sum(t["income"] for t in result)
    total_expenses = sum(t["expenses"] for t in result)
    avg_daily_expenses = total_expenses / len(result) if result else 0

    return (
        f"📈 Spending Trends (Last {days} days):\n"
        f"Total Income: {total_income:.2f} CAD\n"
        f"Total Expenses: {total_expenses:.2f} CAD\n"
        f"Average Daily Expenses: {avg_daily_expenses:.2f} CAD\n"
        f"Net: {total_income - total_expenses:.2f} CAD"
    )


async def get_transaction_stats(user_id: str) -> str:
    """Get general transaction statistics."""
    result = await api_request(
        "GET",
        f"/api/transactions/{user_id}/stats"
    )
    return (
        f"📊 Transaction Statistics:\n"
        f"Total Transactions: {result['total_transactions']}\n"
        f"Income Transactions: {result['income_count']}\n"
        f"Expense Transactions: {result['expense_count']}\n"
        f"Average Income: {result['average_income']:.2f} CAD\n"
        f"Average Expense: {result['average_expense']:.2f} CAD\n"
        f"Largest Income: {result['largest_income']:.2f} CAD\n"
        f"Largest Expense: {result['largest_expense']:.2f} CAD"
    )


# Tool Registry
TOOLS = {
    "create_expense": create_expense,
    "create_income": create_income,
    "get_balance": get_balance,
    "get_transactions": get_transactions,
    "get_daily_summary": get_daily_summary,
    "get_weekly_summary": get_weekly_summary,
    "get_monthly_summary": get_monthly_summary,
    "get_category_breakdown": get_category_breakdown,
    "get_spending_trends": get_spending_trends,
    "get_transaction_stats": get_transaction_stats,
}


async def call_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Call tool by name with arguments.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Formatted string response from the tool
    """
    tool_func = TOOLS.get(tool_name)
    if not tool_func:
        return f"Error: Unknown tool '{tool_name}'"
    try:
        return await tool_func(**arguments)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

