from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class HouseholdMemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    avatar_color: str = Field(default="#3b82f6", max_length=16)

class HouseholdMemberCreate(HouseholdMemberBase):
    pin: str = Field(..., min_length=4, max_length=8)

class HouseholdMemberResponse(HouseholdMemberBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
