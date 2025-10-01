from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Только для администраторов и суперпользователей."""

    def has_permission(self, request, view):
        return request.user and (
            request.user.is_admin or request.user.is_superuser
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Чтение для всех, изменение только для администраторов."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user and (
                request.user.is_admin
                or request.user.is_superuser
            )
        )


class IsModerator(permissions.BasePermission):
    """Только для модераторов, администраторов и суперпользователей."""

    def has_permission(self, request, view):
        return (request.user
                and (
                    request.user.is_moderator
                    or request.user.is_admin
                    or request.user.is_superuser
                ))


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Чтение - все, создание - аутентифицированные пользователи
    Изменение/удаление: автор, модератор или администратор
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user
            or request.user.is_moderator
            or request.user.is_admin
            or request.user.is_superuser
        )
