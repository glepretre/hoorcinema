from rest_framework.permissions import SAFE_METHODS, DjangoModelPermissions


class StaffDjangoModelPermissions(DjangoModelPermissions):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_staff
            and super().has_permission(request, view)
        )
