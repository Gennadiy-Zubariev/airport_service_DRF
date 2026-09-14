from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    """Read access for any authenticated user, write access for staff only."""

    def has_permission(self, request, view):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )
