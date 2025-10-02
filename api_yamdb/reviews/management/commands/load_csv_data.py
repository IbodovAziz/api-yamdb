import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from reviews.models import Category, Genre, Title, GenreTitle


class Command(BaseCommand):
    help = 'Load data from CSV files into the database'

    def handle(self, *args, **options):
        base_path = os.path.join(
            settings.BASE_DIR, 'api_yamdb', 'static', 'data')

        try:
            with open(os.path.join(base_path, 'category.csv'), encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    Category.objects.get_or_create(
                        id=row['id'],
                        name=row['name'],
                        slug=row['slug']
                    )
                self.stdout.write(self.style.SUCCESS(
                    'Successfully loaded categories'))
        except FileNotFoundError:
            raise CommandError('Category CSV file not found')
        except Exception as e:
            raise CommandError(f'Error loading categories: {str(e)}')

        try:
            with open(os.path.join(base_path, 'genre.csv'), encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    Genre.objects.get_or_create(
                        id=row['id'],
                        name=row['name'],
                        slug=row['slug']
                    )
                self.stdout.write(self.style.SUCCESS(
                    'Successfully loaded genres'))
        except FileNotFoundError:
            raise CommandError('Genre CSV file not found')
        except Exception as e:
            raise CommandError(f'Error loading genres: {str(e)}')

        try:
            with open(os.path.join(base_path, 'titles.csv'), encoding='utf-8'
                      ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category = Category.objects.get(id=row['category'])
                    Title.objects.get_or_create(
                        id=row['id'],
                        name=row['name'],
                        year=row['year'],
                        category=category,
                        description=row.get('description', '')
                    )
                self.stdout.write(self.style.SUCCESS(
                    'Successfully loaded titles'))
        except FileNotFoundError:
            raise CommandError('Titles CSV file not found')
        except Exception as e:
            raise CommandError(f'Error loading titles: {str(e)}')

        try:
            with open(os.path.join(base_path, 'genre_title.csv'
                                   ), encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    title = Title.objects.get(id=row['title_id'])
                    genre = Genre.objects.get(id=row['genre_id'])
                    GenreTitle.objects.get_or_create(title=title, genre=genre)
                self.stdout.write(self.style.SUCCESS(
                    'Successfully loaded genre-title relations'))
        except FileNotFoundError:
            raise CommandError('Genre-Title CSV file not found')
        except Exception as e:
            raise CommandError(
                f'Error loading genre-title relations: {str(e)}')

        self.stdout.write(self.style.SUCCESS(
            'Data import completed successfully!'))
