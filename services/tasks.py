from celery import shared_task
from services.email_service import send_otp_email

@shared_task
def send_otp_email_task(user_email, otp):
    send_otp_email(user_email, otp)
