from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timezone

from app.db.init_db import init_db
from app.db.session import get_session
from app.models.scheduler import Scheduler
from app.models.note import Note
from app.models.user import User
from sqlmodel import Session, select
from app.api.v1.api import api_router

async def scheduler_worker():
    while True:
        async with asyncio.Lock():
            with next(get_session()) as session:
                now = datetime.now(timezone.utc)
                statement = select(Scheduler).where(
                    Scheduler.is_sent == False,
                    Scheduler.scheduled_time <= now,
                )
                schedulers = session.exec(statement).all()
                for sched in schedulers:
                    # Fetch the note and user
                    note = session.get(Note, sched.note_id)
                    user = session.get(User, note.user_id) if note else None
                    # Example: print user info
                    print(
                        f"Scheduler triggered for note_id={sched.note_id} at {sched.scheduled_time} "
                        f"by user_id={user.id if user else 'unknown'} email={user.email if user else 'unknown'}"
                    )
                    sched.is_sent = True
                    session.add(sched)
                session.commit()
        await asyncio.sleep(30)  # Check every 30 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 App is starting up...")
    init_db()
    # Start background scheduler worker
    loop = asyncio.get_event_loop()
    task = loop.create_task(scheduler_worker())
    yield
    task.cancel()
    print("💥 App is shutting down...")

app = FastAPI(lifespan=lifespan, title="AI Note-Taking App API")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "AINotes API base is running!"}
