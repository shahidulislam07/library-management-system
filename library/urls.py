"""
URL routing for the library app's REST API, using a DRF DefaultRouter
so every ViewSet automatically gets list/create/retrieve/update/
partial_update/delete routes, plus the browsable API root.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    AuthorViewSet,
    BookViewSet,
    CategoryViewSet,
    LoanViewSet,
    MemberViewSet,
    UserProfileViewSet,
)

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'books', BookViewSet, basename='book')
router.register(r'members', MemberViewSet, basename='member')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')

urlpatterns = router.urls
