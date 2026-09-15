from tests.base import LibraryFixture


class StageTests(LibraryFixture):
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
