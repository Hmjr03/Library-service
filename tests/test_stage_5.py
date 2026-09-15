from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from borrowings.models import Borrowing
from borrowings.services import create_borrowing
from tests.base import LibraryFixture


class StageTests(LibraryFixture):
    def test_create_assigns_current_user_date_and_decreases_inventory(self):
        self.login()
        response = self.borrow(
            user=self.other.pk, actual_return_date="2020-01-01", borrow_date="2020-01-01"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.user.pk)
        self.assertEqual(response.data["borrow_date"], str(timezone.localdate()))
        self.assertIsNone(response.data["actual_return_date"])
        self.assertEqual(response.data["book"]["title"], self.book.title)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

    def test_no_stock_returns_400_without_creating_borrowing(self):
        self.book.inventory = 0
        self.book.save()
        self.login()
        self.assertEqual(self.borrow().status_code, 400)
        self.assertEqual(Borrowing.objects.count(), 0)

    def test_past_date_rejected_today_allowed(self):
        self.login()
        self.assertEqual(
            self.borrow(
                expected_return_date=str(timezone.localdate() - timedelta(days=1))
            ).status_code,
            400,
        )
        self.assertEqual(
            self.borrow(expected_return_date=str(timezone.localdate())).status_code, 201
        )

    def test_invalid_book_rejected(self):
        self.login()
        self.assertEqual(self.borrow(book=999999).status_code, 400)

    def test_create_rollback_if_record_creation_fails(self):
        with patch(
            "borrowings.services.Borrowing.objects.create",
            side_effect=RuntimeError("database failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.make_borrowing()
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_service_rejects_past_date(self):
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            create_borrowing(
                user=self.user,
                book=self.book,
                expected_return_date=timezone.localdate() - timedelta(days=1),
            )

    def test_anonymous_borrowings_and_profile_denied(self):
        borrowing = self.make_borrowing()
        for url in ("/users/me/", "/borrowings/", f"/borrowings/{borrowing.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.borrow().status_code, 401)
