from django.urls import path
from .views import *

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path('forgot-password/',UserForgotPasswordView.as_view(),name='user-forgot-password'),
    path('reset-password/',UserResetPasswordView.as_view(),name='reset-password'),
    path('profile/',UserProfileView.as_view(),name='profile'),
    path('trainers/available/', AvailableTrainerAPIView.as_view(), name='available-trainers'),
    path('trainers/<int:trainer_id>/courses/', TrainerCoursesAPIView.as_view(), name='trainer-courses'),
    path('courses/<int:course_id>/', CourseDetailAPIView.as_view(), name='course-detail'),
    path('stadiums/nearby/', NearbyStadiumsAPIView.as_view(), name='nearby_stadiums_api'),
    path('stadiums/<int:pk>/', StadiumDetailAPIView.as_view(), name='stadium-detail'),
    path('stadiums/<int:stadium_id>/available-slots/', AvailableUpcomingSlotsAPIView.as_view(), name='available_slots'),
    path('stadiums/<int:stadium_id>/slots/book/', BookSlotsAPIView.as_view(), name='book_slots'),
    path('logout/',UserLogoutView.as_view()),
    path('live-sessions/', UserLiveSessionsView.as_view(), name='user-live-sessions'),
    path('sessions/<int:session_id>/join/', UserJoinSessionView.as_view(), name='user-join-session'),
    
]