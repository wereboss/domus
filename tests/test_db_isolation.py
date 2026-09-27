from app.db.base import LogisticsBase, FinanceBase
from app.models.logistics import Task, Chore, Note
from app.models.finance import LedgerExpense, FixedBill
from app.models.member import HouseholdMember

def test_separate_database_tables(test_logistics_engine, test_finance_engine):
    """Verifies that Logistics tables and Finance tables reside in distinct database engines."""
    from sqlalchemy import inspect
    
    logistics_inspector = inspect(test_logistics_engine)
    logistics_tables = set(logistics_inspector.get_table_names())

    finance_inspector = inspect(test_finance_engine)
    finance_tables = set(finance_inspector.get_table_names())

    # Logistics DB must contain logistics tables and NO finance tables
    assert "household_members" in logistics_tables
    assert "tasks" in logistics_tables
    assert "chores" in logistics_tables
    assert "notes" in logistics_tables
    assert "ledger_expenses" not in logistics_tables
    assert "fixed_bills" not in logistics_tables

    # Finance DB must contain finance tables and NO logistics tables
    assert "ledger_expenses" in finance_tables
    assert "fixed_bills" in finance_tables
    assert "household_members" not in finance_tables
    assert "tasks" not in finance_tables
