from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from books.models import Book
from borrowings.models import Borrowing
from tests.base import LibraryFixture


class StageTests(LibraryFixture):
    def test_cannot_delete_book_with_history(self):
        self.make_borrowing()
        self.login(self.admin)
        self.assertEqual(self.client.delete(f"/books/{self.book.pk}/").status_code, 400)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_user_sees_only_own_borrowings_even_with_user_filter(self):
        own = self.make_borrowing()
        foreign = self.make_borrowing(self.other)
        self.login()
        response = self.client.get(f"/borrowings/?user_id={self.other.pk}")
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])
        self.assertEqual(self.client.get(f"/borrowings/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/borrowings/{foreign.pk}/return/").status_code, 404)

    def test_borrowing_update_delete_not_exposed(self):
        borrowing = self.make_borrowing()
        self.login(self.admin)
        self.assertEqual(self.client.patch(f"/borrowings/{borrowing.pk}/", {}).status_code, 405)
        self.assertEqual(self.client.delete(f"/borrowings/{borrowing.pk}/").status_code, 405)

    def test_database_date_constraints(self):
        for field in ("expected_return_date", "actual_return_date"):
            with self.subTest(field=field), self.assertRaises(IntegrityError), transaction.atomic():
                Borrowing.objects.create(
                    user=self.user,
                    book=self.book,
                    **{
                        "expected_return_date": self.due,
                        field: timezone.localdate() - timedelta(days=1),
                    },
                )
