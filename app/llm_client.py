import json
from typing import Literal, Optional, TypedDict, Any

from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class LLMParseResult(TypedDict, total=False):
    tool: Literal[
        "create_expense",
        "create_income",
        "get_balance",
        "get_transactions",
        "get_daily_summary",
        "get_weekly_summary",
        "get_monthly_summary",
        "get_category_breakdown",
        "get_spending_trends",
        "get_transaction_stats",
        "unknown"
    ]
    arguments: dict[str, Any]  # Tool arguments
    error: Optional[str]


SYSTEM_PROMPT = """
You are an assistant for a personal finance bot.

Your job:
- Understand user messages about expenses, income, balance queries, and summary requests.
- Return a STRICT JSON object with this shape:

{
  "tool": "create_expense" | "create_income" | "get_balance" | "get_transactions" | "get_daily_summary" | "get_weekly_summary" | "get_monthly_summary" | "get_category_breakdown" | "get_spending_trends" | "get_transaction_stats" | "unknown",
  "arguments": {
    "user_id": string (will be provided separately),
    // For create_expense/create_income:
    "amount": float (required),
    "currency": string (default: "CAD"),
    "category": string | null,
    "description": string | null,
    // For get_daily_summary:
    "date": string | null (ISO format YYYY-MM-DD, null = today),
    // For get_weekly_summary:
    "start_date": string | null (ISO format YYYY-MM-DD, null = start of current week),
    // For get_monthly_summary:
    "year": number | null (null = current year),
    "month": number | null (1-12, null = current month),
    // For get_category_breakdown:
    "start_date": string | null (ISO format, null = 30 days ago),
    "end_date": string | null (ISO format, null = today),
    // For get_spending_trends:
    "days": number | null (default: 30),
    // For get_transactions:
    "limit": number | null (default: 20),
    "type_filter": "income" | "expense" | null
  },
  "error": string | null
}

Rules:
- If the user records an EXPENSE, use "create_expense" tool.
- If the user records INCOME, use "create_income" tool.
- Default currency is "CAD" unless explicitly mentioned.
- amount must be numeric only (no "$").
- If user asks about balance, use "get_balance" tool (no arguments needed except user_id).
- For daily summaries: use "get_daily_summary". Include "date" in arguments if mentioned.
- For weekly summaries: use "get_weekly_summary". Include "start_date" in arguments if mentioned.
- For monthly summaries: use "get_monthly_summary". Include "year" and/or "month" in arguments if mentioned.
- For category breakdowns: use "get_category_breakdown". Include date range in arguments if mentioned.
- For spending trends: use "get_spending_trends". Include "days" in arguments if mentioned.
- For transaction lists: use "get_transactions". Include "limit" and/or "type_filter" if mentioned.
- For general stats: use "get_transaction_stats" (no arguments except user_id).
- If you can't interpret the message, tool = "unknown" and fill error.

Examples:
- "I spent 30 dollars on food" -> {"tool": "create_expense", "arguments": {"amount": 30, "currency": "USD", "category": "food"}}
- "I got paid 2000" -> {"tool": "create_income", "arguments": {"amount": 2000, "currency": "CAD"}}
- "what is my balance?" -> {"tool": "get_balance", "arguments": {}}
- "show me today's expenses" -> {"tool": "get_daily_summary", "arguments": {}}
- "what did I spend last week?" -> {"tool": "get_weekly_summary", "arguments": {}}
- "monthly summary" -> {"tool": "get_monthly_summary", "arguments": {}}
- "how much on groceries?" -> {"tool": "get_category_breakdown", "arguments": {"category": "groceries"}}
- "spending trends last 7 days" -> {"tool": "get_spending_trends", "arguments": {"days": 7}}
"""


def choose_model(message: str) -> str:
    length = len(message)
    if length < 80:
        return "gpt-4.1-mini"
    else:
        return "gpt-4.1-mini"  # you can switch to gpt-4.1 later if needed


def parse_with_llm(message: str, user_id: str) -> LLMParseResult:
    """
    Parse user message with LLM and return tool name and arguments.
    
    Args:
        message: User's natural language message
        user_id: User identifier
        
    Returns:
        LLMParseResult with tool name and arguments dict
    """
    model = choose_model(message)

    completion = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {
                "role": "user",
                "content": f"User ID: {user_id}\nMessage: {message}",
            },
        ],
    )

    raw = completion.choices[0].message.content

    try:
        data = json.loads(raw)
    except Exception as e:
        return {
            "tool": "unknown",
            "arguments": {},
            "error": f"Failed to parse LLM JSON: {e}",
        }

    # Extract tool name
    tool = data.get("tool", "unknown")
    
    # Extract arguments and add user_id
    arguments = data.get("arguments", {})
    arguments["user_id"] = user_id
    
    return {
        "tool": tool,
        "arguments": arguments,
        "error": data.get("error"),
    }
