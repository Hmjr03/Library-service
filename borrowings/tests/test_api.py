from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.services import create_borrowing, return_borrowing

User = get_user_model()
PASSWORD = "Library!Practice8392"


class LibraryAPITests(APITestCase):
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

    def borrow(self, **extra):
        return self.client.post(
            "/borrowings/", {"book": self.book.pk, "expected_return_date": str(self.due), **extra}
        )

    def make_borrowing(self, user=None):
        return create_borrowing(
            user=user or self.user, book=self.book, expected_return_date=self.due
        )

    def test_public_can_list_and_retrieve_books(self):
        self.assertEqual(self.client.get("/books/").status_code, 200)
        self.assertEqual(self.client.get(f"/books/{self.book.pk}/").data["title"], self.book.title)

    def test_anonymous_cannot_write_books(self):
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            url = "/books/" if method == self.client.post else f"/books/{self.book.pk}/"
            self.assertEqual(method(url, {}).status_code, 401)

    def test_reader_cannot_write_books(self):
        self.login()
        self.assertEqual(self.client.post("/books/", {}).status_code, 403)
        self.assertEqual(
            self.client.patch(f"/books/{self.book.pk}/", {"inventory": 9}).status_code, 403
        )
        self.assertEqual(self.client.delete(f"/books/{self.book.pk}/").status_code, 403)

    def test_admin_book_crud(self):
        self.login(self.admin)
        data = {
            "title": "Django",
            "author": "A. Author",
            "cover": "HARD",
            "inventory": 3,
            "daily_fee": "2.00",
        }
        response = self.client.post("/books/", data)
        self.assertEqual(response.status_code, 201)
        url = f"/books/{response.data['id']}/"
        self.assertEqual(self.client.patch(url, {"inventory": 4}).data["inventory"], 4)
        self.assertEqual(self.client.put(url, data).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_book_validation(self):
        self.login(self.admin)
        for field, value in (
            ("inventory", -1),
            ("daily_fee", "0"),
            ("cover", "INVALID"),
            ("title", ""),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.client.patch(f"/books/{self.book.pk}/", {field: value}).status_code, 400
                )

    def test_cannot_delete_book_with_history(self):
        self.make_borrowing()
        self.login(self.admin)
        self.assertEqual(self.client.delete(f"/books/{self.book.pk}/").status_code, 400)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_register_hashes_password_and_blocks_privilege_escalation(self):
        response = self.client.post(
            "/users/",
            {
                "email": "NEW@EXAMPLE.COM",
                "password": PASSWORD,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn("password", response.data)

    def test_register_rejects_weak_password_and_duplicate_email(self):
        self.assertEqual(
            self.client.post(
                "/users/", {"email": "new@example.com", "password": "123"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/users/", {"email": "READER@EXAMPLE.COM", "password": PASSWORD}
            ).status_code,
            400,
        )

    def test_jwt_login_refresh_and_custom_header(self):
        response = self.client.post(
            "/users/token/", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZE="Bearer " + response.data["access"])
        self.assertEqual(self.client.get("/users/me/").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/users/token/refresh/", {"refresh": response.data["refresh"]}
            ).status_code,
            200,
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
        self.assertEqual(self.client.get("/users/me/").status_code, 401)

    def test_invalid_jwt_and_password(self):
        self.assertEqual(
            self.client.post(
                "/users/token/", {"email": self.user.email, "password": "wrong"}
            ).status_code,
            401,
        )
        self.client.credentials(HTTP_AUTHORIZE="Bearer invalid")
        self.assertEqual(self.client.get("/users/me/").status_code, 401)

    def test_profile_update_password_and_no_staff_escalation(self):
        self.login()
        response = self.client.patch(
            "/users/me/",
            {"first_name": "Reader", "password": "Changed!Password782", "is_staff": True},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Changed!Password782"))
        self.assertFalse(self.user.is_staff)
        self.assertNotIn("password", response.data)

    def test_profile_put_without_password(self):
        self.login()
        response = self.client.put(
            "/users/me/", {"email": self.user.email, "first_name": "Reader", "last_name": "One"}
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_profile_duplicate_email(self):
        self.login()
        self.assertEqual(
            self.client.patch("/users/me/", {"email": self.other.email.upper()}).status_code, 400
        )

    def test_anonymous_borrowings_and_profile_denied(self):
        borrowing = self.make_borrowing()
        for url in ("/users/me/", "/borrowings/", f"/borrowings/{borrowing.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.borrow().status_code, 401)
        self.assertEqual(self.client.post(f"/borrowings/{borrowing.pk}/return/").status_code, 401)

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

    def test_user_sees_only_own_borrowings_even_with_user_filter(self):
        own = self.make_borrowing()
        foreign = self.make_borrowing(self.other)
        self.login()
        response = self.client.get(f"/borrowings/?user_id={self.other.pk}")
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])
        self.assertEqual(self.client.get(f"/borrowings/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/borrowings/{foreign.pk}/return/").status_code, 404)

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
        return_borrowing(returned)
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

    def test_borrowing_update_delete_not_exposed(self):
        borrowing = self.make_borrowing()
        self.login(self.admin)
        self.assertEqual(self.client.patch(f"/borrowings/{borrowing.pk}/", {}).status_code, 405)
        self.assertEqual(self.client.delete(f"/borrowings/{borrowing.pk}/").status_code, 405)

    def test_create_rollback_if_record_creation_fails(self):
        with patch(
            "borrowings.services.Borrowing.objects.create",
            side_effect=RuntimeError("database failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.make_borrowing()
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_stale_return_object_cannot_increment_twice(self):
        borrowing = self.make_borrowing()
        stale = Borrowing.objects.get(pk=borrowing.pk)
        return_borrowing(borrowing)
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            return_borrowing(stale)
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

    def test_schema_and_documentation_accessible(self):
        for url in ("/schema/", "/docs/", "/redoc/"):
            self.assertEqual(self.client.get(url).status_code, 200)


class UserManagerTests(TestCase):
    def test_missing_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", PASSWORD)

    def test_superuser_flags(self):
        for field in ("is_staff", "is_superuser"):
            with self.assertRaises(ValueError):
                User.objects.create_superuser("admin@example.com", PASSWORD, **{field: False})

    def test_database_email_case_insensitive_constraint(self):
        User.objects.create_user("reader@example.com", PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="READER@example.com")])
