from django.core.mail import send_mail
from django.conf import settings

def send_password_reset_email(email,reset_link):
    subject = "Reset Your Password"
    message = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, ignore this email."
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
        logger.info(f"OTP sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: {str(e)}")