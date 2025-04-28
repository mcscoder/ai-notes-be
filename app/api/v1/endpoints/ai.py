from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel, note as NoteModel, task as TaskModel
from app.schemas import note as NoteSchema, task as TaskSchema
from app.services import ai_service

router = APIRouter()


async def _apply_ai_and_update_note(
    ai_function,
    note: NoteModel.Note,
    current_user: UserModel.User,
    session: Session,
):
    if note.type in [1, 4]:  # Apply AI functions for content
        modified_content = await ai_function(note.content, note.title)
        note_update_data = NoteSchema.NoteUpdate(content=modified_content)
        note_updated = v1.note.update_note(
            note.id, note_update_data, current_user, session
        )
        return note_updated
    else:
        is_sub_task = note.type == 3
        return await _apply_ai_and_update_tasks(ai_function, note, session, is_sub_task)


async def _update_tasks(
    ai_function,
    title: str,
    tasks: List[TaskModel.Task],
    session: Session,
):
    for task in tasks:
        modified_title = await ai_function(task.title, title)
        task_update_data = TaskSchema.TaskUpdate(title=modified_title)
        v1.note.update_task(task.id, task_update_data, session)


async def _apply_ai_and_update_tasks(
    ai_function,
    note: NoteModel.Note,
    session: Session,
    is_sub_task: bool = False,
):
    if is_sub_task:
        print("sub_task")
        for task in note.tasks:
            title = task.title
            sub_tasks = task.tasks
            await _update_tasks(ai_function, title, sub_tasks, session)
    else:
        print("task")
        title = note.title
        tasks = note.tasks
        await _update_tasks(ai_function, title, tasks, session)

    session.refresh(note)
    return note


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

    return await _apply_ai_and_update_note(
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

    return await _apply_ai_and_update_note(
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

    return await _apply_ai_and_update_note(
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

    return await _apply_ai_and_update_note(
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

    return await _apply_ai_and_update_note(
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

    return await _apply_ai_and_update_note(
        ai_service.summarize_content, note, current_user, session
    )
