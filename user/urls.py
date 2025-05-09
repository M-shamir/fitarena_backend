from django.urls import path
from .views import SignUpView,UserVerifyOtpView,UserResendOtpView,LoginView,UserForgotPasswordView,UserResetPasswordView,UserLogoutView,UserProfileView,UserTrainerCoursesView,UserTrainerCourseDetailView,NearbyStadiumsAPIView,StadiumDetailAPIView

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path('forgot-password/',UserForgotPasswordView.as_view(),name='user-forgot-password'),
    path('reset-password/',UserResetPasswordView.as_view(),name='reset-password'),
    path('profile/',UserProfileView.as_view(),name='profile'),
    path('trainer-courses/', UserTrainerCoursesView.as_view(), name='user-trainer-courses'),
    path('courses/<int:course_id>/', UserTrainerCourseDetailView.as_view(), name='trainer-course-detail'),
    path('stadiums/nearby/', NearbyStadiumsAPIView.as_view(), name='nearby_stadiums_api'),
    path('stadiums/<int:pk>/', StadiumDetailAPIView.as_view(), name='stadium-detail'),
    path('logout/',UserLogoutView.as_view())
    
]