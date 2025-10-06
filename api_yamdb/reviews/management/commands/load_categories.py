import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from reviews.models import Category


User = get_user_model()


class Command(BaseCommand):
    help = "Импортируем категории."

    def handle(self, *args, **options):
        with open('static/data/category.csv', mode='r',
                  encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    Category.objects.get_or_create(
                        id=row['id'],
                        name=row['name'],
                        slug=row['slug']
                    )
                except IntegrityError as e:
                    self.stdout.write(f'Не удалось добавить категорию: {e}')
