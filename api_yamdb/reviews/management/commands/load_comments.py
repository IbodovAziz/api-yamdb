import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reviews.models import Comment


User = get_user_model()


class Command(BaseCommand):
    help = "Импортируем комментарии."

    def handle(self, *args, **options):
        comments_to_create = []
        with open('static/data/comments.csv', mode='r',
                  encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                comments_to_create.append(
                    Comment(
                        id=row['id'],
                        review_id=row['review_id'],
                        author_id=row['user_id'],
                        text=row['text'],
                        pub_date=row['pub_date']
                    )
                )
        Comment.objects.bulk_create(comments_to_create)
        self.stdout.write(
            f'Импортировано {len(comments_to_create)} комментариев.')
