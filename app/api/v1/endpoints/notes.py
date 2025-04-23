from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel
from app.schemas import note as NoteSchema, common as CommonSchema

router = APIRouter()


@router.get("/", response_model=list[NoteSchema.NoteRead])
def list_notes(
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    return v1.note.get_notes(current_user, session)


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
