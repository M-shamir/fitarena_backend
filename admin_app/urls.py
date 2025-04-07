from django.urls import path
from .views import AdminLoginView,UserListView,BlockUnblockUserView,TrainerPendingAprrovalView,ApproveTrainerView,RejectTrainerView,ApprovedTrainerListView

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("users/", UserListView.as_view(), name="admin-users"),
    path('users/<int:user_id>/block-unblock/',BlockUnblockUserView.as_view(),name="block-unblock-user"),
    path('trainers/pending/',TrainerPendingAprrovalView.as_view(),name="pending-trainers"),
    path("trainers/<int:trainer_id>/approve/", ApproveTrainerView.as_view(), name="approve-trainer"),
    path("trainers/<int:trainer_id>/reject/", RejectTrainerView.as_view(), name="reject-trainer"),
    path('trainers/approved/', ApprovedTrainerListView.as_view(), name='approved-trainers'),
    


]
