from sqlmodel import Session, select

from app.models import user as UserModel, setting as SettingModel
from app.schemas import user as UserSchema
from app.core import security
from app.services import otp_service


def get_user_by_id(user_id: int, session: Session):
    statement = select(UserModel.User).where(UserModel.User.id == user_id)
    user = session.exec(statement).first()
    if not user:
        return None
    return user


def get_user_by_email(email: str, session: Session):
    statement = select(UserModel.User).where(UserModel.User.email == email)
    user = session.exec(statement).first()
    if not user:
        return None
    return user


def create_user(user_create: UserSchema.UserCreate, session: Session):
    hash_password = security.get_password_hash(user_create.password)
    new_user = UserModel.User(
        **user_create.model_dump(exclude={"password"}),
        password=hash_password,
    )
    session.add(new_user)
    session.flush()

    # Create default settings for the new user
    default_setting = SettingModel.Setting(user_id=new_user.id)
    session.add(default_setting)

    session.commit()
    session.refresh(new_user)
    return new_user


def authenticate_user(user_login: UserSchema.UserLogin, session: Session):
    user = get_user_by_email(user_login.email, session)
    if not user:
        return None
    if not security.verify_password(user_login.password, user.password):
        return None
    return user


def update_user(
    user_update: UserSchema.UserUpdate, user: UserModel.User, session: Session
):
    user_update_data = user_update.model_dump(exclude_unset=True)  # Important for PATCH
    for key, value in user_update_data.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user_password(
    user_password_update: UserSchema.UserPasswordUpdate,
    user: UserModel.User,
    session: Session,
):
    if not security.verify_password(
        user_password_update.current_password, user.password
    ):
        return None
    user.password = security.get_password_hash(user_password_update.new_password)
    session.add(user)
    session.commit()
    return True


def create_user_settings(user: UserModel.User, session: Session):
    settings = SettingModel.Setting(user_id=user.id)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def get_user_settings(user: UserModel.User, session: Session):
    statement = select(SettingModel.Setting).where(
        SettingModel.Setting.user_id == user.id
    )
    settings = session.exec(statement).first()
    if not settings:
        return create_user_settings(user, session)
    return settings


def update_user_settings(
    user_settings_update: UserSchema.UserSettingsUpdate,
    user: UserModel.User,
    session: Session,
):
    settings = get_user_settings(user, session)
    settings_update_data = user_settings_update.model_dump(
        exclude_unset=True
    )  # Important for PATCH
    for key, value in settings_update_data.items():
        setattr(settings, key, value)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def verify_signup_otp_and_create_user(data: UserSchema.SignupVerifyRequest, session: Session):
    record = otp_service.get_signup_otp(data.email)
    if not record or record.get("otp") != data.otp:
        return None
    user_create = UserSchema.UserCreate(**record["user_data"])
    user_obj = get_user_by_email(user_create.email, session)
    if user_obj:
        # Đã tồn tại user, không tạo nữa
        otp_service.delete_signup_otp(data.email)
        return None
    new_user = create_user(user_create, session)
    otp_service.delete_signup_otp(data.email)
    return new_user


def verify_forgot_otp_and_reset_password(data: UserSchema.ForgotPasswordVerifyRequest, session: Session):
    record = otp_service.get_forgot_otp(data.email)
    if not record or record.get("otp") != data.otp:
        return False
    user_obj = get_user_by_email(data.email, session)
    if not user_obj:
        otp_service.delete_forgot_otp(data.email)
        return False
    user_obj.password = security.get_password_hash(data.new_password)
    session.add(user_obj)
    session.commit()
    otp_service.delete_forgot_otp(data.email)
    return True
