from django.urls import path
from .views import (
    AdminLoginView,
    UserListView,
    BlockUnblockUserView,
    TrainerPendingAprrovalView,
    ApproveTrainerView,
    RejectTrainerView,
    ApprovedTrainerListView,
    ListUnlistTrainerView,
    PendingStadiumOwnerApprovalView,
    ApprovedStadiumOwnerListView,
    ApprovedStadiumOwnerView,
    RejectStadiumOwnerView,
    ListUnlistStadiumOwnerView,
    PendingStadiumListView,
    ApprovedStadiumListView,
    ApproveStadiumView,
    RejectStadiumView,
    ListUnlistStadiumView

)

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("users/", UserListView.as_view(), name="admin-users"),
    path('users/<int:user_id>/block-unblock/',BlockUnblockUserView.as_view(),name="block-unblock-user"),
    path('trainers/pending/',TrainerPendingAprrovalView.as_view(),name="pending-trainers"),
    path("trainers/<int:trainer_id>/approve/", ApproveTrainerView.as_view(), name="approve-trainer"),
    path("trainers/<int:trainer_id>/reject/", RejectTrainerView.as_view(), name="reject-trainer"),
    path('trainers/approved/', ApprovedTrainerListView.as_view(), name='approved-trainers'),
    path("trainers/<int:trainer_id>/list-unlist/", ListUnlistTrainerView.as_view()),
    path('stadium_owner/pending/',PendingStadiumOwnerApprovalView.as_view(),name="pending-stadium_owner"),
    path('stadium_owner/approved/',ApprovedStadiumOwnerListView.as_view(),name="approved-stadium_owner"),
    path("stadium_owner/<int:stadium_owner_id>/approve/", ApprovedStadiumOwnerView.as_view(), name="approve-stadium_owner"),
    path("stadium_owner/<int:stadium_owner_id>/reject/", RejectStadiumOwnerView.as_view(), name="reject-stadium_owner"),
    path("stadium_owner/<int:stadium_owner_id>/list-unlist/", ListUnlistStadiumOwnerView.as_view()),
    path('stadiums/pending-approval/',PendingStadiumListView.as_view(),name="pending-stadium-approval"),
    path('stadiums/approved/',ApprovedStadiumListView.as_view(),name="pending-stadium-approved"),
    path('stadiums/<int:stadium_id>/approve/', ApproveStadiumView.as_view(), name='approve-stadium'),
    path('stadiums/<int:stadium_id>/reject/', RejectStadiumView.as_view(), name='reject-stadium'),
    path("stadiums/<int:stadium_id>/list-toggle/", ListUnlistStadiumView.as_view()),


]
