from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.logistics import Task, Chore
from app.models.finance import FixedBill, LedgerExpense
from app.models.member import HouseholdMember
from app.schemas.timeline import TimelineItem, TimelineSummary, TimelineDayResponse

def get_day_timeline(
    target_date: str,
    logistics_db: Session,
    finance_db: Session,
    current_member: Optional[HouseholdMember] = None,
    filter_view: str = "all"  # "all" or "mine"
) -> TimelineDayResponse:
    """Interleaves logistics tasks/chores and financial commitments for target_date (YYYY-MM-DD)."""
    items: List[TimelineItem] = []
    
    # Parse target date to get day-of-month for recurring bills
    parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    target_day_of_month = parsed_date.day
    today_str = date.today().isoformat()

    # Cache members for quick lookup
    members = {m.id: m for m in logistics_db.query(HouseholdMember).all()}

    # 1. Fetch Logistics Tasks
    task_query = logistics_db.query(Task)
    if filter_view == "mine" and current_member:
        task_query = task_query.filter(
            (Task.assigned_to_id == current_member.id) | (Task.assigned_to_id.is_(None))
        )
    
    # Tasks due today or overdue
    all_relevant_tasks = task_query.filter(
        (Task.due_date == target_date) | 
        ((Task.due_date < target_date) & (Task.is_completed == False))
    ).all()

    total_tasks = 0
    completed_tasks = 0

    for task in all_relevant_tasks:
        is_overdue = (task.due_date < target_date) and not task.is_completed
        if task.due_date == target_date:
            total_tasks += 1
            if task.is_completed:
                completed_tasks += 1

        assignee_name = "Shared"
        badge_color = "#64748b"
        if task.assigned_to_id and task.assigned_to_id in members:
            assignee = members[task.assigned_to_id]
            assignee_name = assignee.name
            badge_color = assignee.avatar_color

        items.append(
            TimelineItem(
                id=f"task-{task.id}",
                item_type="task",
                title=task.title,
                time_str=task.due_time,
                amount=None,
                category=task.priority,
                badge=assignee_name,
                badge_color=badge_color,
                is_completed=task.is_completed,
                is_overdue=is_overdue,
                severity="urgent" if (is_overdue or task.priority == "urgent") else "normal"
            )
        )

    # 2. Fetch Recurring Chores due on target_date
    chore_query = logistics_db.query(Chore).filter(
        Chore.is_active == True,
        Chore.next_due_date <= target_date
    )
    if filter_view == "mine" and current_member:
        chore_query = chore_query.filter(
            (Chore.assigned_to_id == current_member.id) | (Chore.assigned_to_id.is_(None))
        )
    
    for chore in chore_query.all():
        assignee_name = "Shared"
        badge_color = "#64748b"
        if chore.assigned_to_id and chore.assigned_to_id in members:
            assignee = members[chore.assigned_to_id]
            assignee_name = assignee.name
            badge_color = assignee.avatar_color
            
        items.append(
            TimelineItem(
                id=f"chore-{chore.id}",
                item_type="chore",
                title=chore.title,
                time_str=None,
                amount=None,
                category=chore.recurrence,
                badge=assignee_name,
                badge_color=badge_color,
                is_completed=False,
                is_overdue=(chore.next_due_date < target_date),
                severity="normal"
            )
        )

    # 3. Fetch Fixed Bills due on target_day_of_month
    due_bills = finance_db.query(FixedBill).filter(
        FixedBill.is_active == True,
        FixedBill.due_day_of_month == target_day_of_month
    ).all()

    total_due_bills_amount = 0.0
    for bill in due_bills:
        total_due_bills_amount += bill.amount
        items.append(
            TimelineItem(
                id=f"bill-{bill.id}",
                item_type="bill",
                title=bill.title,
                time_str=None,
                amount=bill.amount,
                category=bill.category,
                badge="Auto-Pay" if bill.is_auto_pay else "Due Today",
                badge_color="#10b981" if bill.is_auto_pay else "#f59e0b",
                is_completed=bill.is_auto_pay,
                is_overdue=False,
                severity="due_today"
            )
        )

    # 4. Fetch Ledger Expenses incurred on target_date
    expenses = finance_db.query(LedgerExpense).filter(
        LedgerExpense.date == target_date
    ).all()

    total_spent_today = 0.0
    for expense in expenses:
        total_spent_today += expense.amount
        payer_badge = "Household"
        badge_color = "#64748b"
        if expense.payer_member_id and expense.payer_member_id in members:
            payer = members[expense.payer_member_id]
            payer_badge = payer.name
            badge_color = payer.avatar_color

        items.append(
            TimelineItem(
                id=f"expense-{expense.id}",
                item_type="expense",
                title=expense.title,
                time_str=None,
                amount=expense.amount,
                category=expense.category,
                badge=payer_badge,
                badge_color=badge_color,
                is_completed=True,
                is_overdue=False,
                severity="info"
            )
        )

    # Chronological sort: Overdue -> Bills -> Timed Tasks -> Anytime Tasks/Chores -> Expenses
    def sort_key(item: TimelineItem):
        if item.is_overdue:
            return (0, "")
        if item.item_type == "bill":
            return (1, "")
        if item.time_str:
            return (2, item.time_str)
        if item.item_type in ("task", "chore"):
            return (3, "")
        return (4, "")

    items.sort(key=sort_key)

    summary = TimelineSummary(
        date=target_date,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_due_bills_amount=round(total_due_bills_amount, 2),
        total_spent_today=round(total_spent_today, 2)
    )

    return TimelineDayResponse(date=target_date, summary=summary, items=items)
