from django.utils import timezone
from rest_framework import serializers

from reviews.models import Category, Genre, Title


MIN_YEAR = -3000
MAX_YEAR = timezone.now().year


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year',
            'description', 'genre', 'category'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = ('name', 'year', 'description', 'genre', 'category')

    def validate_year(self, value):
        if value < MIN_YEAR:
            raise serializers.ValidationError(
                f'Год не может быть меньше {MIN_YEAR} до н.э.'
            )
        if value > MAX_YEAR:
            raise serializers.ValidationError(
                f'Год выпуска не должен превышать {MAX_YEAR}.'
            )
        return value

    def to_representation(self, instance):
        return TitleReadSerializer(instance).data
