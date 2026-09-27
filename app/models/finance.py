from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base import FinanceBase

class LedgerExpense(FinanceBase):
    __tablename__ = "ledger_expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(64), default="General", nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    payment_method = Column(String(32), default="Card", nullable=False)
    # Note: payer_member_id is intentionally an unconstrained integer reference to preserve DB isolation
    payer_member_id = Column(Integer, nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FixedBill(FinanceBase):
    __tablename__ = "fixed_bills"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(64), default="Utilities", nullable=False)
    recurrence = Column(String(32), default="monthly", nullable=False)  # monthly, quarterly, annual
    due_day_of_month = Column(Integer, nullable=False)                  # 1 - 31
    is_auto_pay = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
