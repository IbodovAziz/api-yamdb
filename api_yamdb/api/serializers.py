import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import NotFound

from reviews.models import Category, ConfirmationCode, Genre, Title, User, UserNameValidator


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
        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            raise serializers.ValidationError(
                "Поля username и email обязательны для заполнения")

        user_exists = User.objects.filter(email=email).exists()
        username_exists = User.objects.filter(username=username).exists()

        if username_exists and username.lower() != 'me':
            existing_user = User.objects.get(username=username)
            if existing_user.email != email:
                raise serializers.ValidationError(
                    {"username": "Введенный username занят"})
        elif username.lower() == 'me':
            raise serializers.ValidationError(
                {"username": "Введенный username занят"})

        if user_exists:
            existing_user = User.objects.get(email=email)
            if existing_user.username != username:
                raise serializers.ValidationError(
                    {"email": "Введенный email занят"})

        return data

    def create(self, validated_data):
        code = ''.join(random.choices(string.digits, k=6))
        email = validated_data['email']
        username = validated_data['username']

        ConfirmationCode.objects.update_or_create(
            email=email,
            defaults={'code': code}
        )

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

        self._send_confirmation_email(email, code)
        return user

    def _send_confirmation_email(self, email, code):
        """Отправка email с кодом подтверждения"""
        subject = 'Код подтверждения для регистрации'
        message = f'''
        Здравствуйте!

        Ваш код подтверждения для регистрации: {code}

        Введите этот код для завершения регистрации.

        Код действителен в течение 5 минут.

        Если вы не запрашивали регистрацию, проигнорируйте это письмо.

        С уважением,
        Команда проекта
        '''

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
        except User.DoesNotExist:
            raise NotFound({"detail": "Пользователь не найден"})

        try:
            code_obj = ConfirmationCode.objects.get(email=user.email)
        except ConfirmationCode.DoesNotExist:
            raise serializers.ValidationError("Код подтверждения не найден")

        if not code_obj.is_valid():
            raise serializers.ValidationError("Код подтверждения истек")
        if code_obj.code != confirmation_code:
            raise serializers.ValidationError("Неверный код подтверждения")

        user.is_active = True
        user.save()

        data['access_token'] = str(AccessToken.for_user(user))
        data['user'] = user
        return data


class UserSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )


class UserCreateSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )

    def create(self, validated_data):
        validated_data['is_active'] = False
        return super().create(validated_data)

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {"username": "Пользователь с таким username уже существует"})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "Пользователь с таким email уже существует"})

        return data


class UserUpdateSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
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
        if value > timezone.now().year:
            raise serializers.ValidationError(
                'Год выпуска не должен превышать текущий'
            )
        return value

    def to_representation(self, instance):
        return TitleReadSerializer(instance).data
