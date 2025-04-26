from sqlmodel import Session, select
from app.models import scheduler as SchedulerModel
from app.schemas import scheduler as SchedulerSchema

def create_scheduler(scheduler_create: SchedulerSchema.SchedulerCreate, session: Session):
    scheduler = SchedulerModel.Scheduler(**scheduler_create.model_dump())
    session.add(scheduler)
    session.commit()
    session.refresh(scheduler)
    return scheduler

def get_schedulers(session: Session):
    statement = select(SchedulerModel.Scheduler)
    return session.exec(statement).all()

def get_scheduler_by_id(scheduler_id: int, session: Session):
    statement = select(SchedulerModel.Scheduler).where(SchedulerModel.Scheduler.id == scheduler_id)
    return session.exec(statement).first()

def update_scheduler(scheduler_id: int, scheduler_update: SchedulerSchema.SchedulerUpdate, session: Session):
    scheduler = get_scheduler_by_id(scheduler_id, session)
    if not scheduler:
        return None
    data = scheduler_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(scheduler, key, value)
    session.add(scheduler)
    session.commit()
    session.refresh(scheduler)
    return scheduler

def delete_scheduler(scheduler_id: int, session: Session):
    scheduler = get_scheduler_by_id(scheduler_id, session)
    if not scheduler:
        return False
    session.delete(scheduler)
    session.commit()
    return True
