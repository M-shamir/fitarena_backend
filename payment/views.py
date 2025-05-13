from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import TrainerCource
from orders.models import Order,CourseEnrollment,SlotBooking
from .services.payment_service import PaymentService

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
