from tests.base import LibraryFixture


class StageTests(LibraryFixture):
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
