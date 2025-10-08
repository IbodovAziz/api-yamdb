from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings


UserNameValidator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='username может содержать только буквы, цифры и символы @/./+/-/_'
)


class User(AbstractUser):
    """
    Модель пользователя с расширенными полями.

    Наследуется от AbstractUser для сохранения стандартной функциональности.
    """

    username = models.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        unique=True,
        validators=[UserNameValidator],
        verbose_name='Имя пользователя',
        help_text='Обязательное поле. Не более 150 символов.'
        ' Только буквы, цифры и @/./+/-/_.',
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    email = models.EmailField(
        blank=True,
        verbose_name='Email адрес',
        help_text='Не более 254 символов.'
    )

    first_name = models.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        blank=True,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        blank=True,
        verbose_name='Фамилия'
    )

    bio = models.TextField(
        blank=True,
        verbose_name='Биография'
    )

    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    role = models.CharField(
        max_length=settings.MAX_ROLE_LENGTH,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(username='me'),
                name='username_not_me'
            )
        ]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR
