from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional
from sqlalchemy import desc, asc, or_, and_

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
        # Split the search phrase into individual words
        search_words = search.split()
        if search_words:  # Only add filter if there are any words
            # Create a list of conditions, one for each word
            word_filters = []
            for word in search_words:
                word_pattern = f"%{word}%"
                # Condition: This word must appear in the title OR content
                word_condition = or_(
                    NoteModel.Note.title.ilike(word_pattern),
                    NoteModel.Note.content.ilike(word_pattern),
                )
                word_filters.append(word_condition)

            # Combine all word conditions with AND
            # Meaning ALL words must appear (in title or content)
            filters.append(and_(*word_filters))
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


def get_task_by_id(task_id: int, session: Session):
    statement = (
        select(TaskModel.Task)
        .where(TaskModel.Task.id == task_id)
        .options(selectinload(TaskModel.Task.tasks))
    )
    return session.exec(statement).first()


def update_task(
    task_id: int,
    task_update: TaskSchema.TaskUpdate,
    session: Session,
):
    task = get_task_by_id(task_id, session)
    if not task:
        return None

    data = task_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(task_id: int, session: Session):
    task = get_task_by_id(task_id, session)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True
