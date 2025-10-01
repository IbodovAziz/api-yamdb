import django_filters
from django.contrib.auth import get_user_model

from reviews.models import Title


User = get_user_model()


class TitleFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name='category__slug'
    )
    genre = django_filters.CharFilter(
        field_name='genre__slug'
    )
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )
    year = django_filters.NumberFilter(
        field_name='year'
    )

    class Meta:
        model = Title
        fields = ['category', 'genre', 'name', 'year']


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    role = django_filters.ChoiceFilter(choices=User.Role.choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'role']
