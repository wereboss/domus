from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.config import DATA_DIR
from app.db.logistics import get_logistics_db
from app.db.finance import get_finance_db
from app.models.inbox import UnprocessedInbox
from app.models.logistics import Task, Note
from app.models.finance import LedgerExpense
from app.models.member import HouseholdMember
from app.schemas.inbox import InboxItemCreate, InboxItemResponse, InboxCountResponse, InboxTriageRequest
from app.services.storage import save_uploaded_file, INBOX_UPLOAD_DIR
from app.auth.dependencies import get_current_member

router = APIRouter(tags=["Family Inbox & Capture"])
CONFIRMATION_HTML = Path(__file__).resolve().parent.parent / "static" / "share-confirmation.html"

# ==============================================================
# OS WEB SHARE TARGET RECEIVERS
# ==============================================================

@router.post("/share-target", response_class=FileResponse)
async def receive_share_target_post(
    title: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_logistics_db)
):
    """Intercepts incoming POST data from OS native Share sheet."""
    # Determine primary content and item type
    shared_text = text or ""
    shared_url = url or ""
    shared_title = title or ""

    # Check if a URL was passed inside text
    if not shared_url and ("http://" in shared_text or "https://" in shared_text):
        for word in shared_text.split():
            if word.startswith("http://") or word.startswith("https://"):
                shared_url = word
                break

    raw_content = shared_url if shared_url else shared_text
    item_type = "link" if shared_url else "text"
    item_title = shared_title or (shared_url if shared_url else (shared_text[:40] + "..." if len(shared_text) > 40 else shared_text))

    file_rel_path = None
    file_orig_name = None
    file_mime = None
    file_sz = None

    # Handle file if attached
    if files and len(files) > 0 and files[0].filename:
        upload = files[0]
        file_rel_path, file_orig_name, file_mime, file_sz, detected_type = await save_uploaded_file(upload)
        item_type = detected_type
        if not item_title or item_title == "":
            item_title = file_orig_name

    inbox_item = UnprocessedInbox(
        source="share_target",
        item_type=item_type,
        title=item_title or "Shared Item",
        raw_content=raw_content,
        file_path=file_rel_path,
        file_name=file_orig_name,
        file_mime_type=file_mime,
        file_size=file_sz,
        status="pending"
    )
    db.add(inbox_item)
    db.commit()

    return FileResponse(CONFIRMATION_HTML, media_type="text/html")

@router.get("/share-target", response_class=FileResponse)
def receive_share_target_get(
    title: Optional[str] = Query(None),
    text: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    db: Session = Depends(get_logistics_db)
):
    """Fallback handler for OS Share sheets using GET query params."""
    shared_url = url or ""
    shared_text = text or ""
    shared_title = title or ""

    if not shared_url and ("http://" in shared_text or "https://" in shared_text):
        for word in shared_text.split():
            if word.startswith("http://") or word.startswith("https://"):
                shared_url = word
                break

    raw_content = shared_url if shared_url else shared_text
    item_type = "link" if shared_url else "text"
    item_title = shared_title or (shared_url if shared_url else (shared_text[:40] + "..." if len(shared_text) > 40 else shared_text))

    inbox_item = UnprocessedInbox(
        source="share_target",
        item_type=item_type,
        title=item_title or "Shared Link",
        raw_content=raw_content,
        status="pending"
    )
    db.add(inbox_item)
    db.commit()

    return FileResponse(CONFIRMATION_HTML, media_type="text/html")


# ==============================================================
# INBOX APIS
# ==============================================================

@router.get("/api/inbox", response_model=List[InboxItemResponse])
def list_pending_inbox_items(db: Session = Depends(get_logistics_db)):
    """Returns all pending items in the Family Inbox."""
    return db.query(UnprocessedInbox).filter(
        UnprocessedInbox.status == "pending"
    ).order_by(UnprocessedInbox.created_at.desc()).all()

@router.get("/api/inbox/count", response_model=InboxCountResponse)
def get_inbox_count(db: Session = Depends(get_logistics_db)):
    """Returns the count of pending items for the bottom navigation badge."""
    count = db.query(UnprocessedInbox).filter(UnprocessedInbox.status == "pending").count()
    return InboxCountResponse(pending_count=count)

