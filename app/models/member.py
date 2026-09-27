from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.base import LogisticsBase

class HouseholdMember(LogisticsBase):
    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    pin_hash = Column(String(128), nullable=False)
    avatar_color = Column(String(16), default="#3b82f6", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
