from django.urls import path
from .views import *

urlpatterns =  [
    path('auth/signup',StadiumOwnerSignUpView.as_view(),name='stadium_owner_signup'),
    path('auth/verifyotp',StadiumOwnerVerifyOtpView.as_view(),name='stadium_owner_verifyotp'),
    path('auth/resendotp',StadiumOwnerResendOtpView.as_view(),name='stadium_owner_resendotp'),
    path('auth/login',StadiumOwnerLoginView.as_view(),name='stadium_owner_trainerlogin'),
    path("auth/refresh-token", StadiumOwnerTokenRefreshView.as_view(), name="stadium_owner_token_refresh"),
    path('profile/',StadiumOwnerProfile.as_view(),name='stadium_owner-profile'),
    path('stadiums/create/', StadiumCreateView.as_view(), name='stadium-create'),
    path('stadiums/pending/', PendingStadiumListView.as_view(), name='pending-stadiums'),
    path('stadiums/edit/<int:pk>/', StadiumOwnerEditPendingView.as_view(), name='owner-edit-pending-stadium'),
    path('stadiums/delete/<int:pk>/', StadiumSoftDeleteView.as_view(), name='stadium-soft-delete'),
    path('slots/create/', SlotCreateAPIView.as_view(), name='create-slot'),
    path('approved-stadiums/', ApprovedStadiumsListView.as_view(), name='approved_stadiums'),
    path('slots/<int:stadium_id>/', SlotListAPIView.as_view(), name='slot-list'),
    path('stadiums/unassigned/', UnassignedStadiumsAPIView.as_view(), name='unassigned-stadiums'),
    path('orders/', StadiumOwnerOrderListView.as_view(), name='stadium-owner-orders'),
    path('payment-history/', StadiumOwnerPaymentHistoryAPIView.as_view(), name='stadium-owner-payment-history'),
    path('logout/',StadiumOwnerLogoutView.as_view()),
    
]