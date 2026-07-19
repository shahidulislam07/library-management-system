"""
Django Admin configuration for the Library Management System.

Every model is registered with customized ModelAdmin classes using
list_display, search_fields, list_filter, ordering, readonly_fields,
filter_horizontal (for the Book <-> Category ManyToMany), and inline
models (Loans shown inline on both Book and Member admin pages).
"""

from django.contrib import admin

from .models import Author, Book, Category, Loan, Member, UserProfile


class LoanInline(admin.TabularInline):
    """Displays a Book's or Member's loan history inline."""

    model = Loan
    extra = 0
    fields = ('member', 'book', 'loan_date', 'due_date', 'return_date', 'is_returned', 'fine_amount')
    readonly_fields = ('loan_date',)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'nationality', 'date_of_birth', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'nationality')
    list_filter = ('nationality',)
    ordering = ('last_name', 'first_name')
    readonly_fields = ('created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'isbn', 'author', 'price', 'total_copies',
        'available_copies', 'is_available', 'created_at',
    )
    search_fields = ('title', 'isbn', 'author__first_name', 'author__last_name')
    list_filter = ('categories', 'author', 'publication_date')
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('categories',)
    inlines = [LoanInline]
    autocomplete_fields = ('author',)

    @admin.display(boolean=True, description='Available')
    def is_available(self, obj):
        return obj.available_copies > 0


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'is_active', 'membership_date')
    search_fields = ('full_name', 'email', 'phone_number')
    list_filter = ('is_active', 'membership_date')
    ordering = ('full_name',)
    readonly_fields = ('membership_date',)
    inlines = [LoanInline]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'book', 'loan_date', 'due_date',
        'return_date', 'is_returned', 'fine_amount', 'is_overdue',
    )
    search_fields = ('member__full_name', 'book__title')
    list_filter = ('is_returned', 'loan_date', 'due_date')
    ordering = ('-loan_date',)
    readonly_fields = ('loan_date',)
    autocomplete_fields = ('book', 'member')

    @admin.display(boolean=True, description='Overdue')
    def is_overdue(self, obj):
        return obj.is_overdue


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_number', 'phone_number', 'is_librarian', 'created_at')
    search_fields = ('user__username', 'user__email', 'membership_number')
    list_filter = ('is_librarian',)
    ordering = ('user__username',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)
