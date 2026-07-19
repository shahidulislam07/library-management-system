"""
django-filter FilterSet definitions used by the API's Filtering,
Searching & Ordering requirements.

Each FilterSet is attached to its ViewSet's `filterset_class` and works
alongside DjangoFilterBackend, e.g.:

    GET /api/books/?category=Programming
    GET /api/books/?author=1&available=true
    GET /api/loans/?is_returned=false&member=3
"""

import django_filters

from .models import Book, Loan, Member, Author


class BookFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(queryset=Author.objects.all())
    category = django_filters.CharFilter(
        field_name='categories__name', lookup_expr='iexact'
    )
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    published_after = django_filters.DateFilter(
        field_name='publication_date', lookup_expr='gte'
    )
    published_before = django_filters.DateFilter(
        field_name='publication_date', lookup_expr='lte'
    )
    available = django_filters.BooleanFilter(
        field_name='available_copies', method='filter_available'
    )

    class Meta:
        model = Book
        fields = ['author', 'category', 'min_price', 'max_price', 'available']

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(available_copies__gt=0)
        return queryset.filter(available_copies=0)


class MemberFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(field_name='is_active')
    joined_after = django_filters.DateFilter(
        field_name='membership_date', lookup_expr='gte'
    )

    class Meta:
        model = Member
        fields = ['is_active', 'joined_after']


class LoanFilter(django_filters.FilterSet):
    is_returned = django_filters.BooleanFilter(field_name='is_returned')
    member = django_filters.NumberFilter(field_name='member_id')
    book = django_filters.NumberFilter(field_name='book_id')
    overdue = django_filters.BooleanFilter(method='filter_overdue')
    due_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_after = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')

    class Meta:
        model = Loan
        fields = ['is_returned', 'member', 'book']

    def filter_overdue(self, queryset, name, value):
        import datetime
        today = datetime.date.today()
        if value:
            return queryset.filter(is_returned=False, due_date__lt=today)
        return queryset.exclude(is_returned=False, due_date__lt=today)
