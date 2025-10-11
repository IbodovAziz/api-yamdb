from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from api import views


router_v1 = DefaultRouter()
router_v1.register('categories', views.CategoryViewSet, basename='categories')
router_v1.register('genres', views.GenreViewSet, basename='genres')
router_v1.register('titles', views.TitleViewSet, basename='titles')
router_v1.register('users', views.UserViewSet, basename='users')

titles_router = NestedSimpleRouter(router_v1, r'titles', lookup='title')
titles_router.register(r'reviews', views.ReviewViewSet, basename='title-reviews')

reviews_router = NestedSimpleRouter(titles_router, r'reviews', lookup='review')
reviews_router.register(r'comments', views.CommentViewSet, basename='review-comments')

urlpatterns = [
    path('v1/auth/signup/', views.signup),
    path('v1/auth/token/', views.token),
    path('v1/', include(router_v1.urls)),
    path('v1/', include(titles_router.urls)),
    path('v1/', include(reviews_router.urls))
]
