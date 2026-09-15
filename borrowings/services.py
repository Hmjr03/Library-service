from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from books.models import Book

from .models import Borrowing


@transaction.atomic
def create_borrowing(*, user, book, expected_return_date):
    today = timezone.localdate()
    if expected_return_date < today:
        raise ValidationError({"expected_return_date": "Return date cannot be before today."})
    # Conditional database update prevents inventory from going below zero.
    if not Book.objects.filter(pk=book.pk, inventory__gt=0).update(inventory=F("inventory") - 1):
        raise ValidationError({"book": "This book is out of stock."})
    return Borrowing.objects.create(
        user=user, book=book, borrow_date=today, expected_return_date=expected_return_date
    )


@transaction.atomic
def return_borrowing(borrowing):
    # A compare-and-set update makes double return impossible, including races.
    if not Borrowing.objects.filter(pk=borrowing.pk, actual_return_date__isnull=True).update(
        actual_return_date=timezone.localdate()
    ):
        raise ValidationError({"detail": "This borrowing has already been returned."})
    Book.objects.filter(pk=borrowing.book_id).update(inventory=F("inventory") + 1)
    borrowing.refresh_from_db()
    return borrowing
