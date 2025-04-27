from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel, note as NoteModel
from app.schemas import note as NoteSchema
from app.services import ai_service

router = APIRouter()


async def _apply_ai_and_update(
    ai_function,
    note: NoteModel.Note,
    current_user: UserModel.User,
    session: Session,
):
    modified_content = await ai_function(note.content)
    note_update_data = NoteSchema.NoteUpdate(content=modified_content)
    note_updated = v1.note.update_note(note.id, note_update_data, current_user, session)
    return note_updated


@router.post("/{note_id}/format", response_model=NoteSchema.NoteRead)
async def format_note(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.format_content, note, current_user, session
    )


@router.post("/{note_id}/cleanup", response_model=NoteSchema.NoteRead)
async def cleanup_content(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.cleanup_content, note, current_user, session
    )


@router.post("/{note_id}/refine", response_model=NoteSchema.NoteRead)
async def refine_content(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.refine_content, note, current_user, session
    )


@router.post("/{note_id}/continue", response_model=NoteSchema.NoteRead)
async def continue_writing(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.continue_writing, note, current_user, session
    )


@router.post("/{note_id}/polish", response_model=NoteSchema.NoteRead)
async def polish_content(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.polish_content, note, current_user, session
    )


@router.post("/{note_id}/summarize", response_model=NoteSchema.NoteRead)
async def summarize_content(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return await _apply_ai_and_update(
        ai_service.summarize_content, note, current_user, session
    )
