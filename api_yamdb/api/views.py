from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from reviews.models import Category, Genre, Title

from .filters import TitleFilter, UserFilter
from .permissions import IsAdmin, IsAuthorOrReadOnly
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    SignUpSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    TokenObtainSerializer,
    UserSerializer, UserCreateSerializer, UserUpdateSerializer
)


User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """Вьюсет для аутентификации."""

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'email': user.email, 'username': user.username},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='token')
    def token(self, request):
        serializer = TokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'token': serializer.validated_data['access_token'],
        })


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для работы с категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для работы с жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""

    queryset = Title.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TitleWriteSerializer
        return TitleReadSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    lookup_field = 'username'

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @action(
        detail=False, methods=['get', 'patch'],
        permission_classes=[IsAuthorOrReadOnly]
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
