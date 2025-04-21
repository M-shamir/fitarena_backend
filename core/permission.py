from rest_framework.permissions import BasePermission

class IsTrainer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'trainer'
