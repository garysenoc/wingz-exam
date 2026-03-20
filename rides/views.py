from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.pagination import PageNumberPagination

from .models import Ride, User
from .permissions import IsAdminRole
from .selectors import RideFilters, get_ride_list, get_user_list
from .serializers import RideSerializer, RideWriteSerializer, UserSerializer
from .services import create_ride, update_ride


class RidePagination(PageNumberPagination):
    page_size: int = 10
    page_size_query_param: str = "page_size"
    max_page_size: int = 100


@extend_schema_view(
    list=extend_schema(
        summary="List rides",
        description=(
            "Returns a paginated list of rides with nested rider, driver, "
            "and today's ride events (last 24 hours only). "
            "Supports filtering by status and rider email, "
            "and sorting by pickup_time or distance to a GPS position."
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filter by ride status",
                required=False,
                type=str,
                enum=["en-route", "pickup", "dropoff"],
                examples=[
                    OpenApiExample("No filter", value=""),
                    OpenApiExample("Pickup only", value="pickup"),
                    OpenApiExample("En-route only", value="en-route"),
                    OpenApiExample("Dropoff only", value="dropoff"),
                ],
            ),
            OpenApiParameter(
                name="rider_email",
                description="Filter by rider's email address",
                required=False,
                type=str,
                examples=[
                    OpenApiExample("No filter", value=""),
                    OpenApiExample("Alice", value="alice@example.com"),
                    OpenApiExample("Bob", value="bob@example.com"),
                ],
            ),
            OpenApiParameter(
                name="sort_by",
                description="Sort field: 'pickup_time' or 'distance'",
                required=False,
                type=str,
                enum=["pickup_time", "distance"],
            ),
            OpenApiParameter(
                name="order",
                description="Sort order for pickup_time (default: asc)",
                required=False,
                type=str,
                enum=["asc", "desc"],
            ),
            OpenApiParameter(
                name="latitude",
                description="Latitude for distance sorting",
                required=False,
                type=float,
                examples=[
                    OpenApiExample("Los Angeles", value=34.0522),
                    OpenApiExample("New York", value=40.7128),
                    OpenApiExample("San Francisco", value=37.7749),
                ],
            ),
            OpenApiParameter(
                name="longitude",
                description="Longitude for distance sorting",
                required=False,
                type=float,
                examples=[
                    OpenApiExample("Los Angeles", value=-118.2437),
                    OpenApiExample("New York", value=-74.0060),
                    OpenApiExample("San Francisco", value=-122.4194),
                ],
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of results per page (default: 10, max: 100)",
                required=False,
                type=int,
                examples=[
                    OpenApiExample("Default", value=10),
                    OpenApiExample("Small", value=2),
                    OpenApiExample("Large", value=50),
                ],
            ),
        ],
    ),
    create=extend_schema(
        summary="Create a ride",
        examples=[
            OpenApiExample(
                "Create a ride (LA to Santa Monica)",
                value={
                    "status": "en-route",
                    "id_rider": 2,
                    "id_driver": 4,
                    "pickup_latitude": 34.0522,
                    "pickup_longitude": -118.2437,
                    "dropoff_latitude": 34.0195,
                    "dropoff_longitude": -118.4912,
                    "pickup_time": "2026-03-20T10:00:00Z",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve a ride"),
    update=extend_schema(summary="Update a ride"),
    partial_update=extend_schema(summary="Partially update a ride"),
    destroy=extend_schema(summary="Delete a ride"),
)
class RideViewSet(viewsets.ModelViewSet[Ride]):
    """
    Thin view layer — delegates query logic to selectors,
    business logic to services.

    Query budget: 2 queries (+1 for pagination count).
    """

    pagination_class = RidePagination
    permission_classes: list[type] = [IsAdminRole]
    authentication_classes: list[type] = [TokenAuthentication, SessionAuthentication]

    def get_serializer_class(self) -> type:
        if self.action in ("create", "update", "partial_update"):
            return RideWriteSerializer
        return RideSerializer

    def get_queryset(self) -> QuerySet[Ride]:
        filters = RideFilters(
            status=self.request.query_params.get("status"),
            rider_email=self.request.query_params.get("rider_email"),
            sort_by=self.request.query_params.get("sort_by"),
            sort_order=self.request.query_params.get("order", "asc"),
            latitude=self._parse_float(self.request.query_params.get("latitude")),
            longitude=self._parse_float(self.request.query_params.get("longitude")),
        )
        return get_ride_list(filters=filters)

    def perform_create(self, serializer: RideWriteSerializer) -> None:
        ride = create_ride(**serializer.validated_data)
        serializer.instance = ride

    def perform_update(self, serializer: RideWriteSerializer) -> None:
        ride = update_ride(ride=self.get_object(), data=serializer.validated_data)
        serializer.instance = ride

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


@extend_schema_view(
    list=extend_schema(summary="List users"),
    create=extend_schema(summary="Create a user"),
    retrieve=extend_schema(summary="Retrieve a user"),
    update=extend_schema(summary="Update a user"),
    partial_update=extend_schema(summary="Partially update a user"),
    destroy=extend_schema(summary="Delete a user"),
)
class UserViewSet(viewsets.ModelViewSet[User]):
    serializer_class = UserSerializer
    permission_classes: list[type] = [IsAdminRole]
    authentication_classes: list[type] = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self) -> QuerySet[User]:
        return get_user_list()
