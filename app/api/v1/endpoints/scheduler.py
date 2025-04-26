from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db import session
from app.schemas import scheduler as SchedulerSchema, common as CommonSchema
from app.crud.v1 import scheduler as scheduler_crud

router = APIRouter()

@router.post("/", response_model=SchedulerSchema.SchedulerRead, status_code=status.HTTP_201_CREATED)
def create_scheduler(
    scheduler_create: SchedulerSchema.SchedulerCreate,
    session: Session = Depends(session.get_session),
):
    return scheduler_crud.create_scheduler(scheduler_create, session)

@router.get("/", response_model=list[SchedulerSchema.SchedulerRead])
def list_schedulers(
    session: Session = Depends(session.get_session),
):
    return scheduler_crud.get_schedulers(session)

@router.get("/{scheduler_id}", response_model=SchedulerSchema.SchedulerRead)
def get_scheduler(
    scheduler_id: int,
    session: Session = Depends(session.get_session),
):
    scheduler = scheduler_crud.get_scheduler_by_id(scheduler_id, session)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Scheduler not found")
    return scheduler

@router.put("/{scheduler_id}", response_model=SchedulerSchema.SchedulerRead)
def update_scheduler(
    scheduler_id: int,
    scheduler_update: SchedulerSchema.SchedulerUpdate,
    session: Session = Depends(session.get_session),
):
    scheduler = scheduler_crud.update_scheduler(scheduler_id, scheduler_update, session)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Scheduler not found")
    return scheduler

@router.delete("/{scheduler_id}", response_model=CommonSchema.Message)
def delete_scheduler(
    scheduler_id: int,
    session: Session = Depends(session.get_session),
):
    ok = scheduler_crud.delete_scheduler(scheduler_id, session)
    if not ok:
        raise HTTPException(status_code=404, detail="Scheduler not found")
    return CommonSchema.Message(message="Scheduler deleted successfully")
