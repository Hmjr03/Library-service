from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()
PASSWORD = "Library!Practice8392"


class LibraryFixture(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("reader@example.com", PASSWORD)
        self.other = User.objects.create_user("other@example.com", PASSWORD)
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)

    def login(self, user=None):
        self.client.force_authenticate(user or self.user)
