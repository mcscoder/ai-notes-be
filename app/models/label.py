from app.models.base import BaseModel
from sqlmodel import Relationship
from typing import TYPE_CHECKING, List
from . import NoteLabelLink

if TYPE_CHECKING:
    from app.models.note import Note


class LabelBase(BaseModel):
    name: str


class Label(LabelBase, table=True):
    # One label can have many notes
    notes: List["Note"] = Relationship(
        back_populates="labels", link_model=NoteLabelLink
    )
