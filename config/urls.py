from django.urls import include, path
from rest_framework.routers import DefaultRouter
from books.views import BookViewSet

router = DefaultRouter()
router.register("books", BookViewSet)
urlpatterns = [path("users/", include("users.urls")), path("", include(router.urls))]
