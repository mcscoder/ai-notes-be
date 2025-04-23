from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import session
from app.crud import v1
from app.schemas import label as LabelSchema

router = APIRouter()

@router.get("/", response_model=list[LabelSchema.LabelRead])
def list_labels(
    db: Session = Depends(session.get_session),
):
    return v1.label.get_labels(db)

@router.get("/{label_id}", response_model=LabelSchema.LabelRead)
def get_label(
    label_id: int,
    db: Session = Depends(session.get_session),
):
    label = v1.label.get_label_by_id(label_id, db)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return label
