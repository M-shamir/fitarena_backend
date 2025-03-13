from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
def send_otp_email(user,otp):
    subject = "Your OTP For Verification"
    message =  f'{otp}'
    recipient_list = [user.email]
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
        logger.info(f"OTP sent successfully to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send OTP to {user.email}: {str(e)}")