from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .services.payment_service import PaymentService
import stripe
from django.conf import settings
from rest_framework import status
from orders.models import Order, CourseEnrollment
from trainer.models import TrainerCource
from stadium_owner.models import Slot
import json
import logging


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# views.py
class CreateCheckoutSessionView(APIView):
    def post(self, request):
        payment_service = PaymentService(request=request)
        
        success, response = payment_service.create_checkout_session(
            amount=request.data.get('amount'),
            currency=request.data.get('currency', 'inr'),
            metadata={
                'course_id': request.data.get('course_id'),
                'success_url': request.data.get('success_url'),
                'cancel_url': request.data.get('cancel_url'),
            }
        )
        
        if success:
            return Response(response)
        return Response({'error': response}, status=400)


class VerifyPaymentView(APIView):
    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_service = PaymentService()
        success, response = payment_service.verify_payment(session_id)
        
        if success:
            return Response(response, status=status.HTTP_200_OK)
        return Response({'error': response}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def stripe_webhook(request):
    logger.info("Webhook received")
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        
        try:
            # 1. Create Order record
            order = Order.objects.create(
                user=User.objects.get(id=metadata.get('user_id')),
                stripe_session_id=session.id,
                amount=session.amount_total / 100,
                currency=session.currency.upper(),
                status='completed',
                order_type='course' if 'course_id' in metadata else 'slot'
            )

            # 2. Handle course enrollment
            if 'course_id' in metadata:
                course = TrainerCource.objects.get(id=metadata['course_id'])
                CourseEnrollment.objects.create(
                    order=order,
                    course=course
                )
                # Add any additional enrollment logic here

            # 3. Log successful creation
            print(f"Successfully created order {order.id} for user {order.user.id}")
            
        except User.DoesNotExist:
            print(f"User not found: {metadata.get('user_id')}")
            return HttpResponse(status=400)
        except TrainerCource.DoesNotExist:
            print(f"Course not found: {metadata.get('course_id')}")
            return HttpResponse(status=400)
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)