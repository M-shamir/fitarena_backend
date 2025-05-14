# services/payment_gateways/stripe.py
import stripe
from django.conf import settings
from django.urls import reverse
from .base import PaymentGateway

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentGateway(PaymentGateway):
    def __init__(self):
        pass

    def create_payment_intent(self, amount, currency, metadata=None, success_url=None, cancel_url=None):
        try:
            success_url = success_url or self.success_url
            cancel_url = cancel_url or self.cancel_url

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': metadata.get('product_name', 'Course Enrollment'),
                        },
                        'unit_amount': int(amount * 100),  # Stripe uses cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata=metadata or {},
            )

            return {
                'session_id': session.id,
                'payment_url': session.url
            }

        except Exception as e:
            raise Exception(f"Stripe error: {str(e)}")



    def verify_payment(self, session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'paid': session.payment_status == 'paid',
                'amount': session.amount_total / 100,
                'currency': session.currency,
                'metadata': session.metadata
            }
        except Exception as e:
            raise Exception(f"Stripe verification error: {str(e)}")

    def refund_payment(self, payment_id, amount=None):
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_id,
                amount=int(amount * 100) if amount else None
            )
            return refund.status == 'succeeded'
        except Exception as e:
            raise Exception(f"Stripe refund error: {str(e)}")