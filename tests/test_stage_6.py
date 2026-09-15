from django.utils import timezone

from borrowings.models import Borrowing
from tests.base import LibraryFixture


class StageTests(LibraryFixture):
    def test_admin_all_and_user_filter(self):
        own = self.make_borrowing()
        self.make_borrowing(self.other)
        self.login(self.admin)
        self.assertEqual(self.client.get("/borrowings/").data["count"], 2)
        response = self.client.get(f"/borrowings/?user_id={self.user.pk}")
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])

    def test_active_filters(self):
        active = self.make_borrowing()
        returned = self.make_borrowing()
        Borrowing.objects.filter(pk=returned.pk).update(actual_return_date=timezone.localdate())
        self.login()
        self.assertEqual(
            self.client.get("/borrowings/?is_active=true").data["results"][0]["id"], active.pk
        )
        self.assertEqual(
            self.client.get("/borrowings/?is_active=false").data["results"][0]["id"], returned.pk
        )

    def test_invalid_filters(self):
        self.login(self.admin)
        for query in ("is_active=maybe", "user_id=abc", "user_id=-1"):
            self.assertEqual(self.client.get("/borrowings/?" + query).status_code, 400)
