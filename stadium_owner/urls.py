from django.urls import path
from .views import StadiumOwnerSignUpView,StadiumOwnerLoginView,StadiumOwnerVerifyOtpView,StadiumOwnerResendOtpView
urlpatterns =  [
    path('auth/signup',StadiumOwnerSignUpView.as_view(),name='stadium_owner_signup'),
    path('auth/verifyotp',StadiumOwnerVerifyOtpView.as_view(),name='stadium_owner_verifyotp'),
    path('auth/resendotp',StadiumOwnerResendOtpView.as_view(),name='stadium_owner_resendotp'),
    path('auth/login',StadiumOwnerLoginView.as_view(),name='stadium_owner_trainerlogin')
]