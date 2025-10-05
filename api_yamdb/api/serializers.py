import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.validators import RegexValidator
from rest_framework.exceptions import NotFound


from reviews.models import (
    Category,
    ConfirmationCode,
    Genre,
    Title,
    User,
    UserNameValidator,
    Review,
    Comment
)


MIN_YEAR = 0


class BaseUserSerializer(serializers.ModelSerializer):
    def validate_username(self, value):
        if value and value.lower() == 'me':
            raise serializers.ValidationError(
                "Имя 'me' запрещено в качестве username")
        return value


class SignUpSerializer(BaseUserSerializer):
    username = serializers.CharField(
        max_length=150,
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
                    {"username": "Введенный username занят"})
            if user.email == email and user.username != username:
                raise serializers.ValidationError(
                    {"email": "Введенный email занят"})

        return data

    def create(self, validated_data):
        email = validated_data['email']
        username = validated_data['username']
        code = ''.join(random.choices(
            string.digits, k=settings.CONFIRMATION_CODE_LENGTH))

        ConfirmationCode.objects.update_or_create(
            email=email,
            defaults={'code': code, 'created_at': timezone.now()}
        )

        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                'username': username,
                'is_active': False
            }
        )

        self._send_confirmation_email(email, code)
        return user

    def _send_confirmation_email(self, email, code):
        subject = 'Код подтверждения для регистрации'
        message = f'Ваш код подтверждения: {code}'

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Ошибка отправки email: {e}")


class TokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField()

    def validate(self, data):
        username = data['username']
        confirmation_code = data['confirmation_code']

        try:
            user = User.objects.get(username=username)
            code_obj = ConfirmationCode.objects.get(email=user.email)
        except (User.DoesNotExist, ConfirmationCode.DoesNotExist):
            raise NotFound({"detail": "Неверные данные"})

        if not code_obj.is_valid():
            raise serializers.ValidationError("Код подтверждения истек")
        if code_obj.code != confirmation_code:
            raise serializers.ValidationError("Неверный код подтверждения")

        user.is_active = True
        user.save()

        data['access_token'] = str(AccessToken.for_user(user))
        return data


class UserSerializer(BaseUserSerializer):
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
                    "username": "Пользователь с таким username уже существует"
                })

            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    "email": "Пользователь с таким email уже существует"
                })

        return data


slug_validators = [
    RegexValidator(
        regex=r'^[-a-zA-Z0-9_]+$',
        message="Slug может содержать только латинские буквы,"
        " цифры, дефис и подчеркивание."
    ),
]


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        min_length=1,
        max_length=50,
        validators=slug_validators,
        help_text="Slug (максимум 50 символов): только латинские буквы,"
        " цифры, дефис и подчеркивание"
    )

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        min_length=1,
        max_length=50,
        validators=slug_validators,
        help_text="Slug (максимум 50 символов): только латинские буквы,"
        " цифры, дефис и подчеркивание"
    )

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
            'id', 'name', 'year',
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
            title_id = self.context.get('view').kwargs.get('title_id')
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
