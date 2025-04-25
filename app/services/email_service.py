import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

def send_otp_email(to_email: str, otp: str, subject: str = "Your OTP Code"):
    body = f"Your OTP code is: {otp}. It will expire in 5 minutes."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if getattr(settings, "SMTP_USE_TLS", False):
            server.starttls()
        if getattr(settings, "SMTP_USERNAME", None):
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
