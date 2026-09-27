from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.member import HouseholdMemberResponse

class PinLoginRequest(BaseModel):
    member_id: int
    pin: str = Field(..., min_length=4, max_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member: HouseholdMemberResponse
