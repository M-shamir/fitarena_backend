from django.urls import path
from .views import AdminLoginView,UserListView,BlockUnblockUserView

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("users/", UserListView.as_view(), name="admin-users"),
    path('users/<int:user_id>/block-unblock/',BlockUnblockUserView.as_view(),name="block-unblock-user")

]
