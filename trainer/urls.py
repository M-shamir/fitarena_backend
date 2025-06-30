from django.urls import path
from .views import *
urlpatterns =  [
    path('auth/signup',TrainerSignUpView.as_view(),name='signup'),
    path('auth/verifyotp',TrainerVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',TrainerResendOtpView.as_view(),name='resendotp'),
    path('auth/login',TrainerLoginView.as_view(),name='trainerlogin'),
    path("auth/refresh-token", TrainerTokenRefreshView.as_view(), name="trainer_token_refresh"),
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
    path('courses/enrollments/', TrainerCourseEnrollmentsView.as_view(), name='trainer-course-enrollments'),
    path('courses/<int:course_id>/enrolled-users/', CourseEnrolledUsersView.as_view(),name='course-enrolled-users'),
    path('live-sessions/', TrainerLiveSessionsView.as_view(), name='trainer-live-sessions'),
    path('sessions/<int:session_id>/join/', JoinSessionView.as_view(), name='join-session'),
    path('dashboard/stats/', DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('payment-history/', TrainerPaymentHistoryAPIView.as_view(), name='trainer-payment-history'),
    
   

    
]