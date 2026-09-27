from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
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
    request: Request,
    db: Session = Depends(get_logistics_db)
):
    """Intercepts incoming POST data from OS native Share sheet."""
    try:
        form = await request.form()
    except Exception:
        form = {}

    shared_title = str(form.get("title") or "").strip()
    shared_text = str(form.get("text") or "").strip()
    shared_url = str(form.get("url") or "").strip()

    # Discover ANY uploaded file across any form field key (e.g. 'files', 'file', 'image')
    uploaded_files: List[UploadFile] = []
    for key in form.keys():
        for val in form.getlist(key):
            if hasattr(val, "filename") and val.filename:
                uploaded_files.append(val)

    # Check if a URL was passed inside text
    if not shared_url and ("http://" in shared_text or "https://" in shared_text):
        for word in shared_text.split():
            if word.startswith("http://") or word.startswith("https://"):
                shared_url = word
                break

    file_rel_path = None
    file_orig_name = None
    file_mime = None
    file_sz = None
    item_type = "link" if shared_url else "text"

    # Handle file if attached
    if uploaded_files:
        upload = uploaded_files[0]
        file_rel_path, file_orig_name, file_mime, file_sz, detected_type = await save_uploaded_file(upload)
        item_type = detected_type
        item_title = shared_title or file_orig_name
    else:
        # Check if the shared URL or text points directly to an image
        url_check = (shared_url or shared_text).lower().split("?")[0]
        if any(url_check.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"]):
            item_type = "image"
        item_title = shared_title or (shared_url if shared_url else (shared_text[:40] + "..." if len(shared_text) > 40 else shared_text))

    raw_content = shared_url if shared_url else shared_text

    # Guard against empty share intents (e.g. Android WebAPK permission bug where file is stripped)
    if not file_rel_path and not raw_content and not shared_title:
        return RedirectResponse("/static/share-confirmation.html?status=empty", status_code=303)

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
    items = db.query(UnprocessedInbox).filter(
        UnprocessedInbox.status == "pending"
    ).order_by(UnprocessedInbox.created_at.desc()).all()
    results = []
    for it in items:
        resp = InboxItemResponse.model_validate(it)
        if it.file_path:
            resp.file_url = f"/api/inbox/files/{Path(it.file_path).name}"
        elif it.file_name:
            resp.file_url = f"/api/inbox/files/{it.file_name}"
        elif it.raw_content and any(it.raw_content.lower().split("?")[0].endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
            resp.file_url = it.raw_content
        results.append(resp)
    return results

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
            url_clean = raw_content.lower().split("?")[0]
            if any(url_clean.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                item_type = "image"

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
    resp = InboxItemResponse.model_validate(item)
    if item_type == "image" and raw_content.startswith("http"):
        resp.file_url = raw_content
    return resp

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
    resp = InboxItemResponse.model_validate(item)
    resp.file_url = f"/api/inbox/files/{Path(file_rel_path).name}"
    return resp

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
            content=payload.content or item.raw_content or "",
            category="Inbox",
            attachment_path=item.file_path,
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
    """Serves uploaded images and documents with fallback matching."""
    safe_filename = Path(filename).name
    file_path = INBOX_UPLOAD_DIR / safe_filename
    if not file_path.exists():
        # Fallback: search for file ending with _{safe_filename}
        matches = list(INBOX_UPLOAD_DIR.glob(f"*_{safe_filename}"))
        if matches:
            file_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
