import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404

from reviews.models import Genre, Title


User = get_user_model()


class Command(BaseCommand):
    help = "Импортируем связи между произведениями и жанрами."

    def handle(self, *args, **options):
        with open('static/data/genre_title.csv', mode='r',
                  encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = get_object_or_404(Title, id=row['title_id'])
                genre = get_object_or_404(
                    Genre,
                    id=row['genre_id']
                )
                title.genre.add(genre)
