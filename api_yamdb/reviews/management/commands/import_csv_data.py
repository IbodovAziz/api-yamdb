import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

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

    def import_model(self, filename, Model, process_row_callback=None,
                     use_bulk_create=False):
        """Общий метод для импорта моделей из CSV файлов."""
        model_name = Model._meta.verbose_name_plural
        self.stdout.write(f'Импортируем {model_name}.')
        try:
            with open(filename, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                if use_bulk_create:
                    self._bulk_create_objects(
                        reader, Model, process_row_callback)
                else:
                    self._single_create_objects(
                        reader, Model, process_row_callback, model_name)
                self.stdout.write(self.style.SUCCESS(
                    f'{model_name.capitalize()} успешно импортированы.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Файл {filename} не найден.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при импорте {model_name}: {e}.'))

    def _bulk_create_objects(self, reader, Model, process_row_callback):
        """Обрабатывает массовое создание объектов."""
        objects_to_create = []
        for row in reader:
            if process_row_callback:
                obj = process_row_callback(row, Model)
            else:
                obj = Model(**row)
            objects_to_create.append(obj)
        Model.objects.bulk_create(objects_to_create)

    def _single_create_objects(self, reader, Model, process_row_callback,
                               model_name):
        """Обрабатывает построчное создание объектов."""
        for row in reader:
            try:
                if process_row_callback:
                    process_row_callback(row, Model)
                else:
                    Model.objects.get_or_create(**row)
            except IntegrityError as e:
                self.stdout.write(
                    f'Не удалось добавить {model_name[:-1]}: {e}')

    @transaction.atomic
    def import_users(self):
        """Импорт пользователей с обработкой пароля."""
        def process_user_row(row, Model):
            user = User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                role=row['role'],
                bio=row['bio'],
                first_name=row['first_name'],
                last_name=row['last_name'],
            )
            user.set_password('temporary_password_123')
            return user
        self.import_model(
            'static/data/users.csv',
            User,
            process_row_callback=process_user_row,
            use_bulk_create=True
        )

    @transaction.atomic
    def import_categories(self):
        """Импорт категорий."""
        def process_category_row(row, Model):
            return Category.objects.get_or_create(
                id=row['id'],
                name=row['name'],
                slug=row['slug']
            )
        self.import_model(
            'static/data/category.csv',
            Category,
            process_row_callback=process_category_row
        )

    @transaction.atomic
    def import_genres(self):
        """Импорт жанров."""
        def process_genre_row(row, Model):
            return Genre.objects.get_or_create(
                id=row['id'],
                name=row['name'],
                slug=row['slug']
            )
        self.import_model(
            'static/data/genre.csv',
            Genre,
            process_row_callback=process_genre_row
        )

    @transaction.atomic
    def import_titles(self):
        """Импорт произведений."""
        def process_title_row(row, Model):
            try:
                category = Category.objects.get(id=row['category'])
                return Title.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'year': row['year'],
                        'category': category
                    }
                )
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Категория с id {row["category"]} не найдена'
                ))
                return None, False
        self.import_model(
            'static/data/titles.csv',
            Title,
            process_row_callback=process_title_row
        )

    @transaction.atomic
    def import_genre_titles(self):
        """Импорт связей между произведениями и жанрами."""
        self.stdout.write('Импортируем связи между произведениями и жанрами.')
        try:
            with open('static/data/genre_title.csv', mode='r', encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        title = Title.objects.get(id=row['title_id'])
                        genre = Genre.objects.get(id=row['genre_id'])
                        title.genre.add(genre)
                    except Title.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f'Произведение с ID {row["title_id"]} не найдено'
                        ))
                    except Genre.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f'Жанр с ID {row["genre_id"]} не найден'
                        ))
            self.stdout.write(self.style.SUCCESS(
                'Связи между произведениями и жанрами успешно импортированы.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Файл static/data/genre_title.csv не найден.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при импорте связей: {e}.'))

    @transaction.atomic
    def import_reviews(self):
        """Импорт отзывов."""
        def process_review_row(row, Model):
            try:
                title = Title.objects.get(id=row['title_id'])
                author = User.objects.get(id=row['author'])
                return Review.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'title': title,
                        'author': author,
                        'text': row['text'],
                        'pub_date': row['pub_date'],
                        'score': row['score']
                    }
                )
            except Title.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Произведение с ID {row["title_id"]} не найдено'
                ))
                return None, False
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Пользователь с ID {row["author"]} не найден'
                ))
                return None, False
        self.import_model(
            'static/data/review.csv',
            Review,
            process_row_callback=process_review_row
        )

    @transaction.atomic
    def import_comments(self):
        """Импорт комментариев."""
        def process_comment_row(row, Model):
            try:
                review = Review.objects.get(id=row['review_id'])
                author = User.objects.get(id=row['author'])
                return Comment.objects.get_or_create(
                    id=row['id'],
                    defaults={
                        'review': review,
                        'author': author,
                        'text': row['text'],
                        'pub_date': row['pub_date']
                    }
                )
            except Review.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Отзыв с ID {row["review_id"]} не найден'
                ))
                return None, False
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Пользователь с ID {row["author"]} не найден'
                ))
                return None, False
        self.import_model(
            'static/data/comments.csv',
            Comment,
            process_row_callback=process_comment_row
        )
