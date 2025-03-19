from django.urls import path
from .views import SignUpView,UserVerifyOtpView,UserResendOtpView,LoginView,UserForgotPasswordView,UserResetPasswordView

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path('forgot-password/',UserForgotPasswordView.as_view(),name='forgot-password'),
    path('reset-password/',UserResetPasswordView.as_view(),name='reset-password')
    
]