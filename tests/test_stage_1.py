from django.db import IntegrityError, transaction
from django.test import TestCase

from tests.base import PASSWORD, LibraryFixture, User


class StageTests(LibraryFixture):
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
