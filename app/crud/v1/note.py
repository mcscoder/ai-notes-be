from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import (
    note as NoteModel,
    user as UserModel,
    label as LabelModel,
    task as TaskModel,
)
from app.schemas import note as NoteSchema, task as TaskSchema


def create_note(
    note_create: NoteSchema.NoteCreate, user: UserModel.User, session: Session
):
    label_ids = note_create.label_ids or []
    data = note_create.model_dump(exclude={"label_ids"})
    new_note = NoteModel.Note(**data, user_id=user.id)
    session.add(new_note)
    session.flush()
    if label_ids:
        labels = session.exec(
            select(LabelModel.Label).where(LabelModel.Label.id.in_(label_ids))
        ).all()
        new_note.labels = labels
    session.commit()
    session.refresh(new_note)
    return new_note


def get_note_by_id(note_id: int, user: UserModel.User, session: Session):
    statement = (
        select(NoteModel.Note)
        .where(
            NoteModel.Note.id == note_id,
            NoteModel.Note.user_id == user.id,
        )
        .options(selectinload(NoteModel.Note.labels))
    )
    return session.exec(statement).first()


def get_notes(user: UserModel.User, session: Session):
    statement = (
        select(NoteModel.Note)
        .where(NoteModel.Note.user_id == user.id)
        .options(selectinload(NoteModel.Note.labels))
    )
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
    label_ids = data.pop("label_ids", None)
    for key, value in data.items():
        setattr(note, key, value)
    if label_ids is not None:
        labels = session.exec(
            select(LabelModel.Label).where(LabelModel.Label.id.in_(label_ids))
        ).all()
        note.labels = labels
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
