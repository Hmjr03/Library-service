from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from .models import Borrowing
from .serializers import (
    BorrowingCreateSerializer,
    BorrowingFilterSerializer,
    BorrowingReadSerializer,
)


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user").all()
    serializer_class = BorrowingReadSerializer

    def get_serializer_class(self):
        return BorrowingCreateSerializer if self.action == "create" else BorrowingReadSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Borrowing.objects.none()
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        if self.action == "list":
            filters = BorrowingFilterSerializer(data=dict(self.request.query_params.items()))
            filters.is_valid(raise_exception=True)
            params = filters.validated_data
            if "is_active" in params:
                queryset = queryset.filter(actual_return_date__isnull=params["is_active"])
            if self.request.user.is_staff and "user_id" in params:
                queryset = queryset.filter(user_id=params["user_id"])
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("is_active", bool, description="true: not returned; false: returned."),
            OpenApiParameter(
                "user_id",
                int,
                description="Staff only. Ignored for regular users; they always see their own records.",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=BorrowingCreateSerializer,
        responses={201: BorrowingReadSerializer},
        description="Borrow one available copy. The authenticated user and current date are assigned automatically. Inventory decreases atomically. Past return dates or unavailable books return 400.",
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrowing = serializer.save()
        return Response(
            BorrowingReadSerializer(borrowing, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
