from rest_framework.permissions import BasePermission


class IsBranchAdmin(BasePermission):
    def has_permission(self, request, view):
        SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.role == "branch_admin"
