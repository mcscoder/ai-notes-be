from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional
from sqlalchemy import desc, asc, or_

from app.models import (
    note as NoteModel,
    user as UserModel,
    task as TaskModel,
)
from app.schemas import note as NoteSchema, task as TaskSchema


def create_note(
    note_create: NoteSchema.NoteCreate, user: UserModel.User, session: Session
):
    data = note_create.model_dump()
    new_note = NoteModel.Note(**data, user_id=user.id)
    session.add(new_note)
    session.commit()
    session.refresh(new_note)
    return new_note


def get_note_by_id(note_id: int, user: UserModel.User, session: Session):
    statement = select(NoteModel.Note).where(
        NoteModel.Note.id == note_id,
        NoteModel.Note.user_id == user.id,
    )
    return session.exec(statement).first()


def get_notes(
    user: UserModel.User,
    session: Session,
    type: Optional[int] = None,
    is_pinned: Optional[bool] = None,
    is_finished: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    sort_order: str = "desc",
    search: Optional[str] = None,
):
    filters = [NoteModel.Note.user_id == user.id]
    if type is not None:
        filters.append(NoteModel.Note.type == type)
    if is_pinned is not None:
        filters.append(NoteModel.Note.is_pinned == is_pinned)
    if is_finished is not None:
        filters.append(NoteModel.Note.is_finished == is_finished)
    if is_archived is not None:
        filters.append(NoteModel.Note.is_archived == is_archived)
    if search:
        filters.append(
            or_(
                NoteModel.Note.title.ilike(f"%{search}%"),
                NoteModel.Note.content.ilike(f"%{search}%"),
            )
        )
    statement = select(NoteModel.Note).where(*filters)
    if sort_order == "asc":
        statement = statement.order_by(asc(NoteModel.Note.updated_at))
    else:
        statement = statement.order_by(desc(NoteModel.Note.updated_at))
    return session.exec(statement).all()


def update_note(
    note_id: int,
    note_update: NoteSchema.NoteUpdate,
    user: UserModel.User,
    session: Session,
):
    note = get_note_by_id(note_id, user, session)
    if not note:
        return None
    data = note_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(note, key, value)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(note_id: int, user: UserModel.User, session: Session):
    note = get_note_by_id(note_id, user, session)
    if not note:
        return False
    session.delete(note)
    session.commit()
    return True


def create_task(
    note_id: int,
    task_create: TaskSchema.TaskCreate,
    user: UserModel.User,
    session: Session,
):
    note = get_note_by_id(note_id, user, session)
    if not note:
        return None
    data = task_create.model_dump()
    if task_create.parent_id is None:
        data["note_id"] = note.id
    task = TaskModel.Task(**data)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task_by_id(note_id: int, task_id: int, user: UserModel.User, session: Session):
    note = get_note_by_id(note_id, user, session)
    if not note:
        return None
    statement = (
        select(TaskModel.Task)
        .where(TaskModel.Task.id == task_id, TaskModel.Task.note_id == note_id)
        .options(selectinload(TaskModel.Task.tasks))
    )
    return session.exec(statement).first()


def update_task(
    note_id: int,
    task_id: int,
    task_update: TaskSchema.TaskUpdate,
    user: UserModel.User,
    session: Session,
):
    task = get_task_by_id(note_id, task_id, user, session)
    if not task:
        return None

    data = task_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(note_id: int, task_id: int, user: UserModel.User, session: Session):
    task = get_task_by_id(note_id, task_id, user, session)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True
