from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.conf import settings
from django.utils import timezone


UserNameValidator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='username может содержать только буквы, цифры и символы @/./+/-/_'
)


class User(AbstractUser):
    """
    Модель пользователя с расширенными полями.
    Наследуется от AbstractUser для сохранения стандартной функциональности Django.
    """

    username = models.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        unique=True,
        validators=[UserNameValidator],
        verbose_name='Имя пользователя',
        help_text='Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_.',
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


class ConfirmationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=settings.CONFIRMATION_CODE_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() < settings.CONFIRMATION_TTL


class Category(models.Model):
    """Модель категорий произведений"""
    name = models.CharField('Название категории',
                            max_length=settings.MAX_NAME_LENGTH)
    slug = models.SlugField('Слаг категории', unique=True,
                            max_length=settings.MAX_SLUG_LENGTH)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель жанров произведений"""
    name = models.CharField(
        'Название жанра', max_length=settings.MAX_NAME_LENGTH)
    slug = models.SlugField('Слаг жанра', unique=True,
                            max_length=settings.MAX_SLUG_LENGTH)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель произведений."""
    name = models.CharField('Название произведения',
                            max_length=settings.MAX_NAME_LENGTH)
    description = models.TextField('Описание', blank=True)
    year = models.IntegerField(
        verbose_name='Год выпуска',
        validators=[
            MinValueValidator(
                settings.MIN_YEAR,
                message='Год не может быть отрицательным'
            ),
            MaxValueValidator(
                timezone.now().year,
                message='Год не может превышать текущий'
            )
        ]
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titles',
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        related_name='titles_set',
        verbose_name='Жанр'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name='titles'
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='genres'
    )

    def __str__(self):
        return f'{self.genre} {self.title}'


class Review(models.Model):
    """Модель отзывов на произведения"""
    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField('Текст')
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='Оценка',
        validators=[MinValueValidator(
            settings.MIN_SCORE_VALUE), MaxValueValidator(settings.MAX_SCORE_VALUE)]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-pub_date']
        constraints = (
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='unique_review_per_author',
            ),
        )

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    """Модель комментариев к отзывам"""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    text = models.TextField('Текст комментария')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-pub_date']

    def __str__(self):
        return f'Комментарий {self.author} к отзыву {self.review.id}'
