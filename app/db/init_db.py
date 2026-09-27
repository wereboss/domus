from datetime import date
from app.db.base import LogisticsBase, FinanceBase
from app.db.logistics import logistics_engine, LogisticsSessionLocal
from app.db.finance import finance_engine, FinanceSessionLocal
from app.models.member import HouseholdMember
from app.models.logistics import Task, Chore, Note
from app.models.finance import LedgerExpense, FixedBill
from app.auth.pin import hash_pin

def init_databases():
    """Initializes schemas in logistics.db and finance.db, and seeds default profiles and baseline data."""
    # Create tables in Logistics DB
    LogisticsBase.metadata.create_all(bind=logistics_engine)
    
    # Create tables in Finance DB
    FinanceBase.metadata.create_all(bind=finance_engine)
    
    today_str = date.today().isoformat()
    today_day = date.today().day

    # Seed Logistics DB
    log_db = LogisticsSessionLocal()
    try:
        if log_db.query(HouseholdMember).count() == 0:
            mom = HouseholdMember(
                name="Mom",
                pin_hash=hash_pin("1234"),
                avatar_color="#ec4899"
            )
            dad = HouseholdMember(
                name="Dad",
                pin_hash=hash_pin("5678"),
                avatar_color="#3b82f6"
            )
            log_db.add_all([mom, dad])
            log_db.commit()

            # Seed sample task and chore
            sample_task = Task(
                title="Pick up school supplies & snacks",
                assigned_to_id=mom.id,
                due_date=today_str,
                due_time="15:00",
                priority="normal"
            )
            sample_chore = Chore(
                title="Take out recycling & compost bins",
                recurrence="weekly",
                assigned_to_id=dad.id,
                next_due_date=today_str
            )
            sample_note = Note(
                title="Wi-Fi Password & Home Network",
                content="SSID: DomusHome-5G / Key: HomeSweetHome2026",
                category="Household",
                author_id=dad.id
            )
            log_db.add_all([sample_task, sample_chore, sample_note])
            log_db.commit()
            print("Seeded default household members, starter task, chore, and note.")
    finally:
        log_db.close()

    # Seed Finance DB
    fin_db = FinanceSessionLocal()
    try:
        if fin_db.query(FixedBill).count() == 0:
            sample_bill = FixedBill(
                title="Gigabit Fiber Internet",
                amount=70.00,
                category="Utilities",
                recurrence="monthly",
                due_day_of_month=today_day,
                is_auto_pay=False
            )
            fin_db.add(sample_bill)
            fin_db.commit()
            print("Seeded starter fixed recurring bill.")
    finally:
        fin_db.close()

if __name__ == "__main__":
    init_databases()
