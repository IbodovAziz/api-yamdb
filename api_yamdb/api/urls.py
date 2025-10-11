from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import (
    AuthViewSet,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    UserViewSet,
    ReviewViewSet,
    CommentViewSet
)

router_v1 = DefaultRouter()
router_v1.register('auth', AuthViewSet, basename='auth')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register('users', UserViewSet, basename='users')

titles_router = NestedSimpleRouter(router_v1, r'titles', lookup='title')
titles_router.register(r'reviews', ReviewViewSet, basename='title-reviews')

reviews_router = NestedSimpleRouter(titles_router, r'reviews', lookup='review')
reviews_router.register(r'comments', CommentViewSet, basename='review-comments')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/', include(titles_router.urls)),
    path('v1/', include(reviews_router.urls))
]
