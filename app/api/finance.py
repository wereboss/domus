from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.finance import get_finance_db
from app.models.finance import LedgerExpense, FixedBill
from app.schemas.finance import ExpenseCreate, ExpenseResponse, BillCreate, BillResponse

router = APIRouter(prefix="/api", tags=["Finances"])

# ================= Ledger Expenses =================
@router.get("/expenses", response_model=List[ExpenseResponse])
def list_expenses(
    date: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_finance_db)
):
    """Lists expenses from finance.db with optional date or category filter."""
    query = db.query(LedgerExpense)
    if date:
        query = query.filter(LedgerExpense.date == date)
    if category:
        query = query.filter(LedgerExpense.category == category)
    return query.order_by(LedgerExpense.date.desc(), LedgerExpense.id.desc()).all()

@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_finance_db)):
    """Logs a new expense into finance.db."""
    expense = LedgerExpense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_finance_db)):
    """Deletes an expense entry."""
    expense = db.query(LedgerExpense).filter(LedgerExpense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return None

# ================= Fixed Bills =================
@router.get("/bills", response_model=List[BillResponse])
def list_bills(db: Session = Depends(get_finance_db)):
    """Lists all recurring / fixed commitments."""
    return db.query(FixedBill).filter(FixedBill.is_active == True).order_by(FixedBill.due_day_of_month.asc()).all()

@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(payload: BillCreate, db: Session = Depends(get_finance_db)):
    """Adds a fixed / recurring bill into finance.db."""
    bill = FixedBill(**payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill

@router.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: int, db: Session = Depends(get_finance_db)):
    """Deletes a fixed bill."""
    bill = db.query(FixedBill).filter(FixedBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return None
