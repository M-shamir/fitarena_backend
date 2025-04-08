from django.urls import path
from .views import SignUpView,UserVerifyOtpView,UserResendOtpView,LoginView,UserForgotPasswordView,UserResetPasswordView,UserLogoutView,UserProfileView

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path('forgot-password/',UserForgotPasswordView.as_view(),name='user-forgot-password'),
    path('reset-password/',UserResetPasswordView.as_view(),name='reset-password'),
    path('profile/',UserProfileView.as_view(),name='profile'),
    path('logout/',UserLogoutView.as_view())
    
]