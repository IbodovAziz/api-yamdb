from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import NotFound

from reviews.models import (
    Category,
    Genre,
    Title,
    Review,
    Comment
)

from users.models import UserNameValidator

MIN_YEAR = settings.MIN_YEAR

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    def validate_username(self, value):
        if value and value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя "me" запрещено в качестве username')
        return value


class SignUpSerializer(BaseUserSerializer):
    username = serializers.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        validators=[UserNameValidator]
    )

    class Meta:
        model = User
        fields = ('email', 'username')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True}
        }

    def validate(self, data):
        username = data['username']
        email = data['email']

        users = User.objects.filter(
            Q(username=username) | Q(email=email)
        )

        for user in users:
            if user.username == username and user.email != email:
                raise serializers.ValidationError(
                    {'username': 'Введенный username занят'})
            if user.email == email and user.username != username:
                raise serializers.ValidationError(
                    {'email': 'Введенный email занят'})

        return data

    def create(self, validated_data):
        email = validated_data['email']
        username = validated_data['username']

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'is_active': False
            }
        )

        if not created:
            user.username = username
            user.is_active = False
            user.save()

        token = default_token_generator.make_token(user)

        self._send_confirmation_email(email, token)
        return user

    def _send_confirmation_email(self, email, token):
        subject = 'Код подтверждения для регистрации'
        message = f'Ваш код подтверждения: {token}'

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f'Ошибка отправки email: {e}')


class TokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.MAX_USERNAME_LENGTH)
    confirmation_code = serializers.CharField()

    def validate(self, data):
        username = data['username']
        confirmation_code = data['confirmation_code']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound({'detail': 'Неверные данные'})

        if not default_token_generator.check_token(user, confirmation_code):
            raise serializers.ValidationError('Неверный код подтверждения')

        user.is_active = True
        user.save()

        data['access_token'] = str(AccessToken.for_user(user))
        return data


class UserSerializer(BaseUserSerializer):
    """Сериализатор для пользователей."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        validated_data['is_active'] = False
        return super().create(validated_data)

    def validate(self, data):
        if self.instance is None:
            username = data.get('username')
            email = data.get('email')

            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    'username': 'Пользователь с таким username уже существует'
                })

            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    'email': 'Пользователь с таким email уже существует'
                })

        request = self.context.get('request')
        if 'role' in data and request and not request.user.is_admin:
            raise serializers.ValidationError({
                'role': 'Изменение роли доступно только администраторам'
            })

        return data


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий произведений."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров произведений."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных произведений."""

    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating',
            'description', 'genre', 'category'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления произведений."""

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = ('name', 'year', 'description', 'genre', 'category')

    def validate_year(self, value):
        current_year = timezone.now().year
        if value < MIN_YEAR:
            raise serializers.ValidationError(
                'Год не может быть отрицательным числом.'
            )
        if value > current_year:
            raise serializers.ValidationError(
                f'Год выпуска не должен превышать {current_year}.'
            )
        return value

    def to_representation(self, instance):
        return TitleReadSerializer(instance).data


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор отзывов."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        request = self.context['request']
        if request.method == 'POST':
            title_id = self.context.get('view').kwargs.get('title_pk')
            if Review.objects.filter(
                    title_id=title_id,
                    author=request.user
            ).exists():
                raise serializers.ValidationError(
                    'Можно оставить только один отзыв на произведение'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментариев."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
