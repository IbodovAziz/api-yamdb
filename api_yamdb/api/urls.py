from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, CategoryViewSet, GenreViewSet, TitleViewSet, UserViewSet

router_v1 = DefaultRouter()
router_v1.register('auth', AuthViewSet, basename='auth')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
