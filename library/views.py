"""
Views for the Library Management API.

Every model is exposed through a ModelViewSet, giving full
Create / List / Retrieve / Update / Partial-Update / Delete support
out of the box. Each ViewSet configures:

    - filterset_class  -> field-based filtering   (?author=1)
    - search_fields     -> free-text search        (?search=python)
    - ordering_fields    -> sortable columns        (?ordering=-price)

Pagination is applied globally via REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'].
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import BookFilter, LoanFilter, MemberFilter
from .models import Author, Book, Category, Loan, Member, UserProfile
from .permissions import IsAdminOrReadOnly
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    CategorySerializer,
    LoanSerializer,
    MemberSerializer,
    UserProfileSerializer,
)


class AuthorViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Authors.

    list:   GET  /api/authors/
    create: POST /api/authors/
    retrieve/update/partial_update/delete: /api/authors/{id}/
    """

    queryset = Author.objects.all().order_by('last_name', 'first_name')
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['first_name', 'last_name', 'email', 'nationality']
    ordering_fields = ['first_name', 'last_name', 'date_of_birth', 'created_at']
    ordering = ['last_name']


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD API for Categories."""

    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Books.

    Supports:
        GET /api/books/?category=Programming
        GET /api/books/?author=1
        GET /api/books/?search=python
        GET /api/books/?ordering=-price
        GET /api/books/?available=true
    """

    queryset = Book.objects.select_related('author').prefetch_related(
        'categories'
    ).all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BookFilter
    search_fields = ['title', 'isbn', 'author__first_name', 'author__last_name', 'description']
    ordering_fields = ['title', 'price', 'publication_date', 'available_copies', 'created_at']
    ordering = ['title']


class MemberViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Members.

    Supports:
        GET /api/members/?is_active=true
        GET /api/members/?search=Rahim
        GET /api/members/?ordering=-membership_date
    """

    queryset = Member.objects.prefetch_related('loans__book').all()
    serializer_class = MemberSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = MemberFilter
    search_fields = ['full_name', 'email', 'phone_number']
    ordering_fields = ['full_name', 'membership_date']
    ordering = ['full_name']


class LoanViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Loans (borrow transactions).

    Supports:
        GET /api/loans/?is_returned=false
        GET /api/loans/?member=3
        GET /api/loans/?overdue=true
        GET /api/loans/?ordering=-due_date

    Custom action:
        POST /api/loans/{id}/return_book/  -> marks a loan as returned
        and restocks the book automatically.
    """

    queryset = Loan.objects.select_related('book', 'member').all()
    serializer_class = LoanSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = LoanFilter
    search_fields = ['book__title', 'member__full_name']
    ordering_fields = ['loan_date', 'due_date', 'return_date', 'fine_amount']
    ordering = ['-loan_date']

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """Mark a loan as returned and automatically restock the book."""
        import datetime

        loan = self.get_object()
        if loan.is_returned:
            return Response(
                {'detail': 'This loan has already been marked as returned.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loan.is_returned = True
        loan.return_date = datetime.date.today()
        if loan.is_overdue:
            overdue_days = (loan.return_date - loan.due_date).days
            loan.fine_amount = max(0, overdue_days) * 5
        loan.full_clean()
        loan.save()

        book = loan.book
        book.available_copies = min(book.total_copies, book.available_copies + 1)
        book.save(update_fields=['available_copies'])

        serializer = self.get_serializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD API for UserProfiles (extended User information).

    Supports:
        GET /api/profiles/?search=librarian
        GET /api/profiles/?ordering=user__username
    """

    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['user__username', 'user__email', 'membership_number']
    ordering_fields = ['membership_number', 'created_at']
    ordering = ['user__username']
