"""
Database models for the Library Management System.

Models implemented (6 total, exceeding the minimum of 4):
    1. Author        - writers of books
    2. Category       - book genres/categories
    3. Book           - the core catalogue item
    4. Member         - library members who borrow books
    5. Loan           - a borrowing transaction linking Member <-> Book
    6. UserProfile    - extends Django's built-in User (OneToOne)

Relationships demonstrated:
    - ForeignKey:     Book -> Author, Loan -> Book, Loan -> Member
    - ManyToMany:      Book <-> Category
    - OneToOne:       UserProfile -> User
"""

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone


class Author(models.Model):
    """Represents a book author."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def clean(self):

        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(
                {'date_of_birth': 'Date of birth cannot be in the future.'}
            )


class Category(models.Model):
    """Represents a book category/genre, e.g. Fiction, Programming."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Book(models.Model):
    """Represents a book in the library catalogue."""

    isbn_validator = RegexValidator(
        regex=r'^\d{10}(\d{3})?$',
        message='ISBN must be exactly 10 or 13 digits.',
    )

    title = models.CharField(max_length=255)
    isbn = models.CharField(
        max_length=13,
        unique=True,
        validators=[isbn_validator],
        help_text='10 or 13 digit ISBN number (numbers only).',
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='books',
    )
    categories = models.ManyToManyField(
        Category,
        related_name='books',
        blank=True,
    )
    publication_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    total_copies = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=1,
    )
    available_copies = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=1,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def __str__(self):
        return f'{self.title} ({self.isbn})'

    def clean(self):

        if self.available_copies > self.total_copies:
            raise ValidationError(
                {
                    'available_copies': (
                        'Available copies cannot exceed total copies.'
                    )
                }
            )
        if len(self.isbn) not in (10, 13):
            raise ValidationError({'isbn': 'ISBN must be 10 or 13 digits.'})

    @property
    def is_available(self):
        return self.available_copies > 0


class Member(models.Model):
    """Represents a library member who can borrow books."""

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?\d{7,15}$',
        message="Phone number must be entered in the format: '+999999999'.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True
    )
    address = models.TextField(blank=True)
    membership_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'

    def __str__(self):
        return self.full_name


class Loan(models.Model):
    """Represents a single borrowing transaction of a Book by a Member."""

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    loan_date = models.DateField(default=datetime.date.today)
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    is_returned = models.BooleanField(default=False)
    fine_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ['-loan_date']
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'


        unique_together = ('book', 'member', 'loan_date')

    def __str__(self):
        return f'{self.member.full_name} -> {self.book.title}'

    def clean(self):

        if self.due_date and self.loan_date and self.due_date <= self.loan_date:
            raise ValidationError(
                {'due_date': 'Due date must be after the loan date.'}
            )


        if self.is_returned and not self.return_date:
            raise ValidationError(
                {'return_date': 'Return date is required once a loan is marked returned.'}
            )


        if self.book_id and not self.is_returned and self.pk is None:
            if self.book.available_copies < 1:
                raise ValidationError(
                    {'book': 'This book has no available copies to lend.'}
                )

    @property
    def is_overdue(self):
        if self.is_returned:
            return False
        return timezone.now().date() > self.due_date


class UserProfile(models.Model):
    """
    Extends the built-in Django User model with library-specific
    information. Demonstrates a OneToOne relationship.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='library_profile',
    )
    phone_regex = RegexValidator(
        regex=r'^\+?\d{7,15}$',
        message="Phone number must be entered in the format: '+999999999'.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True
    )
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    membership_number = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique library membership number, e.g. LIB-0001.',
    )
    is_librarian = models.BooleanField(
        default=False,
        help_text='Designates whether this user is library staff.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'Profile of {self.user.username}'

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(
                {'date_of_birth': 'Date of birth cannot be in the future.'}
            )
