"""
Custom pagination classes for the Library Management API.

StandardResultsSetPagination is applied globally (see REST_FRAMEWORK
settings) so that every list endpoint returns the required
count / next / previous / results envelope, and clients can override
the page size per-request with ?page_size=.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
