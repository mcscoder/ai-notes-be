from sqlmodel import Session, select

from app.models import label as LabelModel, user as UserModel
from app.schemas import label as LabelSchema

def create_label(label_create: LabelSchema.LabelCreate, user: UserModel.User, session: Session):
    new_label = LabelModel.Label(
        **label_create.model_dump(),
        user_id=user.id
    )
    session.add(new_label)
    session.commit()
    session.refresh(new_label)
    return new_label

def get_label_by_id(label_id: int, user: UserModel.User, session: Session):
    statement = select(LabelModel.Label).where(
        LabelModel.Label.id == label_id,
        LabelModel.Label.user_id == user.id
    )
    return session.exec(statement).first()

def get_labels(user: UserModel.User, session: Session):
    statement = select(LabelModel.Label).where(LabelModel.Label.user_id == user.id)
    return session.exec(statement).all()

def update_label(label_id: int, label_update: LabelSchema.LabelUpdate, user: UserModel.User, session: Session):
    label = get_label_by_id(label_id, user, session)
    if not label:
        return None
    update_data = label_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(label, key, value)
    session.add(label)
    session.commit()
    session.refresh(label)
    return label

def delete_label(label_id: int, user: UserModel.User, session: Session):
    label = get_label_by_id(label_id, user, session)
    if not label:
        return False
    session.delete(label)
    session.commit()
    return True
