from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator
)
from django.db import models
from django.conf import settings
from django.utils import timezone


User = get_user_model()

SlugValidator = RegexValidator(
    regex=r'^[-a-zA-Z0-9_]+$',
    message='Slug может содержать только латинские буквы,'
    ' цифры, дефис и подчеркивание.'
)


class Category(models.Model):
    """Модель категорий произведений."""

    name = models.CharField(
        'Название категории',
        max_length=settings.MAX_NAME_LENGTH
    )
    slug = models.SlugField(
        'Слаг категории', unique=True,
        max_length=settings.MAX_SLUG_LENGTH,
        validators=(SlugValidator,)
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель жанров произведений."""

    name = models.CharField(
        'Название жанра', max_length=settings.MAX_NAME_LENGTH)
    slug = models.SlugField(
        'Слаг жанра', unique=True,
        max_length=settings.MAX_SLUG_LENGTH,
        validators=(SlugValidator,)
    )

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
    """Модель отзывов на произведения."""

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
            settings.MIN_SCORE_VALUE),
            MaxValueValidator(settings.MAX_SCORE_VALUE)]
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
    """Модель комментариев к отзывам."""

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