@router.post("/api/inbox", response_model=InboxItemResponse, status_code=status.HTTP_201_CREATED)
def create_inbox_item(
    payload: InboxItemCreate,
    current_member: Optional[HouseholdMember] = Depends(get_current_member),
    db: Session = Depends(get_logistics_db)
):
    """In-app quick capture endpoint (e.g. from 1-tap clipboard paste)."""
    raw_content = payload.raw_content or ""
    item_type = payload.item_type

    if not item_type or item_type == "text":
        if raw_content.startswith("http://") or raw_content.startswith("https://"):
            item_type = "link"

    item = UnprocessedInbox(
        source=payload.source or "in_app_paste",
        item_type=item_type,
        title=payload.title or (raw_content[:50] + "..." if len(raw_content) > 50 else raw_content),
        raw_content=raw_content,
        captured_by_id=current_member.id if current_member else None,
        status="pending"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/api/inbox/upload", response_model=InboxItemResponse, status_code=status.HTTP_201_CREATED)
async def upload_inbox_file(
    file: UploadFile = File(...),
    current_member: Optional[HouseholdMember] = Depends(get_current_member),
    db: Session = Depends(get_logistics_db)
):
    """In-app file/photo upload endpoint."""
    file_rel_path, file_orig_name, file_mime, file_sz, item_type = await save_uploaded_file(file)

    item = UnprocessedInbox(
        source="file_upload",
        item_type=item_type,
        title=file_orig_name,
        raw_content=None,
        file_path=file_rel_path,
        file_name=file_orig_name,
        file_mime_type=file_mime,
        file_size=file_sz,
        captured_by_id=current_member.id if current_member else None,
        status="pending"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/api/inbox/{item_id}/triage")
def triage_inbox_item(
    item_id: int,
    payload: InboxTriageRequest,
    current_member: Optional[HouseholdMember] = Depends(get_current_member),
    log_db: Session = Depends(get_logistics_db),
    fin_db: Session = Depends(get_finance_db)
):
    """Converts an inbox item into a Task, Expense, or Note, marking it processed."""
    item = log_db.query(UnprocessedInbox).filter(UnprocessedInbox.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    today_str = date.today().isoformat()

    if payload.target_type == "task":
        new_task = Task(
            title=payload.title,
            description=item.raw_content or item.file_name,
            due_date=payload.due_date or today_str,
            due_time=payload.due_time,
            priority=payload.priority or "normal",
            assigned_to_id=payload.assigned_to_id
        )
        log_db.add(new_task)

    elif payload.target_type == "expense":
        new_expense = LedgerExpense(
            title=payload.title,
            amount=payload.amount if payload.amount is not None else 0.0,
            category=payload.category or "General",
            date=today_str,
            payment_method=payload.payment_method or "Card",
            payer_member_id=current_member.id if current_member else None,
            notes=item.raw_content or item.file_name
        )
        fin_db.add(new_expense)
        fin_db.commit()

    elif payload.target_type == "note":
        new_note = Note(
            title=payload.title,
            content=payload.content or item.raw_content or (f"Attached file: {item.file_name}" if item.file_name else "Quick capture note"),
            category="Inbox",
            author_id=current_member.id if current_member else None
        )
        log_db.add(new_note)

    item.status = "processed"
    log_db.commit()
    return {"message": f"Successfully converted item to {payload.target_type}", "item_id": item_id}

@router.delete("/api/inbox/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_inbox_item(item_id: int, db: Session = Depends(get_logistics_db)):
    """Dismisses an item from the inbox."""
    item = db.query(UnprocessedInbox).filter(UnprocessedInbox.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    item.status = "dismissed"
    db.commit()
    return None

@router.get("/api/inbox/files/{filename}")
def serve_inbox_file(filename: str):
    """Serves uploaded images and documents."""
    safe_filename = Path(filename).name
    file_path = INBOX_UPLOAD_DIR / safe_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
