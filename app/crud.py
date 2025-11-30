from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import datetime, date, timedelta
from typing import Optional
from . import models, schemas


def create_transaction(db: Session, tx: schemas.TransactionCreate) -> models.Transaction:
    db_tx = models.Transaction(
        user_id=tx.user_id,
        type=tx.type,
        amount=tx.amount,
        currency=tx.currency,
        category=tx.category,
        description=tx.description,
        raw_message=tx.raw_message,
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx


def get_transactions_by_user(db: Session, user_id: str, limit: int = 50):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


def get_balance_by_user(db: Session, user_id: str) -> float:
    total = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            models.Transaction.type
                            == models.TransactionType.INCOME,
                            models.Transaction.amount
                        ),
                        else_=-models.Transaction.amount,
                    )
                ),
                0.0,
            )
        )
        .filter(models.Transaction.user_id == user_id)
        .scalar()
    )
    return float(total or 0.0)


def get_daily_summary(
    db: Session, user_id: str, target_date: Optional[date] = None
) -> dict:
    """Get daily summary for a specific date (defaults to today)."""
    if target_date is None:
        target_date = date.today()

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    query = (
        db.query(
            models.Transaction.type,
            func.sum(models.Transaction.amount).label("total")
        )
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.created_at >= start_of_day,
                models.Transaction.created_at <= end_of_day
            )
        )
        .group_by(models.Transaction.type)
    )
    
    results = query.all()
    
    income = sum(r.total for r in results if r.type == models.TransactionType.INCOME)
    expenses = sum(r.total for r in results if r.type == models.TransactionType.EXPENSE)
    
    return {
        "date": target_date.isoformat(),
        "income": float(income or 0.0),
        "expenses": float(expenses or 0.0),
        "net": float((income or 0.0) - (expenses or 0.0))
    }


def get_weekly_summary(
    db: Session, user_id: str, start_date: Optional[date] = None
) -> dict:
    """Get weekly summary from start_date (defaults to start of week)."""
    if start_date is None:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())

    end_date = start_date + timedelta(days=6)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    query = (
        db.query(
            models.Transaction.type,
            func.sum(models.Transaction.amount).label("total")
        )
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.created_at >= start_datetime,
                models.Transaction.created_at <= end_datetime
            )
        )
        .group_by(models.Transaction.type)
    )
    
    results = query.all()
    
    income = sum(r.total for r in results if r.type == models.TransactionType.INCOME)
    expenses = sum(r.total for r in results if r.type == models.TransactionType.EXPENSE)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "income": float(income or 0.0),
        "expenses": float(expenses or 0.0),
        "net": float((income or 0.0) - (expenses or 0.0))
    }


def get_monthly_summary(
    db: Session,
    user_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> dict:
    """Get monthly summary for year/month (defaults to current month)."""
    if year is None or month is None:
        today = date.today()
        year = year or today.year
        month = month or today.month

    start_datetime = datetime(year, month, 1)
    if month == 12:
        end_datetime = datetime(
            year + 1, 1, 1
        ) - timedelta(seconds=1)
    else:
        end_datetime = datetime(
            year, month + 1, 1
        ) - timedelta(seconds=1)
    
    query = (
        db.query(
            models.Transaction.type,
            func.sum(models.Transaction.amount).label("total")
        )
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.created_at >= start_datetime,
                models.Transaction.created_at <= end_datetime
            )
        )
        .group_by(models.Transaction.type)
    )
    
    results = query.all()
    
    income = sum(r.total for r in results if r.type == models.TransactionType.INCOME)
    expenses = sum(r.total for r in results if r.type == models.TransactionType.EXPENSE)
    
    return {
        "year": year,
        "month": month,
        "income": float(income or 0.0),
        "expenses": float(expenses or 0.0),
        "net": float((income or 0.0) - (expenses or 0.0))
    }


def get_category_breakdown(
    db: Session,
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[dict]:
    """Get category breakdown for date range (defaults to last 30 days)."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    query = (
        db.query(
            models.Transaction.category,
            models.Transaction.type,
            func.sum(models.Transaction.amount).label("total"),
            func.count(models.Transaction.id).label("count")
        )
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.created_at >= start_datetime,
                models.Transaction.created_at <= end_datetime
            )
        )
        .group_by(models.Transaction.category, models.Transaction.type)
    )
    
    results = query.all()
    
    category_map = {}
    for r in results:
        cat = r.category or "uncategorized"
        if cat not in category_map:
            category_map[cat] = {"category": cat, "income": 0.0, "expenses": 0.0, "count": 0}
        
        if r.type == models.TransactionType.INCOME:
            category_map[cat]["income"] += float(r.total or 0.0)
        else:
            category_map[cat]["expenses"] += float(r.total or 0.0)
        category_map[cat]["count"] += r.count
    
    return list(category_map.values())


def get_spending_trends(db: Session, user_id: str, days: int = 30) -> list[dict]:
    """Get spending trends over the last N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    query = (
        db.query(
            func.date(models.Transaction.created_at).label("date"),
            models.Transaction.type,
            func.sum(models.Transaction.amount).label("total")
        )
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.created_at >= start_datetime,
                models.Transaction.created_at <= end_datetime
            )
        )
        .group_by(func.date(models.Transaction.created_at), models.Transaction.type)
        .order_by(func.date(models.Transaction.created_at))
    )
    
    results = query.all()
    
    # Group by date
    date_map = {}
    for r in results:
        date_str = r.date.isoformat() if isinstance(r.date, date) else str(r.date)
        if date_str not in date_map:
            date_map[date_str] = {"date": date_str, "income": 0.0, "expenses": 0.0}
        
        if r.type == models.TransactionType.INCOME:
            date_map[date_str]["income"] += float(r.total or 0.0)
        else:
            date_map[date_str]["expenses"] += float(r.total or 0.0)
    
    return [date_map[date_str] for date_str in sorted(date_map.keys())]


def get_transaction_stats(db: Session, user_id: str) -> dict:
    """Get general statistics about transactions."""
    total_count = (
        db.query(func.count(models.Transaction.id))
        .filter(models.Transaction.user_id == user_id)
        .scalar()
    )
    
    income_count = (
        db.query(func.count(models.Transaction.id))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.INCOME
            )
        )
        .scalar()
    )
    
    expense_count = (
        db.query(func.count(models.Transaction.id))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.EXPENSE
            )
        )
        .scalar()
    )
    
    avg_income = (
        db.query(func.avg(models.Transaction.amount))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.INCOME
            )
        )
        .scalar()
    )
    
    avg_expense = (
        db.query(func.avg(models.Transaction.amount))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.EXPENSE
            )
        )
        .scalar()
    )
    
    largest_income = (
        db.query(func.max(models.Transaction.amount))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.INCOME
            )
        )
        .scalar()
    )
    
    largest_expense = (
        db.query(func.max(models.Transaction.amount))
        .filter(
            and_(
                models.Transaction.user_id == user_id,
                models.Transaction.type == models.TransactionType.EXPENSE
            )
        )
        .scalar()
    )
    
    return {
        "total_transactions": total_count or 0,
        "income_count": income_count or 0,
        "expense_count": expense_count or 0,
        "average_income": float(avg_income or 0.0),
        "average_expense": float(avg_expense or 0.0),
        "largest_income": float(largest_income or 0.0),
        "largest_expense": float(largest_expense or 0.0)
    }
