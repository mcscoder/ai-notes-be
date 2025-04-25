import random
from app.core.redis import redis_client

OTP_EXPIRE_SECONDS = 300  # 5 phút

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def save_signup_otp(email: str, user_data: dict, otp: str):
    redis_key = f"signup:{email}"
    redis_client.set(redis_key, {
        "otp": otp,
        "user_data": user_data,
    }, expire_seconds=OTP_EXPIRE_SECONDS)

def get_signup_otp(email: str):
    redis_key = f"signup:{email}"
    return redis_client.get(redis_key)

def delete_signup_otp(email: str):
    redis_key = f"signup:{email}"
    redis_client.delete(redis_key)

def save_forgot_otp(email: str, otp: str):
    redis_key = f"forgot:{email}"
    redis_client.set(redis_key, {"otp": otp}, expire_seconds=OTP_EXPIRE_SECONDS)

def get_forgot_otp(email: str):
    redis_key = f"forgot:{email}"
    return redis_client.get(redis_key)

def delete_forgot_otp(email: str):
    redis_key = f"forgot:{email}"
    redis_client.delete(redis_key)
