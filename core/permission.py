from rest_framework import permissions



class IsTrainer(permissions.BasePermission):
    """Allow only trainers to access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'trainer'

class IsStadiumOwner(permissions.BasePermission):
    """Allow only stadium owners to access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'stadium_owner'
