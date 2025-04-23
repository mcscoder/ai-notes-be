from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel
from app.schemas import label as LabelSchema, common as CommonSchema

router = APIRouter()


@router.get("/", response_model=list[LabelSchema.LabelRead])
def list_labels(
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    return v1.label.get_labels(current_user, session)


@router.post(
    "/", response_model=LabelSchema.LabelRead, status_code=status.HTTP_201_CREATED
)
def create_label(
    label_create: LabelSchema.LabelCreate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    return v1.label.create_label(label_create, current_user, session)


@router.get("/{label_id}", response_model=LabelSchema.LabelRead)
def get_label(
    label_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    label = v1.label.get_label_by_id(label_id, current_user, session)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return label


@router.put("/{label_id}", response_model=LabelSchema.LabelRead)
def update_label(
    label_id: int,
    label_update: LabelSchema.LabelUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    label = v1.label.update_label(label_id, label_update, current_user, session)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return label


@router.delete("/{label_id}", response_model=CommonSchema.Message)
def delete_label(
    label_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    db: Session = Depends(session.get_session),
):
    ok = v1.label.delete_label(label_id, current_user, db)
    if not ok:
        raise HTTPException(status_code=404, detail="Label not found")
    return CommonSchema.Message(message="Label deleted successfully")
