from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.sql import func
import enum
from .db import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    type = Column(Enum(TransactionType), index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="CAD")
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    raw_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
