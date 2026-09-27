from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import LogisticsBase
from app.models.member import HouseholdMember

class UnprocessedInbox(LogisticsBase):
    __tablename__ = "unprocessed_inbox"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(32), default="share_target", nullable=False)  # share_target, clipboard, file_upload
    item_type = Column(String(32), default="text", nullable=False)        # link, text, image, document
    title = Column(String(255), nullable=True)
    raw_content = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_mime_type = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=True)
    suggested_action = Column(String(32), default="review", nullable=False) # task, expense, note, review
    status = Column(String(16), default="pending", nullable=False, index=True) # pending, processed, dismissed
    captured_by_id = Column(Integer, ForeignKey("household_members.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    captured_by = relationship("HouseholdMember", foreign_keys=[captured_by_id])
