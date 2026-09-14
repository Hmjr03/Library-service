from rest_framework import viewsets
from .models import Borrowing
from .serializers import BorrowingReadSerializer


class BorrowingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user").all()
    serializer_class = BorrowingReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset if self.request.user.is_staff else queryset.filter(user=self.request.user)
