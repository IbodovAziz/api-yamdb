from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from api import views


router_v1 = DefaultRouter()
router_v1.register('categories', views.CategoryViewSet, basename='categories')
router_v1.register('genres', views.GenreViewSet, basename='genres')
router_v1.register('titles', views.TitleViewSet, basename='titles')
router_v1.register('users', views.UserViewSet, basename='users')

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
    path('titles/<int:title_id>/reviews/<int:pk>/',
         review_detail, name='review-detail'),
    path('titles/<int:title_id>/reviews/<int:review_id>/comments/',
         comment_list, name='comment-list'),
    path(
        'titles/<int:title_id>/reviews/<int:review_id>/comments/<int:pk>/',
        comment_detail,
        name='comment-detail'
    ),
]

urlpatterns = [
    path('v1/auth/signup/', views.signup),
    path('v1/auth/token/', views.token),
    path('v1/', include(router_v1.urls)),
    path('v1/', include(titles_router.urls)),
    path('v1/', include(reviews_router.urls))
]
