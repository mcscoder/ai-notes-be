from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlmodel import Session
from typing import Optional, Literal

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel
from app.schemas import (
    note as NoteSchema,
    common as CommonSchema,
    task as TaskSchema,
)

router = APIRouter()


@router.get("/", response_model=list[NoteSchema.NoteRead])
def list_notes(
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
    type: Optional[int] = Query(None, description="Filter by note type"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    is_finished: Optional[bool] = Query(None, description="Filter by finished status"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    sort_order: Literal["asc", "desc"] = Query("desc", pattern="^(asc|desc)$", description="Sort order by updated_at: 'asc' or 'desc'"),
    search: Optional[str] = Query(None, description="Search in note title or content"),
):
    return v1.note.get_notes(
        current_user,
        session,
        type=type,
        is_pinned=is_pinned,
        is_finished=is_finished,
        is_archived=is_archived,
        sort_order=sort_order,
        search=search,
    )


@router.post(
    "/", response_model=NoteSchema.NoteRead, status_code=status.HTTP_201_CREATED
)
def create_note(
    note_create: NoteSchema.NoteCreate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    return v1.note.create_note(note_create, current_user, session)


@router.get("/{note_id}", response_model=NoteSchema.NoteRead)
def get_note(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteSchema.NoteRead)
def update_note(
    note_id: int,
    note_update: NoteSchema.NoteUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.update_note(note_id, note_update, current_user, session)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", response_model=CommonSchema.Message)
def delete_note(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    ok = v1.note.delete_note(note_id, current_user, session)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return CommonSchema.Message(message="Note deleted successfully")


@router.post(
    "/{note_id}/tasks",
    response_model=TaskSchema.TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    note_id: int,
    task_create: TaskSchema.TaskCreate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    task = v1.note.create_task(note_id, task_create, current_user, session)
    if not task:
        raise HTTPException(status_code=404, detail="Note not found")
    return task


@router.get("/{note_id}/tasks/{task_id}", response_model=TaskSchema.TaskRead)
def get_task(
    note_id: int,
    task_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    task = v1.note.get_task_by_id(note_id, task_id, current_user, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{note_id}/tasks/{task_id}", response_model=TaskSchema.TaskRead)
def update_task(
    note_id: int,
    task_id: int,
    task_update: TaskSchema.TaskUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    task = v1.note.update_task(note_id, task_id, task_update, current_user, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{note_id}/tasks/{task_id}", response_model=CommonSchema.Message)
def delete_task(
    note_id: int,
    task_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    ok = v1.note.delete_task(note_id, task_id, current_user, session)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return CommonSchema.Message(message="Task deleted successfully")
