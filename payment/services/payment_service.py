from django.conf import settings
from .payment_gateways.stripe import StripeGateway

class PaymentService:
    def __init__(self, gateway='stripe', request=None):
        if gateway == 'stripe':
            self.gateway = StripeGateway()
        else:
            raise ValueError("Unsupported gateway")
        self.request = request  # Store the request object

    def create_checkout_session(self, amount, currency, metadata=None):
        """Specific method for Stripe Checkout"""
        if not metadata:
            metadata = {}
        
        # Ensure required URLs are set
        if self.request and self.request.user.is_authenticated:
            metadata.setdefault('user_id', self.request.user.id)
        metadata.setdefault('success_url', settings.FRONTEND_SUCCESS_URL)
        metadata.setdefault('cancel_url', settings.FRONTEND_CANCEL_URL)
        
        return self.gateway.create_payment_intent(amount, currency, metadata)
    
    def verify_payment(self, payment_id):
        return self.gateway.verify_payment(payment_id)
    
    def refund_payment(self, payment_id, amount=None):
        return self.gateway.refund_payment(payment_id, amount)