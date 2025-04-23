from sqlmodel import Session, select

from app.models import note as NoteModel, user as UserModel
from app.schemas import note as NoteSchema


def create_note(
    note_create: NoteSchema.NoteCreate, user: UserModel.User, session: Session
):
    new_note = NoteModel.Note(**note_create.model_dump(), user_id=user.id)
    session.add(new_note)
    session.commit()
    session.refresh(new_note)
    return new_note


def get_note_by_id(note_id: int, user: UserModel.User, session: Session):
    statement = select(NoteModel.Note).where(
        NoteModel.Note.id == note_id, NoteModel.Note.user_id == user.id
    )
    return session.exec(statement).first()


def get_notes(user: UserModel.User, session: Session):
    statement = select(NoteModel.Note).where(NoteModel.Note.user_id == user.id)
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
    for key, value in update_data.items():
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
