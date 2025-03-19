from django.urls import path
from .views import TrainerSignUpView,TrainerVerifyOtpView,TrainerResendOtpView,TrainerLoginView
urlpatterns =  [
    path('auth/signup',TrainerSignUpView.as_view(),name='signup'),
    path('auth/verifyotp',TrainerVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',TrainerResendOtpView.as_view(),name='resendotp'),
    path('auth/login',TrainerLoginView.as_view(),name='trainerlogin')
    
]