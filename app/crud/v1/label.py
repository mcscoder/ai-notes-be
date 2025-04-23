from sqlmodel import Session, select
from app.models import label as LabelModel
from app.schemas import label as LabelSchema

def get_label_by_id(label_id: int, session: Session):
    statement = select(LabelModel.Label).where(LabelModel.Label.id == label_id)
    return session.exec(statement).first()

def get_labels(session: Session):
    statement = select(LabelModel.Label)
    return session.exec(statement).all()
