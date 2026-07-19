"""
Custom permission classes for the Library Management API.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to any authenticated
    or anonymous request, but restricts write operations (POST, PUT,
    PATCH, DELETE) to staff/admin users only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsLibrarianOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to everyone, but restricts write operations
    to users whose linked UserProfile has is_librarian=True (or who are
    Django staff/superusers).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True

        profile = getattr(user, 'library_profile', None)
        return bool(profile and profile.is_librarian)
