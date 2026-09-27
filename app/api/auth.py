from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.logistics import get_logistics_db
from app.models.member import HouseholdMember
from app.schemas.member import HouseholdMemberCreate, HouseholdMemberResponse
from app.schemas.auth import PinLoginRequest, TokenResponse
from app.auth.pin import verify_pin, hash_pin, create_access_token
from app.auth.dependencies import get_current_member, require_current_member

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/profiles", response_model=List[HouseholdMemberResponse])
def list_profiles(db: Session = Depends(get_logistics_db)):
    """Lists available household profiles for the profile switcher."""
    return db.query(HouseholdMember).filter(HouseholdMember.is_active == True).all()

@router.post("/login", response_model=TokenResponse)
def login_with_pin(payload: PinLoginRequest, db: Session = Depends(get_logistics_db)):
    """Verifies 4-digit PIN for a selected household member and issues a persistent token."""
    member = db.query(HouseholdMember).filter(
        HouseholdMember.id == payload.member_id,
        HouseholdMember.is_active == True
    ).first()
    
    if not member or not verify_pin(payload.pin, member.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect PIN or member not found"
        )
    
    token = create_access_token(data={"sub": str(member.id), "name": member.name})
    return TokenResponse(
        access_token=token,
        member=HouseholdMemberResponse.model_validate(member)
    )

@router.get("/me", response_model=HouseholdMemberResponse)
def get_current_user_profile(current_member: HouseholdMember = Depends(require_current_member)):
    """Returns the currently authenticated member profile."""
    return current_member

@router.post("/profiles", response_model=HouseholdMemberResponse)
def create_profile(payload: HouseholdMemberCreate, db: Session = Depends(get_logistics_db)):
    """Creates a new household member profile with a PIN."""
    existing = db.query(HouseholdMember).filter(HouseholdMember.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Member '{payload.name}' already exists"
        )
    
    new_member = HouseholdMember(
        name=payload.name,
        pin_hash=hash_pin(payload.pin),
        avatar_color=payload.avatar_color
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member
