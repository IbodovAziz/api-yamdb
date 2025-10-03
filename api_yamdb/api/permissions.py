from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Разрешает доступ только администраторам."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Публичное чтение, но запись только администраторам."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsModeratorOrAuthorOrReadOnly(permissions.BasePermission):
    """Чтение для всех, модератор или автор могут менять/удалять."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        is_author = obj.author == request.user
        is_moderator = getattr(request.user, 'is_moderator', False)
        is_admin = getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_superuser', False)
        return bool(is_author or is_moderator or is_admin)
