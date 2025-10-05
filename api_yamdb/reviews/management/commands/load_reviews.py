import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404

from reviews.models import Review, Title


User = get_user_model()


class Command(BaseCommand):
    help = "Импортируем отзывы."

    def handle(self, *args, **options):
        with open('static/data/review.csv', mode='r',
                  encoding='utf-8') as file:
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
                    self.stdout.write(f'Не удалось добавить отзыв: {e}')
