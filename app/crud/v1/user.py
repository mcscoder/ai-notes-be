from sqlmodel import Session, select

from app.models import User
from app.schemas import user
from app.core import security


def get_user_by_id(user_id: int, session: Session):
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    if not user:
        return None
    return user


def get_user_by_email(email: str, session: Session):
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        return None
    return user


def create(user_create: user.UserCreate, session: Session):
    hash_password = security.get_password_hash(user_create.password)
    new_user = User(
        **user_create.model_dump(exclude={"password"}),
        password=hash_password,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


def authenticate(user_login: user.UserLogin, session: Session):
    user = get_user_by_email(user_login.email, session)
    if not user:
        return None
    if not security.verify_password(user_login.password, user.password):
        return None
    return user
