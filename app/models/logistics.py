from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import LogisticsBase
from app.models.member import HouseholdMember

class Task(LogisticsBase):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("household_members.id"), nullable=True, index=True)
    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    due_time = Column(String(5), nullable=True)               # HH:MM (24h)
    priority = Column(String(16), default="normal", nullable=False)  # low, normal, urgent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assigned_to = relationship("HouseholdMember", foreign_keys=[assigned_to_id])

class Chore(LogisticsBase):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    recurrence = Column(String(32), default="daily", nullable=False)  # daily, weekly, biweekly, monthly
    assigned_to_id = Column(Integer, ForeignKey("household_members.id"), nullable=True, index=True)
    last_completed_at = Column(DateTime, nullable=True)
    next_due_date = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assigned_to = relationship("HouseholdMember", foreign_keys=[assigned_to_id])

class Note(LogisticsBase):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("household_members.id"), nullable=True, index=True)
    category = Column(String(64), default="General", nullable=False)
    attachment_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    author = relationship("HouseholdMember", foreign_keys=[author_id])
