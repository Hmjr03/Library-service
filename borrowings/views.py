from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from .models import Borrowing
from .serializers import BorrowingCreateSerializer, BorrowingReadSerializer


class BorrowingViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user").all()
    serializer_class = BorrowingReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset if self.request.user.is_staff else queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        return BorrowingCreateSerializer if self.action == "create" else BorrowingReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            BorrowingReadSerializer(serializer.save()).data, status=status.HTTP_201_CREATED
        )
