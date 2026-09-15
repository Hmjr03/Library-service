from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import ProfileView, RegisterView

urlpatterns = [
    path("", RegisterView.as_view(), name="register"),
    path("me/", ProfileView.as_view(), name="profile"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
