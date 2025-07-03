from django.conf import settings
from .payment_gateways import stripe as stripe_gateway
from stadium_owner.models import Slot
import stripe


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
            metadata=metadata,
            success_url='http://localhost:3000/user/bookings/courses/success',
            cancel_url='http://localhost:3000/user/bookings/courses/cancel'
        )

        return {
            'payment_url': result['payment_url'],
            'session_id': result['session_id']
        }

    def create_slot_payment(self, user, slots):
        total_amount = sum(float(slot.price) for slot in slots)

        metadata = {
            'user_id': str(user.id),
            'slot_ids': ','.join(str(slot.id) for slot in slots),
            'product_name': f"Stadium Slot Booking ({len(slots)} slots)",
            'type': 'slot'
        }

        result = self.gateway.create_payment_intent(
            amount=total_amount,
            currency='INR',
            metadata=metadata,
            success_url='http://localhost:3000/user/bookings/slot/success',
            cancel_url='http://localhost:3000/user/bookings/slot/cancel'
        )

        return {
            'payment_url': result['payment_url'],
            'session_id': result['session_id']
        }

    def verify_payment(self, session_id):
        return self.gateway.verify_payment(session_id)


    def process_refund(self, session_id, amount=None):
    
        try:
            # Process refund through the gateway
            refund_success = self.gateway.refund_payment(
                session_id=session_id,  # Changed from payment_id to session_id
                amount=amount
            )
            
            return refund_success
        except Exception as e:
            raise Exception(f"Refund processing failed: {str(e)}")
        
    def get_refund_id(self, session_id):
    
        try:
            # Retrieve the most recent refund for this payment intent
            session = stripe.checkout.Session.retrieve(session_id)
            refunds = stripe.Refund.list(payment_intent=session.payment_intent, limit=1)
            return refunds.data[0].id if refunds.data else None
        except Exception:
            return None