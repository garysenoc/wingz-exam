from __future__ import annotations

from dataclasses import dataclass

from django.db.models import F, FloatField, Prefetch, QuerySet, Value
from django.db.models.functions import ACos, Cos, Radians, Sin
from django.utils import timezone

from .models import Ride, RideEvent, User

EARTH_RADIUS_KM: float = 6371.0


@dataclass(frozen=True)
class RideFilters:
    """Immutable filter parameters for ride queries."""

    status: str | None = None
    rider_email: str | None = None
    sort_by: str | None = None
    sort_order: str = "asc"
    latitude: float | None = None
    longitude: float | None = None


def get_ride_list(*, filters: RideFilters) -> QuerySet[Ride]:
    """
    Return an optimized ride queryset with related data.

    Query budget:
      - 1 query: rides + rider + driver (via select_related JOIN)
      - 1 query: today's ride events (via Prefetch with 24h filter)
      - 1 query: pagination count (added by DRF paginator)
    """
    qs: QuerySet[Ride] = Ride.objects.select_related("id_rider", "id_driver").prefetch_related(
        _todays_ride_events_prefetch()
    )

    qs = _apply_filters(qs, filters)
    qs = _apply_sorting(qs, filters)

    return qs


def get_user_list() -> QuerySet[User]:
    """Return all users."""
    return User.objects.all()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _todays_ride_events_prefetch() -> Prefetch:
    """Prefetch only RideEvents from the last 24 hours."""
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    return Prefetch(
        "ride_events",
        queryset=RideEvent.objects.filter(
            created_at__gte=cutoff,
        ).order_by("-created_at"),
        to_attr="todays_ride_events",
    )


def _apply_filters(qs: QuerySet[Ride], filters: RideFilters) -> QuerySet[Ride]:
    """Apply optional status and rider email filters."""
    if filters.status:
        qs = qs.filter(status=filters.status)
    if filters.rider_email:
        qs = qs.filter(id_rider__email=filters.rider_email)
    return qs


def _apply_sorting(qs: QuerySet[Ride], filters: RideFilters) -> QuerySet[Ride]:
    """Apply sorting — by pickup_time or by distance to a GPS coordinate."""
    if filters.sort_by == "distance" and _has_coordinates(filters):
        return _sort_by_distance(qs, filters.latitude, filters.longitude)  # type: ignore[arg-type]

    if filters.sort_by == "pickup_time":
        prefix: str = "-" if filters.sort_order == "desc" else ""
        return qs.order_by(f"{prefix}pickup_time")

    # Default: most recent first
    return qs.order_by("-pickup_time")


def _sort_by_distance(
    qs: QuerySet[Ride],
    lat: float,
    lng: float,
) -> QuerySet[Ride]:
    """
    Annotate each ride with distance (km) from the given point and sort ascending.

    Uses the Spherical Law of Cosines computed entirely in the database
    so the sort is compatible with pagination and scales to large tables.
    """
    return qs.annotate(
        distance=Value(EARTH_RADIUS_KM, output_field=FloatField())
        * ACos(
            Cos(Radians(Value(lat)))
            * Cos(Radians(F("pickup_latitude")))
            * Cos(Radians(F("pickup_longitude")) - Radians(Value(lng)))
            + Sin(Radians(Value(lat))) * Sin(Radians(F("pickup_latitude")))
        ),
    ).order_by("distance")


def _has_coordinates(filters: RideFilters) -> bool:
    return filters.latitude is not None and filters.longitude is not None
