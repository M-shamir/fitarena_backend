from django.urls import path
from .views import TrainerSignUpView,TrainerVerifyOtpView,TrainerResendOtpView,TrainerLoginView,TrainerTypeListView,LanguageListView,TrainerLogoutView,TrainerProfileView,TrainerForgotPassword,TrainerResetPasswordView,TrainerCreateCourceView,PendingApprovalSessionsView,TrainerTypesView,ApprovedSessionsView,DeleteTrainerCourceView,TrainerPendingEditView
urlpatterns =  [
    path('auth/signup',TrainerSignUpView.as_view(),name='signup'),
    path('auth/verifyotp',TrainerVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',TrainerResendOtpView.as_view(),name='resendotp'),
    path('auth/login',TrainerLoginView.as_view(),name='trainerlogin'),
    path('forgot-password/',TrainerForgotPassword.as_view(),name='trainer-forgot-password'),
    path('reset-password/',TrainerResetPasswordView.as_view(),name='trainer-reset-passwod'),
    path("types/", TrainerTypeListView.as_view(), name="trainer-types"),
    path("languages/", LanguageListView.as_view(), name="trainer-languages"),
    path("profile/", TrainerProfileView.as_view(), name="trainer-profile"),
    path("create-course/", TrainerCreateCourceView.as_view(), name="create-trainer-course"),
    path('pending-approvals/', PendingApprovalSessionsView.as_view(), name='pending-approvals'), 
    path('trainer-types/', TrainerTypesView.as_view(), name='trainer-types'),
    path('approved-sessions/', ApprovedSessionsView.as_view(), name='approved-sessions'),
    path('trainer-cources/<int:pk>/',DeleteTrainerCourceView.as_view(),name='delete-trainer-course'),
    path('trainer-cources/<int:pk>/edit/',TrainerPendingEditView.as_view(),name='editpendingcource'),
    path('logout/',TrainerLogoutView.as_view()),

    
]