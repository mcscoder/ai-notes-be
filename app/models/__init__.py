from sqlalchemy import event
from app.models.base import BaseModel, utc_now
from sqlmodel import SQLModel, Field


class NoteLabelLink(SQLModel, table=True):
    note_id: int = Field(foreign_key="note.id", primary_key=True)
    label_id: int = Field(foreign_key="label.id", primary_key=True)


@event.listens_for(BaseModel, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    target.updated_at = utc_now()
