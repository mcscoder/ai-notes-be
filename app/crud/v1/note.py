from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import note as NoteModel, user as UserModel, label as LabelModel
from app.schemas import note as NoteSchema


def create_note(
    note_create: NoteSchema.NoteCreate, user: UserModel.User, session: Session
):
    label_ids = note_create.label_ids or []
    new_note = NoteModel.Note(
        title=note_create.title,
        content=note_create.content,
        is_pinned=note_create.is_pinned,
        is_finished=note_create.is_finished,
        is_archived=note_create.is_archived,
        user_id=user.id,
    )
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
    update_data = note_update.model_dump(exclude_unset=True)
    label_ids = update_data.pop("label_ids", None)
    for key, value in update_data.items():
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
