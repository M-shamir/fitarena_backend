from celery import shared_task
from services.email_service import send_otp_email
from services.sendresetpasswordmail import send_password_reset_email

@shared_task
def send_otp_email_task(user_email, otp):
    send_otp_email(user_email, otp)

@shared_task
def send_password_reset_email_task(user_email, reset_link):
    send_password_reset_email(user_email, reset_link)