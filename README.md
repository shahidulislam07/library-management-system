# Library Management System — Django REST Framework

A complete backend REST API for managing a library's authors, categories,
books, members, loans, and staff profiles — built with Django and Django
REST Framework as a final course project.

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Features](#features)
3. [Technologies Used](#technologies-used)
4. [Project Structure](#project-structure)
5. [Installation Steps](#installation-steps)
6. [Database Migration Commands](#database-migration-commands)
7. [Running the Project](#running-the-project)
8. [API Endpoint List](#api-endpoint-list)
9. [Sample API Requests & Responses](#sample-api-requests--responses)
10. [Filtering, Searching & Ordering](#filtering-searching--ordering)
11. [Django Admin](#django-admin)
12. [Running Tests / Manual Testing](#running-tests--manual-testing)

---

## Problem Statement

Libraries need a reliable way to track their catalogue of books, the
authors and categories those books belong to, their registered members,
and every borrowing (loan) transaction — including due dates, return
dates, and overdue fines. This project implements a RESTful backend
that a front-end (web or mobile) or a librarian using Django Admin can
use to manage all of this data safely, with proper validation, search,
filtering, and pagination.

## Features

- Full CRUD REST API for **Authors**, **Categories**, **Books**,
  **Members**, **Loans**, and **User Profiles**.
- Relational data model with **ForeignKey**, **ManyToMany**, and
  **OneToOne** relationships.
- Model-level (`clean()`), field-level, and serializer-level (cross-field)
  validation, including business rules such as:
  - Available copies of a book can never exceed total copies.
  - A book with zero available copies cannot be loaned out.
  - A loan's due date must be after its loan date.
  - Returning a loan automatically restocks the book and calculates an
    overdue fine.
- Nested, read-only representations (e.g. a Book's Author and
  Categories; a Member's Loan history) alongside write-only ID fields
  for creating/updating relationships.
- Filtering, searching, and ordering on every list endpoint via
  `django-filter` and DRF's `SearchFilter` / `OrderingFilter`.
- Global pagination (`count` / `next` / `previous` / `results`).
- A fully customized Django Admin panel (list display, search, filters,
  ordering, read-only fields, `filter_horizontal`, and inline models).
- A custom `return_book` action on the Loan endpoint for one-step
  book returns.

## Technologies Used

- **Python 3.11+**
- **Django 5.x**
- **Django REST Framework 3.15**
- **django-filter** for advanced filtering
- **SQLite** as the database

## Project Structure

```
library_management_system/
├── manage.py
├── requirements.txt
├── README.md
├── postman_collection.json
├── library_management/          # Project configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── library/                     # Main application
    ├── __init__.py
    ├── apps.py
    ├── models.py                # Author, Category, Book, Member, Loan, UserProfile
    ├── serializers.py           # ModelSerializers with nested/validated fields
    ├── views.py                 # ModelViewSets
    ├── urls.py                  # DRF router
    ├── filters.py                # django-filter FilterSets
    ├── pagination.py             # Custom pagination class
    ├── permissions.py            # Custom permission classes
    ├── admin.py                  # Django Admin customization
    └── migrations/
        └── __init__.py
```

## Installation Steps

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd library_management_system

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> If starting a brand-new project from scratch instead of cloning, the
> scaffolding was originally generated with:
> ```bash
> pip install django djangorestframework django-filter
> django-admin startproject library_management .
> python manage.py startapp library
> ```

## Database Migration Commands

```bash
python manage.py makemigrations
python manage.py migrate
```

## Running the Project

```bash
# Create an admin/superuser account for Django Admin access
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

- API root: **http://127.0.0.1:8000/api/**
- Django Admin: **http://127.0.0.1:8000/admin/**
- Browsable API login: **http://127.0.0.1:8000/api-auth/login/**

## API Endpoint List

All endpoints are prefixed with `/api/`.

| Resource       | Endpoint                              | Methods                          |
|----------------|----------------------------------------|-----------------------------------|
| Authors        | `/api/authors/`                        | GET, POST                         |
|                | `/api/authors/{id}/`                   | GET, PUT, PATCH, DELETE            |
| Categories     | `/api/categories/`                     | GET, POST                         |
|                | `/api/categories/{id}/`                | GET, PUT, PATCH, DELETE            |
| Books          | `/api/books/`                          | GET, POST                         |
|                | `/api/books/{id}/`                     | GET, PUT, PATCH, DELETE            |
| Members        | `/api/members/`                        | GET, POST                         |
|                | `/api/members/{id}/`                   | GET, PUT, PATCH, DELETE            |
| Loans          | `/api/loans/`                          | GET, POST                         |
|                | `/api/loans/{id}/`                     | GET, PUT, PATCH, DELETE            |
|                | `/api/loans/{id}/return_book/`         | POST (custom action)              |
| User Profiles  | `/api/profiles/`                       | GET, POST                         |
|                | `/api/profiles/{id}/`                  | GET, PUT, PATCH, DELETE            |

## Sample API Requests & Responses

### Create an Author

`POST /api/authors/`

```json
{
  "first_name": "George",
  "last_name": "Orwell",
  "email": "orwell@example.com",
  "bio": "English novelist and essayist.",
  "date_of_birth": "1903-06-25",
  "nationality": "British"
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "first_name": "George",
  "last_name": "Orwell",
  "email": "orwell@example.com",
  "bio": "English novelist and essayist.",
  "date_of_birth": "1903-06-25",
  "nationality": "British",
  "book_count": 0,
  "created_at": "2026-07-19T10:00:00Z"
}
```

### Create a Book (nested categories, FK author)

`POST /api/books/`

```json
{
  "title": "1984",
  "isbn": "9780451524935",
  "author_id": 1,
  "category_ids": [1, 2],
  "publication_date": "1949-06-08",
  "description": "Dystopian social science fiction novel.",
  "price": "9.99",
  "total_copies": 5,
  "available_copies": 5
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "title": "1984",
  "isbn": "9780451524935",
  "author": {"id": 1, "full_name": "George Orwell", "email": "orwell@example.com"},
  "categories": [
    {"id": 1, "name": "Fiction", "description": ""},
    {"id": 2, "name": "Classics", "description": ""}
  ],
  "publication_date": "1949-06-08",
  "description": "Dystopian social science fiction novel.",
  "price": "9.99",
  "total_copies": 5,
  "available_copies": 5,
  "is_available": true,
  "created_at": "2026-07-19T10:05:00Z",
  "updated_at": "2026-07-19T10:05:00Z"
}
```

### Validation Error Example

`POST /api/books/` with an invalid ISBN:

```json
{
  "isbn": [
    "ISBN must be exactly 10 or 13 digits."
  ]
}
```

### List Books (paginated)

`GET /api/books/?page=1`

```json
{
  "count": 30,
  "next": "http://127.0.0.1:8000/api/books/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "title": "1984", "isbn": "9780451524935", "...": "..." }
  ]
}
```

### Create a Loan (borrow a book)

`POST /api/loans/`

```json
{
  "book_id": 1,
  "member_id": 1,
  "due_date": "2026-08-02"
}
```

**Response `201 Created`** — the book's `available_copies` is
automatically decremented by 1.

### Return a Loan

`POST /api/loans/1/return_book/`

Marks the loan as returned, sets `return_date` to today, calculates a
fine if overdue, and restocks the book automatically.

## Filtering, Searching & Ordering

```
GET /api/books/?category=Fiction
GET /api/books/?author=1&available=true
GET /api/books/?min_price=5&max_price=20
GET /api/books/?search=orwell
GET /api/books/?ordering=-price

GET /api/members/?is_active=true
GET /api/members/?search=Rahim

GET /api/loans/?is_returned=false
GET /api/loans/?overdue=true
GET /api/loans/?member=1
GET /api/loans/?ordering=-due_date
```

## Django Admin

Navigate to `/admin/` and log in with a superuser account
(`python manage.py createsuperuser`). All six models are registered
with:

- `list_display`, `search_fields`, `list_filter`, `ordering`
- `readonly_fields` for auto-managed fields (timestamps, membership date)
- `filter_horizontal` for the Book ↔ Category ManyToMany widget
- Inline `Loan` records shown directly on the Book and Member admin pages

## Running Tests / Manual Testing

Every endpoint can be exercised directly from:

- The **DRF Browsable API** (just open any `/api/...` URL in a browser)
- **Postman**, using the included `postman_collection.json` (import it
  into Postman and set the `base_url` collection variable to
  `http://127.0.0.1:8000/api`)
- **Insomnia**, by importing the same collection (Postman v2.1 format
  is supported by Insomnia's import feature)

Demonstrate full CRUD for each resource: create a record, list it,
retrieve it by ID, update it (PUT), partially update it (PATCH), then
delete it — and confirm the correct HTTP status code is returned at
each step (`201`, `200`, `200`, `200`, `204`).
