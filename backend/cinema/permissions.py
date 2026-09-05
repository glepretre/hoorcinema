from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
    DjangoModelPermissions,
)

from cinema.roles import SPECTATOR_GROUP


class IsSpectator(BasePermission):
    message = "The spectator role is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name=SPECTATOR_GROUP).exists()
        )


class StaffDjangoModelPermissions(DjangoModelPermissions):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_staff
            and super().has_permission(request, view)
        )
