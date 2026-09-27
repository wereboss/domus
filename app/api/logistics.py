from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.logistics import get_logistics_db
from app.models.logistics import Task, Chore, Note
from app.models.member import HouseholdMember
from app.schemas.logistics import (
    TaskCreate, TaskUpdate, TaskResponse,
    ChoreCreate, ChoreResponse,
    NoteCreate, NoteResponse
)
from app.auth.dependencies import get_current_member

router = APIRouter(prefix="/api", tags=["Logistics"])

# ================= Tasks =================
@router.get("/tasks", response_model=List[TaskResponse])
def list_tasks(
    assigned_to_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    due_date: Optional[str] = None,
    db: Session = Depends(get_logistics_db)
):
    """Lists tasks with optional filtering."""
    query = db.query(Task)
    if assigned_to_id is not None:
        query = query.filter(Task.assigned_to_id == assigned_to_id)
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    if due_date is not None:
        query = query.filter(Task.due_date == due_date)
    return query.order_by(Task.due_date.asc(), Task.due_time.asc().nulls_last()).all()

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_logistics_db)):
    """Creates a new task in logistics.db."""
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_logistics_db)):
    """Updates a task or toggles its completed state."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    if "is_completed" in update_data:
        if update_data["is_completed"] and not task.is_completed:
            task.completed_at = datetime.utcnow()
        elif not update_data["is_completed"]:
            task.completed_at = None

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_logistics_db)):
    """Deletes a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None

# ================= Chores =================
@router.get("/chores", response_model=List[ChoreResponse])
def list_chores(db: Session = Depends(get_logistics_db)):
    """Lists all active household chores."""
    return db.query(Chore).filter(Chore.is_active == True).order_by(Chore.next_due_date.asc()).all()

@router.post("/chores", response_model=ChoreResponse, status_code=status.HTTP_201_CREATED)
def create_chore(payload: ChoreCreate, db: Session = Depends(get_logistics_db)):
    """Creates a new recurring chore in logistics.db."""
    chore = Chore(**payload.model_dump())
    db.add(chore)
    db.commit()
    db.refresh(chore)
    return chore

@router.post("/chores/{chore_id}/complete", response_model=ChoreResponse)
def complete_chore(chore_id: int, db: Session = Depends(get_logistics_db)):
    """Marks a chore complete and computes its next recurrence date."""
    chore = db.query(Chore).filter(Chore.id == chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    today = date.today()
    chore.last_completed_at = datetime.utcnow()

    # Compute next due date based on recurrence
    if chore.recurrence == "daily":
        next_date = today + timedelta(days=1)
    elif chore.recurrence == "weekly":
        next_date = today + timedelta(days=7)
    elif chore.recurrence == "biweekly":
        next_date = today + timedelta(days=14)
    elif chore.recurrence == "monthly":
        next_date = today + timedelta(days=30)
    else:
        next_date = today + timedelta(days=1)

    chore.next_due_date = next_date.isoformat()
    db.commit()
    db.refresh(chore)
    return chore

# ================= Notes =================
@router.get("/notes", response_model=List[NoteResponse])
def list_notes(category: Optional[str] = None, db: Session = Depends(get_logistics_db)):
    """Lists household notes."""
    query = db.query(Note)
    if category:
        query = query.filter(Note.category == category)
    return query.order_by(Note.created_at.desc()).all()

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    current_member: Optional[HouseholdMember] = Depends(get_current_member),
    db: Session = Depends(get_logistics_db)
):
    """Creates a new household note."""
    note = Note(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        author_id=current_member.id if current_member else None
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_logistics_db)):
    """Deletes a note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None
