from django.urls import path
from .views import TrainerSignUpView,TrainerVerifyOtpView,TrainerResendOtpView,TrainerLoginView,TrainerTypeListView,LanguageListView,TrainerLogoutView
urlpatterns =  [
    path('auth/signup',TrainerSignUpView.as_view(),name='signup'),
    path('auth/verifyotp',TrainerVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',TrainerResendOtpView.as_view(),name='resendotp'),
    path('auth/login',TrainerLoginView.as_view(),name='trainerlogin'),
    path("types/", TrainerTypeListView.as_view(), name="trainer-types"),
    path("languages/", LanguageListView.as_view(), name="trainer-languages"),
    path('logout/',TrainerLogoutView.as_view()),
    
]