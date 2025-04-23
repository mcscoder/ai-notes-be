from sqlmodel import Session
from app.db.init_db import engine


def get_session():
    with Session(engine) as session:
        yield session
