from rest_framework.permissions import BasePermission
from core.models import Branch


class IsBranchAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "baranch_admin"
        )
