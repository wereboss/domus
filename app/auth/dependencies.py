from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.logistics import get_logistics_db
from app.models.member import HouseholdMember
from app.auth.pin import decode_access_token

security = HTTPBearer(auto_error=False)

def get_current_member(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_logistics_db)
) -> Optional[HouseholdMember]:
    """Retrieves current authenticated HouseholdMember from Bearer token.
    If no token provided, returns None (allowing public/shared endpoints)."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    member_id = payload.get("sub")
    if not member_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing member identifier"
        )
    member = db.query(HouseholdMember).filter(HouseholdMember.id == int(member_id)).first()
    if not member or not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Member profile inactive or not found"
        )
    return member

def require_current_member(
    member: Optional[HouseholdMember] = Depends(get_current_member)
) -> HouseholdMember:
    """Enforces authentication; raises 401 if not logged in."""
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication PIN required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return member
