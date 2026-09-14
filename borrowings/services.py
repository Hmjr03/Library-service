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


