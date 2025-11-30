from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class TransactionBase(BaseModel):
    user_id: str
    type: Literal["income", "expense"]
    amount: float
    currency: str = "CAD"
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    raw_message: Optional[str] = None


class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    raw_message: Optional[str]

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    """Base summary structure."""
    income: float
    expenses: float
    net: float


class DailySummary(SummaryResponse):
    """Daily summary response."""
    date: str


class WeeklySummary(SummaryResponse):
    """Weekly summary response."""
    start_date: str
    end_date: str


class MonthlySummary(SummaryResponse):
    """Monthly summary response."""
    year: int
    month: int


class CategoryBreakdown(BaseModel):
    """Category breakdown item."""
    category: str
    income: float
    expenses: float
    count: int


class TrendData(BaseModel):
    """Time series data point for trends."""
    date: str
    income: float
    expenses: float


class TransactionStats(BaseModel):
    """Statistical aggregations."""
    total_transactions: int
    income_count: int
    expense_count: int
    average_income: float
    average_expense: float
    largest_income: float
    largest_expense: float


class ChatRequest(BaseModel):
    """Chat bot request."""
    message: str
    user_id: str


class ChatResponse(BaseModel):
    """Chat bot response."""
    response: str
