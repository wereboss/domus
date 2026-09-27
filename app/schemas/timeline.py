from typing import Optional, List
from pydantic import BaseModel

class TimelineItem(BaseModel):
    id: str                          # e.g., "task-1", "bill-2", "chore-3"
    item_type: str                   # "task", "chore", "bill", "expense"
    title: str
    time_str: Optional[str] = None   # "14:30" (24h) or None for all-day
    amount: Optional[float] = None   # for bills and expenses ($)
    category: Optional[str] = None
    badge: Optional[str] = None      # Assignee name (e.g. "Mom") or "Shared"
    badge_color: Optional[str] = None
    is_completed: bool = False
    is_overdue: bool = False
    severity: str = "normal"         # "normal", "urgent", "info", "due_today"

class TimelineSummary(BaseModel):
    date: str
    total_tasks: int
    completed_tasks: int
    total_due_bills_amount: float
    total_spent_today: float

class TimelineDayResponse(BaseModel):
    date: str
    summary: TimelineSummary
    items: List[TimelineItem]
