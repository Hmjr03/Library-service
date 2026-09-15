from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from books.models import Book

User = get_user_model()
PASSWORD = "Library!Practice8392"


class LibraryFixture(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("reader@example.com", PASSWORD)
        self.other = User.objects.create_user("other@example.com", PASSWORD)
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)
        self.book = Book.objects.create(
            title="Clean Code",
            author="Robert Martin",
            cover="SOFT",
            inventory=2,
            daily_fee=Decimal("1.50"),
        )
        self.due = timezone.localdate() + timedelta(days=7)

    def login(self, user=None):
        self.client.force_authenticate(user or self.user)
