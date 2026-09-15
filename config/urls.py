from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from books.views import BookViewSet

router = DefaultRouter()
router.register("books", BookViewSet)
urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
