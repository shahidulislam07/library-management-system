"""
library_management URL Configuration.

The Django Admin is mounted at /admin/ and the entire REST API is
mounted at /api/ and delegated to the `library` app's own urls.py,
which wires up a DRF router with every model's ViewSet.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('library.urls')),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
