from fastapi import FastAPI, Depends, Request, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from datetime import date, datetime

from .db import Base, engine, get_db
from . import schemas, crud, whatsapp
from .llm_client import parse_with_llm

app = FastAPI(title="WhatsApp Expense Bot")

Base.metadata.create_all(bind=engine)


def format_daily_summary(summary: dict) -> str:
    """Format daily summary for WhatsApp message."""
    return (
        f"📅 Daily Summary ({summary['date']})\n"
        f"Income: {summary['income']:.2f} CAD\n"
        f"Expenses: {summary['expenses']:.2f} CAD\n"
        f"Net: {summary['net']:.2f} CAD"
    )


def format_weekly_summary(summary: dict) -> str:
    """Format weekly summary for WhatsApp message."""
    return (
        f"📅 Weekly Summary ({summary['start_date']} to {summary['end_date']})\n"
        f"Income: {summary['income']:.2f} CAD\n"
        f"Expenses: {summary['expenses']:.2f} CAD\n"
        f"Net: {summary['net']:.2f} CAD"
    )


def format_monthly_summary(summary: dict) -> str:
    """Format monthly summary for WhatsApp message."""
    month_names = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    month_name = month_names[summary['month']]
    return (
        f"📅 Monthly Summary ({month_name} {summary['year']})\n"
        f"Income: {summary['income']:.2f} CAD\n"
        f"Expenses: {summary['expenses']:.2f} CAD\n"
        f"Net: {summary['net']:.2f} CAD"
    )


def format_category_breakdown(breakdown: list[dict]) -> str:
    """Format category breakdown for WhatsApp message."""
    if not breakdown:
        return "No transactions found in this period."
    
    lines = ["📊 Category Breakdown:\n"]
    for item in breakdown[:10]:  # Limit to top 10 categories
        cat = item['category']
        income = item['income']
        expenses = item['expenses']
        count = item['count']
        net = income - expenses
        
        lines.append(f"{cat}:")
        if income > 0:
            lines.append(f"  Income: {income:.2f} CAD")
        if expenses > 0:
            lines.append(f"  Expenses: {expenses:.2f} CAD")
        lines.append(f"  Net: {net:.2f} CAD ({count} transactions)\n")
    
    if len(breakdown) > 10:
        lines.append(f"... and {len(breakdown) - 10} more categories")
    
    return "".join(lines)


def format_trends(trends: list[dict], days: int) -> str:
    """Format spending trends for WhatsApp message."""
    if not trends:
        return f"No transaction data found for the last {days} days."
    
    total_income = sum(t['income'] for t in trends)
    total_expenses = sum(t['expenses'] for t in trends)
    avg_daily_expenses = total_expenses / len(trends) if trends else 0
    
    lines = [
        f"📈 Spending Trends (Last {days} days)\n",
        f"Total Income: {total_income:.2f} CAD\n",
        f"Total Expenses: {total_expenses:.2f} CAD\n",
        f"Average Daily Expenses: {avg_daily_expenses:.2f} CAD\n",
        f"Net: {total_income - total_expenses:.2f} CAD"
    ]
    
    return "".join(lines)


def format_stats(stats: dict) -> str:
    """Format transaction statistics for WhatsApp message."""
    return (
        f"📊 Transaction Statistics\n"
        f"Total Transactions: {stats['total_transactions']}\n"
        f"Income Transactions: {stats['income_count']}\n"
        f"Expense Transactions: {stats['expense_count']}\n"
        f"Average Income: {stats['average_income']:.2f} CAD\n"
        f"Average Expense: {stats['average_expense']:.2f} CAD\n"
        f"Largest Income: {stats['largest_income']:.2f} CAD\n"
        f"Largest Expense: {stats['largest_expense']:.2f} CAD"
    )


def parse_date(date_str: str | None) -> date | None:
    """Parse date string in ISO format."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).date()
    except (ValueError, AttributeError):
        return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/webhook/whatsapp", response_class=PlainTextResponse)
def whatsapp_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    return whatsapp.verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """WhatsApp webhook handler - uses tool functions for processing."""
    from app.mcp_tools import call_tool
    
    body = await request.json()

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])
    except (KeyError, IndexError, TypeError):
        return {"status": "ignored"}

    for msg in messages:
        from_phone = msg["from"]
        text = msg.get("text", {}).get("body", "").strip()

        # Parse with LLM (returns tool name + arguments)
        llm_result = parse_with_llm(text, from_phone)
        tool = llm_result.get("tool", "unknown")

        if tool == "unknown":
            error = llm_result.get("error", "I couldn't understand that.")
            examples = (
                "\nExamples:\n"
                "- I spent 30 dollars on food\n"
                "- I got paid 2000 salary\n"
                "- what is my balance?\n"
                "- show me today's expenses\n"
                "- weekly summary\n"
                "- monthly summary\n"
                "- how much did I spend on groceries?\n"
                "- spending trends last 7 days"
            )
            await whatsapp.send_whatsapp_text_message(from_phone, error + examples)
            continue

        # Call tool function
        try:
            response = await call_tool(tool, llm_result.get("arguments", {}))
            await whatsapp.send_whatsapp_text_message(from_phone, response)
        except Exception as e:
            await whatsapp.send_whatsapp_text_message(
                from_phone,
                f"I encountered an error: {str(e)}"
            )

    return {"status": "processed"}


@app.post("/api/transactions", response_model=schemas.TransactionRead)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction (expense or income)."""
    saved = crud.create_transaction(db, tx)
    return saved


