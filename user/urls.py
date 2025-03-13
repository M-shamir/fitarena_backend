from django.urls import path
from .views import SignUpView,UserVerifyOtpView,UserResendOtpView,LoginView,RefreshTokenView

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path("token/refresh", RefreshTokenView.as_view(), name="token_refresh"),
]