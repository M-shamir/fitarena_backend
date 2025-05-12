import stripe
from django.conf import settings
from .base import PaymentGateway

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeGateway(PaymentGateway):
    def create_payment_intent(self, amount, currency, metadata=None):
        try:
            # For Checkout, we create a Session instead of PaymentIntent
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': metadata.get('product_name', 'Product'),
                        },
                        'unit_amount': int(float(amount) * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=metadata.get('success_url', settings.FRONTEND_SUCCESS_URL),
                cancel_url=metadata.get('cancel_url', settings.FRONTEND_CANCEL_URL),
                metadata=metadata or {}
            )
            return True, {
                'session_id': session.id,
                'url': session.url  # Redirect to this URL for Checkout
            }
        except stripe.error.StripeError as e:
            return False, str(e)

    def verify_payment(self, payment_id):
        try:
            session = stripe.checkout.Session.retrieve(payment_id)
            return True, {
                'id': session.id,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total / 100,
                'currency': session.currency,
                'metadata': session.metadata
            }
        except stripe.error.StripeError as e:
            return False, str(e)

    def refund_payment(self, payment_id, amount=None):
        try:
            # First get the PaymentIntent ID from the Session
            session = stripe.checkout.Session.retrieve(
                payment_id,
                expand=['payment_intent']
            )
            
            refund_params = {
                'payment_intent': session.payment_intent.id
            }
            if amount:
                refund_params['amount'] = int(amount * 100)
                
            refund = stripe.Refund.create(**refund_params)
            return True, {
                'id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status
            }
        except stripe.error.StripeError as e:
            return False, str(e)