@app.get("/transactions/{user_id}", response_model=list[schemas.TransactionRead])
def list_transactions(user_id: str, db: Session = Depends(get_db), limit: int = 20):
    return crud.get_transactions_by_user(db, user_id, limit=limit)


@app.get("/balance/{user_id}")
def get_balance(user_id: str, db: Session = Depends(get_db)):
    balance = crud.get_balance_by_user(db, user_id)
    return {"user_id": user_id, "balance": balance}


@app.get("/api/summaries/{user_id}/daily", response_model=schemas.DailySummary)
def get_daily_summary(
    user_id: str,
    target_date: date | None = Query(None, description="Date for summary (defaults to today)"),
    db: Session = Depends(get_db)
):
    """Get daily expense/income summary."""
    summary = crud.get_daily_summary(db, user_id, target_date)
    return schemas.DailySummary(**summary)


@app.get("/api/summaries/{user_id}/weekly", response_model=schemas.WeeklySummary)
def get_weekly_summary(
    user_id: str,
    start_date: date | None = Query(None, description="Start date of week (defaults to start of current week)"),
    db: Session = Depends(get_db)
):
    """Get weekly summary."""
    summary = crud.get_weekly_summary(db, user_id, start_date)
    return schemas.WeeklySummary(**summary)


@app.get("/api/summaries/{user_id}/monthly", response_model=schemas.MonthlySummary)
def get_monthly_summary(
    user_id: str,
    year: int | None = Query(None, description="Year (defaults to current year)"),
    month: int | None = Query(None, description="Month 1-12 (defaults to current month)"),
    db: Session = Depends(get_db)
):
    """Get monthly summary."""
    summary = crud.get_monthly_summary(db, user_id, year, month)
    return schemas.MonthlySummary(**summary)


@app.get("/api/summaries/{user_id}/by-category", response_model=list[schemas.CategoryBreakdown])
def get_category_breakdown(
    user_id: str,
    start_date: date | None = Query(None, description="Start date (defaults to 30 days ago)"),
    end_date: date | None = Query(None, description="End date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """Get category breakdown."""
    breakdown = crud.get_category_breakdown(db, user_id, start_date, end_date)
    return [schemas.CategoryBreakdown(**item) for item in breakdown]


@app.get("/api/summaries/{user_id}/trends", response_model=list[schemas.TrendData])
def get_spending_trends(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get spending trends over time."""
    trends = crud.get_spending_trends(db, user_id, days)
    return [schemas.TrendData(**item) for item in trends]


@app.get("/api/transactions/{user_id}/stats", response_model=schemas.TransactionStats)
def get_transaction_stats(user_id: str, db: Session = Depends(get_db)):
    """Get general transaction statistics."""
    stats = crud.get_transaction_stats(db, user_id)
    return schemas.TransactionStats(**stats)


@app.post("/api/chat", response_model=schemas.ChatResponse)
async def chat_bot(request: schemas.ChatRequest):
    """
    Chatbot endpoint that analyzes prompts and calls tool functions.
    
    Receives natural language message and returns formatted response.
    """
    from app.mcp_tools import call_tool
    
    # Parse message with LLM (returns tool name + arguments)
    llm_result = parse_with_llm(request.message, request.user_id)
    
    if llm_result.get("tool") == "unknown":
        error = llm_result.get("error", "I couldn't understand that.")
        examples = (
            "\n\nExamples:\n"
            "- I spent 30 dollars on food\n"
            "- I got paid 2000 salary\n"
            "- what is my balance?\n"
            "- show me today's expenses\n"
            "- weekly summary\n"
            "- monthly summary\n"
            "- how much did I spend on groceries?\n"
            "- spending trends last 7 days"
        )
        return {"response": error + examples}
    
    # Call tool function
    response = await call_tool(
        llm_result["tool"],
        llm_result.get("arguments", {})
    )
    
    return {"response": response}
