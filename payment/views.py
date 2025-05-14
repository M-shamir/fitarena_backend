from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import TrainerCource
from orders.models import Order,CourseEnrollment,SlotBooking
from .services.payment_service import PaymentService
from stadium_owner.models import Slot
from django.core.exceptions import ValidationError

class CreateCoursePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = TrainerCource.objects.get(id=course_id)
        except TrainerCource.DoesNotExist:
            return Response({'error': 'Course not found'}, status=404)

        payment_service = PaymentService()

        try:
            payment_data = payment_service.create_course_payment(request.user, course)
            return Response(payment_data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class VerifyPaymentAPIView(APIView):
    def get(self, request):
        session_id = request.GET.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID required'}, status=400)

        payment_service = PaymentService()

        try:
            verification = payment_service.verify_payment(session_id)
            if verification['paid']:
                metadata = verification.get('metadata', {})
                user_id = metadata.get('user_id')
                course_id = metadata.get('course_id')

                if user_id and course_id:
                    order = Order.objects.create(
                        user_id=user_id,
                        order_type='course',
                        stripe_session_id=session_id,
                        amount=verification['amount'],
                        currency=verification['currency'],
                        status='completed'
                    )

                    CourseEnrollment.objects.create(
                        order=order,
                        course_id=course_id
                    )

                    return Response({
                        'success': True,
                        'course_id': course_id
                    })

            return Response({'paid': False}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)



#slot
class CreateSlotPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        slot_ids = request.data.get('slot_ids', [])
        
        if not slot_ids:
            return Response({'error': 'No slots selected'}, status=400)
        
        try:
            slots = Slot.objects.filter(id__in=slot_ids, status='available')
            
            # Verify all slots are available and belong to same stadium
            if len(slots) != len(slot_ids):
                return Response({'error': 'Some slots are no longer available'}, status=400)
                
            stadium_id = slots[0].stadium_id
            if not all(slot.stadium_id == stadium_id for slot in slots):
                return Response({'error': 'Slots must be from the same stadium'}, status=400)
                
            payment_service = PaymentService()
            payment_data = payment_service.create_slot_payment(request.user, slots)
            return Response(payment_data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class VerifySlotPaymentAPIView(APIView):
    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID required'}, status=400)

        payment_service = PaymentService()

        try:
            verification = payment_service.verify_payment(session_id)
            if verification['paid']:
                metadata = verification.get('metadata', {})
                user_id = metadata.get('user_id')
                slot_ids = metadata.get('slot_ids', '').split(',')
                
                if user_id and slot_ids:
                    # Create order
                    order = Order.objects.create(
                        user_id=user_id,
                        order_type='slot',
                        stripe_session_id=session_id,
                        amount=verification['amount'],
                        currency=verification['currency'],
                        status='completed'
                    )
                    
                    # Create slot bookings
                    for slot_id in slot_ids:
                        slot = Slot.objects.get(id=slot_id)
                        SlotBooking.objects.create(
                            order=order,
                            slot=slot,
                            booking_date=slot.date
                        )
                        # Update slot status
                        slot.status = 'booked'
                        slot.booked_by_id = user_id
                        slot.save()
                    
                    return Response({
                        'success': True,
                        'slot_ids': slot_ids
                    })

            return Response({'paid': False}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)