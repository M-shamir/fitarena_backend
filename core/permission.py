from rest_framework.permissions import BasePermission

class IsTrainer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'trainer'


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and (
                request.user.is_superuser or  # allow superusers too
                getattr(request.user, "role", None) == "admin"
            )
        )

class IsStadiumOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'stadium_owner'