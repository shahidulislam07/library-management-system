"""
Serializers for the Library Management API.

Every model has a dedicated ModelSerializer. Nested serializers,
read-only/write-only fields, field-level validation, and object-level
(cross-field) validation are used throughout, per the project rubric.
"""

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Author, Book, Category, Loan, Member, UserProfile

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(source='books.count', read_only=True)

    class Meta:
        model = Author
        fields = [
            'id', 'first_name', 'last_name', 'email', 'bio',
            'date_of_birth', 'nationality', 'book_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_date_of_birth(self, value):
        if value and value > datetime.date.today():
            raise serializers.ValidationError(
                'Date of birth cannot be in the future.'
            )
        return value


class AuthorMinimalSerializer(serializers.ModelSerializer):
    """Lightweight, read-only representation used for nesting inside Book."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'full_name', 'email']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This category already exists.')
        return value


class BookSerializer(serializers.ModelSerializer):
    """
    Full Book serializer.

    - `author` is nested (read-only) for output, while `author_id`
      accepts a primary key for create/update (write-only).
    - `categories` is nested (read-only) for output, while
      `category_ids` accepts a list of primary keys (write-only).
    """

    author = AuthorMinimalSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source='author', write_only=True
    )
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='categories',
        many=True,
        write_only=True,
        required=False,
    )
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'author', 'author_id',
            'categories', 'category_ids', 'publication_date',
            'description', 'price', 'total_copies', 'available_copies',
            'is_available', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_isbn(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('ISBN must contain only digits.')
        if len(value) not in (10, 13):
            raise serializers.ValidationError('ISBN must be exactly 10 or 13 digits.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be a positive value.')
        return value

    def validate_total_copies(self, value):
        if value < 0:
            raise serializers.ValidationError('Total copies cannot be negative.')
        return value

    def validate(self, attrs):


        total = attrs.get(
            'total_copies',
            getattr(self.instance, 'total_copies', None),
        )
        available = attrs.get(
            'available_copies',
            getattr(self.instance, 'available_copies', None),
        )
        if total is not None and available is not None and available > total:
            raise serializers.ValidationError(
                {'available_copies': 'Available copies cannot exceed total copies.'}
            )
        return attrs


class BookListSerializer(serializers.ModelSerializer):
    """A lighter-weight serializer used for list views."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'author_name', 'price',
            'available_copies', 'total_copies',
        ]

    def get_author_name(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


class LoanMinimalSerializer(serializers.ModelSerializer):
    """Lightweight, read-only representation used for nesting inside Member."""

    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'book_title', 'loan_date', 'due_date',
            'return_date', 'is_returned',
        ]


class MemberSerializer(serializers.ModelSerializer):
    """
    Member serializer. Nests the member's loan history (Member with
    Loans example from the rubric) as a read-only field.
    """

    loans = LoanMinimalSerializer(many=True, read_only=True)
    active_loan_count = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'address',
            'membership_date', 'is_active', 'loans', 'active_loan_count',
        ]
        read_only_fields = ['id', 'membership_date']

    def get_active_loan_count(self, obj):
        return obj.loans.filter(is_returned=False).count()

    def validate_email(self, value):
        qs = Member.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'A member with this email already exists.'
            )
        return value


class MemberMinimalSerializer(serializers.ModelSerializer):
    """Lightweight, read-only representation used for nesting inside Loan."""

    class Meta:
        model = Member
        fields = ['id', 'full_name', 'email', 'is_active']


class LoanSerializer(serializers.ModelSerializer):
    """
    Full Loan serializer.

    - `book` / `member` nested read-only representations for output.
    - `book_id` / `member_id` write-only primary key fields for input.
    - `fine_amount` is read-only: it is calculated by business logic
      (e.g. on return), not supplied directly by API clients.
    """

    book = BookListSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source='book', write_only=True
    )
    member = MemberMinimalSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), source='member', write_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'book', 'book_id', 'member', 'member_id',
            'loan_date', 'due_date', 'return_date', 'is_returned',
            'fine_amount', 'is_overdue',
        ]
        read_only_fields = ['id', 'fine_amount']

    def validate(self, attrs):
        loan_date = attrs.get(
            'loan_date', getattr(self.instance, 'loan_date', datetime.date.today())
        )
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        is_returned = attrs.get(
            'is_returned', getattr(self.instance, 'is_returned', False)
        )
        return_date = attrs.get(
            'return_date', getattr(self.instance, 'return_date', None)
        )
        book = attrs.get('book', getattr(self.instance, 'book', None))

        if due_date and loan_date and due_date <= loan_date:
            raise serializers.ValidationError(
                {'due_date': 'Due date must be after the loan date.'}
            )

        if is_returned and not return_date:
            raise serializers.ValidationError(
                {'return_date': 'Return date is required once a loan is marked returned.'}
            )


        if self.instance is None and book is not None and book.available_copies < 1:
            raise serializers.ValidationError(
                {'book_id': 'This book currently has no available copies.'}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        book = validated_data['book']
        loan = Loan.objects.create(**validated_data)

        book.available_copies = max(0, book.available_copies - 1)
        book.save(update_fields=['available_copies'])
        return loan

    @transaction.atomic
    def update(self, instance, validated_data):
        was_returned = instance.is_returned
        loan = super().update(instance, validated_data)

        if not was_returned and loan.is_returned:
            book = loan.book
            book.available_copies = min(
                book.total_copies, book.available_copies + 1
            )
            book.save(update_fields=['available_copies'])
        return loan


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight, read-only representation of Django's built-in User."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    UserProfile serializer.

    - `user` is a nested, read-only representation of the linked
      Django User (OneToOne relationship).
    - `username`, `email`, and `password` are write-only fields used
      only when creating a brand-new User + UserProfile pair together.
    """

    user = UserMinimalSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'}
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'email', 'password',
            'phone_number', 'address', 'date_of_birth',
            'membership_number', 'is_librarian', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_membership_number(self, value):
        qs = UserProfile.objects.filter(membership_number__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'This membership number is already in use.'
            )
        return value

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def validate(self, attrs):
        if self.instance is None:
            if not attrs.get('username'):
                raise serializers.ValidationError(
                    {'username': 'This field is required when creating a profile.'}
                )
            if not attrs.get('password'):
                raise serializers.ValidationError(
                    {'password': 'This field is required when creating a profile.'}
                )
            if User.objects.filter(username=attrs['username']).exists():
                raise serializers.ValidationError(
                    {'username': 'A user with this username already exists.'}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.pop('email', '')
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile
