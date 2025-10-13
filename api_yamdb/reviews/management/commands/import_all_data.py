import csv
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404

from reviews.models import Category, Comment, Genre, Review, Title


User = get_user_model()


class Command(BaseCommand):
    help = "Импортируем все данные из CSV файлов"

    def handle(self, *args, **options):
        self.import_users()
        self.import_categories()
        self.import_genres()
        self.import_titles()
        self.import_genre_titles()
        self.import_reviews()
        self.import_comments()

    def import_users(self):
        """Импорт пользователей."""
        self.stdout.write("Импортируем пользователей.")
        try:
            with open('static/data/users.csv', mode='r',
                      encoding='utf-8') as file:
                objects_to_create = []
                reader = csv.DictReader(file)
                for row in reader:
                    objects_to_create.append(
                        User(
                            id=row['id'],
                            username=row['username'],
                            email=row['email'],
                            role=row['role'],
                            bio=row['bio'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                        )
                    )
                User.objects.bulk_create(objects_to_create)
                self.stdout.write(
                    self.style.SUCCESS("Пользователи импортированы."))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/users.csv не найден."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при импорте пользователей: {e}.'))

    def import_categories(self):
        """Импорт категорий."""
        self.stdout.write("Импортируем категории.")
        try:
            with open('static/data/category.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        Category.objects.get_or_create(
                            id=row['id'],
                            name=row['name'],
                            slug=row['slug']
                        )
                    except IntegrityError as e:
                        self.stdout.write(
                            f'Не удалось добавить категорию: {e}')
            self.stdout.write(self.style.SUCCESS(
                "Категории успешно импортированы"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR
                              ("Файл static/data/category.csv не найден"))
        except Exception as e:
            self.stdout.write(self.style.ERROR
                              (f"Ошибка при импорте категорий: {e}"))

    def import_genres(self):
        """Импорт жанров."""
        self.stdout.write("Импортируем жанры.")
        try:
            with open('static/data/genre.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        Genre.objects.get_or_create(
                            id=row['id'],
                            name=row['name'],
                            slug=row['slug']
                        )
                    except IntegrityError as e:
                        self.stdout.write(
                            f'Не удалось добавить жанр: {e}')
            self.stdout.write(self.style.SUCCESS(
                "Жанры успешно импортированы"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/genre.csv не найден"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при импорте жанров: {e}"))

    def import_titles(self):
        """Импорт произведений."""
        self.stdout.write("Импортируем произведения.")
        try:
            with open('static/data/titles.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category = get_object_or_404(Category, id=row['category'])
                    try:
                        Title.objects.create(
                            id=row['id'],
                            name=row['name'],
                            year=row['year'],
                            category=category
                        )
                    except IntegrityError as e:
                        self.stdout.write(
                            f'Не удалось добавить произведение: {e}')
            self.stdout.write(self.style.SUCCESS(
                "Произведения успешно импортированы."))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/titles.csv не найден."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при импорте произведений: {e}."))

    def import_genre_titles(self):
        """Импорт связей между произведениями и жанрами."""
        self.stdout.write("Импортируем связи между произведениями и жанрами.")
        try:
            with open('static/data/genre_title.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    title = get_object_or_404(Title, id=row['title_id'])
                    genre = get_object_or_404(Genre, id=row['genre_id'])
                    title.genre.add(genre)
            self.stdout.write(self.style.SUCCESS(
                "Связи между произведениями и жанрами успешно импортированы."))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/genre_title.csv не найден."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при импорте связей: {e}."))

    def import_reviews(self):
        """Импорт отзывов."""
        self.stdout.write("Импортируем отзывы.")
        try:
            with open('static/data/review.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    title = get_object_or_404(Title, id=row['title_id'])
                    author = get_object_or_404(User, id=row['author'])
                    try:
                        Review.objects.create(
                            id=row['id'],
                            title=title,
                            author=author,
                            text=row['text'],
                            pub_date=row['pub_date'],
                            score=row['score']
                        )
                    except IntegrityError as e:
                        self.stdout.write(f'Не удалось добавить отзыв: {e}.')
            self.stdout.write(self.style.SUCCESS(
                "Отзывы успешно импортированы."))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/review.csv не найден."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при импорте отзывов: {e}."))

    def import_comments(self):
        """Импорт комментариев."""
        self.stdout.write("Импортируем комментарии.")
        try:
            with open('static/data/comments.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    review = get_object_or_404(Review, id=row['review_id'])
                    author = get_object_or_404(User, id=row['author'])
                    try:
                        Comment.objects.create(
                            id=row['id'],
                            review=review,
                            author=author,
                            text=row['text'],
                            pub_date=row['pub_date']
                        )
                    except IntegrityError as e:
                        self.stdout.write(
                            f'Не удалось добавить комментарии: {e}.')
            self.stdout.write(self.style.SUCCESS(
                "Комментарии успешно импортированы."))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Файл static/data/comments.csv не найден."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при импорте комментариев: {e}."))
