from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, CategoryViewSet, GenreViewSet, TitleViewSet, UserViewSet, ReviewViewSet, CommentViewSet

router_v1 = DefaultRouter()
router_v1.register('auth', AuthViewSet, basename='auth')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register('users', UserViewSet, basename='users')

review_list = ReviewViewSet.as_view({'get': 'list', 'post': 'create'})
review_detail = ReviewViewSet.as_view({
    'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'
})

comment_list = CommentViewSet.as_view({'get': 'list', 'post': 'create'})
comment_detail = CommentViewSet.as_view({
    'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'
})

nested_urls = [
    path('titles/<int:title_id>/reviews/', review_list, name='review-list'),
    path('titles/<int:title_id>/reviews/<int:pk>/', review_detail, name='review-detail'),
    path('titles/<int:title_id>/reviews/<int:review_id>/comments/', comment_list, name='comment-list'),
    path('titles/<int:title_id>/reviews/<int:review_id>/comments/<int:pk>/', comment_detail, name='comment-detail'),
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/', include(nested_urls))
]
