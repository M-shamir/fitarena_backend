from django.urls import path
from .views import (
  
    StadiumOwnerSignUpView,
    StadiumOwnerLoginView,
    StadiumOwnerVerifyOtpView,
    StadiumOwnerResendOtpView,
    StadiumOwnerProfile, 
    StadiumCreateView,
    PendingStadiumListView,
    StadiumOwnerEditPendingView,
    StadiumSoftDeleteView,
    StadiumOwnerLogoutView
)

urlpatterns =  [
    path('auth/signup',StadiumOwnerSignUpView.as_view(),name='stadium_owner_signup'),
    path('auth/verifyotp',StadiumOwnerVerifyOtpView.as_view(),name='stadium_owner_verifyotp'),
    path('auth/resendotp',StadiumOwnerResendOtpView.as_view(),name='stadium_owner_resendotp'),
    path('auth/login',StadiumOwnerLoginView.as_view(),name='stadium_owner_trainerlogin'),
    path('profile/',StadiumOwnerProfile.as_view(),name='stadium_owner-profile'),
    path('stadiums/create/', StadiumCreateView.as_view(), name='stadium-create'),
    path('stadiums/pending/', PendingStadiumListView.as_view(), name='pending-stadiums'),
    path('stadiums/edit/<int:pk>/', StadiumOwnerEditPendingView.as_view(), name='owner-edit-pending-stadium'),
    path('stadiums/delete/<int:pk>/', StadiumSoftDeleteView.as_view(), name='stadium-soft-delete'),

    path('logout/',StadiumOwnerLogoutView.as_view()),
    
]