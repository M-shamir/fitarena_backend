# views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, CourseEnrollment, SlotBooking
from .serializers import OrderSerializer, CourseEnrollmentSerializer, SlotBookingSerializer

class UserBookingsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        
        orders = Order.objects.filter(user=user).prefetch_related(
            'course_enrollment',
            'slot_bookings'
        ).order_by('-created_at')
        
        
        course_enrollments = []
        slot_bookings = []
        
        for order in orders:
            if order.order_type == 'course' and hasattr(order, 'course_enrollment'):
                course_enrollments.append(order.course_enrollment)
            elif order.order_type == 'slot':
                slot_bookings.extend(order.slot_bookings.all())
        
        
        course_serializer = CourseEnrollmentSerializer(course_enrollments, many=True)
        slot_serializer = SlotBookingSerializer(slot_bookings, many=True)
        
        return Response({
            'course_enrollments': course_serializer.data,
            'slot_bookings': slot_serializer.data
        })
    

