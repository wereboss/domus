from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# Ledger Expense Schemas
class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(default="General", max_length=64)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    payment_method: str = Field(default="Card", max_length=32)
    payer_member_id: Optional[int] = None
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Fixed Bill Schemas
class BillBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(default="Utilities", max_length=64)
    recurrence: str = Field(default="monthly", pattern=r"^(monthly|quarterly|annual)$")
    due_day_of_month: int = Field(..., ge=1, le=31)
    is_auto_pay: bool = False

class BillCreate(BillBase):
    pass

class BillResponse(BillBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
