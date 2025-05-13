# services/payment_service.py
from django.conf import settings
from .payment_gateways import stripe as stripe_gateway

class PaymentService:
    def __init__(self):
        self.gateway = stripe_gateway.StripePaymentGateway()

    def create_course_payment(self, user, course):
        metadata = {
            'user_id': str(user.id),
            'course_id': str(course.id),
            'product_name': course.title,
            'type': 'course'
        }
        
        result = self.gateway.create_payment_intent(
            amount=course.price,
            currency='INR',
            metadata=metadata
        )
        
        return {
            'payment_url': result['payment_url'],
            'session_id': result['session_id']
        }

    def verify_payment(self, session_id):
        return self.gateway.verify_payment(session_id)