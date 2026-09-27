from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.logistics import get_logistics_db
from app.db.finance import get_finance_db
from app.models.member import HouseholdMember
from app.schemas.timeline import TimelineDayResponse
from app.services.timeline import get_day_timeline
from app.auth.dependencies import get_current_member

router = APIRouter(prefix="/api", tags=["Timeline"])

@router.get("/timeline", response_model=TimelineDayResponse)
def get_timeline(
    target_date: Optional[str] = Query(None, alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    view: str = Query("all", pattern=r"^(all|mine)$"),
    current_member: Optional[HouseholdMember] = Depends(get_current_member),
    logistics_db: Session = Depends(get_logistics_db),
    finance_db: Session = Depends(get_finance_db)
):
    """Retrieves the unified daily timeline merging logistics and financial items for a given date."""
    if not target_date:
        target_date = date.today().isoformat()
    
    return get_day_timeline(
        target_date=target_date,
        logistics_db=logistics_db,
        finance_db=finance_db,
        current_member=current_member,
        filter_view=view
    )
