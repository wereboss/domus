from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.member import HouseholdMemberResponse

class InboxItemBase(BaseModel):
    source: str = "share_target"
    item_type: str = "text"
    title: Optional[str] = None
    raw_content: Optional[str] = None

class InboxItemCreate(InboxItemBase):
    pass

class InboxItemResponse(InboxItemBase):
    id: int
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_mime_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    suggested_action: str
    status: str
    captured_by_id: Optional[int] = None
    created_at: datetime
    captured_by: Optional[HouseholdMemberResponse] = None

    model_config = ConfigDict(from_attributes=True)

class InboxCountResponse(BaseModel):
    pending_count: int

class InboxTriageRequest(BaseModel):
    target_type: Literal["task", "expense", "note"]
    title: str = Field(..., min_length=1, max_length=255)
    
    # Task specific
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Optional[str] = "normal"
    assigned_to_id: Optional[int] = None

    # Expense specific
    amount: Optional[float] = None
    category: Optional[str] = "General"
    payment_method: Optional[str] = "Card"

    # Note specific
    content: Optional[str] = None
