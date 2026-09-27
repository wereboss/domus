from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.member import HouseholdMemberResponse

# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    due_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")  # HH:MM (24h)
    priority: str = Field(default="normal", pattern=r"^(low|normal|urgent)$")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    is_completed: Optional[bool] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    assigned_to: Optional[HouseholdMemberResponse] = None

    model_config = ConfigDict(from_attributes=True)

# Chore Schemas
class ChoreBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    recurrence: str = Field(default="daily", pattern=r"^(daily|weekly|biweekly|monthly)$")
    assigned_to_id: Optional[int] = None
    next_due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

class ChoreCreate(ChoreBase):
    pass

class ChoreResponse(ChoreBase):
    id: int
    is_active: bool
    last_completed_at: Optional[datetime] = None
    created_at: datetime
    assigned_to: Optional[HouseholdMemberResponse] = None

    model_config = ConfigDict(from_attributes=True)

# Note Schemas
class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    category: str = Field(default="General", max_length=64)
    attachment_path: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    author_id: Optional[int] = None
    attachment_path: Optional[str] = None
    created_at: datetime
    author: Optional[HouseholdMemberResponse] = None

    model_config = ConfigDict(from_attributes=True)
