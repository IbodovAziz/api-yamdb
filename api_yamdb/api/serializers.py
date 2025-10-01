import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, ConfirmationCode, Genre, Title, User, UserNameValidator


class SignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UserNameValidator]
    )

    class Meta:
        model = User
        fields = ('email', 'username')
        extra_kwargs = {'username': {'required': True},
                        'email': {'required': True}}

    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поля username и email обязательны для заполнения")

        if (
                User.objects.filter(username=value).exists()
                or value.lower() == 'me'):
            raise serializers.ValidationError("Введенный username занят")

        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле email обязательны для заполнения")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Введенный email занят")
        return value

    def create(self, validated_data):
        code = ''.join(random.choices(string.digits, k=6))

        email = validated_data['email']
        ConfirmationCode.objects.update_or_create(
            email=email,
            defaults={'code': code}
        )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': validated_data['username'],
                'is_active': False
            }
        )

        if not created:
            user.username = validated_data['username']
            user.is_active = False
            user.save()

        self.send_confirmation_email(email, code)

        return user

    def send_confirmation_email(self, email, code):
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

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
        except Exception as e:
            # В случае ошибки отправки email, все равно продолжаем
            # Для отладки выводим ошибку
            print(f"Ошибка отправки email: {e}")
            # В продакшене можно залогировать ошибку
            # logger.error(f"Ошибка отправки email для {email}: {e}")


class TokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Пользователь не найден"},
                code='not_found'
            )

        try:
            code_obj = ConfirmationCode.objects.get(email=user.email)
            if not code_obj.is_valid():
                raise serializers.ValidationError("Код подтверждения истек")
            if code_obj.code != confirmation_code:
                raise serializers.ValidationError("Неверный код подтверждения")
        except ConfirmationCode.DoesNotExist:
            raise serializers.ValidationError("Код подтверждения не найден")

        user.is_active = True
        user.save()

        access_token = AccessToken.for_user(user)

        data['access_token'] = str(access_token)
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                "Использовать имя 'me' в качестве username запрещено")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
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

    def validate_username(self, value):
        if value and value.lower() == 'me':
            raise serializers.ValidationError(
                "Использовать имя 'me' в качестве username запрещено")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
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

    def validate_username(self, value):
        if value and value.lower() == 'me':
            raise serializers.ValidationError(
                "Использовать имя 'me' в качестве username запрещено")
        return value


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio'
        )
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
        }

    def validate_username(self, value):
        if value and value.lower() == 'me':
            raise serializers.ValidationError(
                "Использовать имя 'me' в качестве username запрещено")
        return value


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
