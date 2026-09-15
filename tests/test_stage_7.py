from django.utils import timezone

from borrowings.models import Borrowing
from borrowings.services import return_borrowing
from tests.base import LibraryFixture


class StageTests(LibraryFixture):
    def test_return_once_restores_one_copy(self):
        borrowing = self.make_borrowing()
        self.login()
        url = f"/borrowings/{borrowing.pk}/return/"
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.book.refresh_from_db()
        borrowing.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)
        self.assertEqual(borrowing.actual_return_date, timezone.localdate())

    def test_staff_can_return_other_users_borrowing(self):
        borrowing = self.make_borrowing(self.other)
        self.login(self.admin)
        self.assertEqual(self.client.post(f"/borrowings/{borrowing.pk}/return/").status_code, 200)

    def test_stale_return_object_cannot_increment_twice(self):
        borrowing = self.make_borrowing()
        stale = Borrowing.objects.get(pk=borrowing.pk)
        return_borrowing(borrowing)
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            return_borrowing(stale)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_return_requires_auth_and_ownership(self):
        borrowing = self.make_borrowing(self.other)
        url = f"/borrowings/{borrowing.pk}/return/"
        self.assertEqual(self.client.post(url).status_code, 401)
        self.login()
        self.assertEqual(self.client.post(url).status_code, 404)
