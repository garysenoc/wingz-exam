from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from rides.models import Ride, RideEvent
from rides.selectors import RideFilters, get_ride_list, get_user_list

from .factories import (
    DriverFactory,
    RideEventFactory,
    RideFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestGetRideList:
    def test_returns_all_rides(self) -> None:
        RideFactory.create_batch(3)
        rides = get_ride_list(filters=RideFilters())
        assert rides.count() == 3

    def test_default_order_is_newest_first(self) -> None:
        now = timezone.now()
        old = RideFactory(pickup_time=now - timedelta(hours=2))
        new = RideFactory(pickup_time=now - timedelta(hours=1))
        rides = list(get_ride_list(filters=RideFilters()))
        assert rides[0].id_ride == new.id_ride
        assert rides[1].id_ride == old.id_ride

    # --- Filtering ---

    def test_filter_by_status(self) -> None:
        RideFactory(status=Ride.Status.PICKUP)
        RideFactory(status=Ride.Status.EN_ROUTE)
        RideFactory(status=Ride.Status.DROPOFF)
        rides = get_ride_list(filters=RideFilters(status="pickup"))
        assert rides.count() == 1
        assert rides.first().status == "pickup"

    def test_filter_by_rider_email(self) -> None:
        rider = UserFactory(email="target@example.com")
        RideFactory(id_rider=rider)
        RideFactory()  # different rider
        rides = get_ride_list(filters=RideFilters(rider_email="target@example.com"))
        assert rides.count() == 1

    def test_filter_by_status_and_email_combined(self) -> None:
        rider = UserFactory(email="combo@example.com")
        RideFactory(id_rider=rider, status=Ride.Status.PICKUP)
        RideFactory(id_rider=rider, status=Ride.Status.EN_ROUTE)
        RideFactory(status=Ride.Status.PICKUP)  # different rider
        rides = get_ride_list(filters=RideFilters(status="pickup", rider_email="combo@example.com"))
        assert rides.count() == 1

    def test_filter_nonexistent_status_returns_empty(self) -> None:
        RideFactory()
        rides = get_ride_list(filters=RideFilters(status="nonexistent"))
        assert rides.count() == 0

    # --- Sorting ---

    def test_sort_by_pickup_time_asc(self) -> None:
        now = timezone.now()
        r1 = RideFactory(pickup_time=now - timedelta(hours=3))
        r2 = RideFactory(pickup_time=now - timedelta(hours=1))
        rides = list(get_ride_list(filters=RideFilters(sort_by="pickup_time", sort_order="asc")))
        assert rides[0].id_ride == r1.id_ride
        assert rides[1].id_ride == r2.id_ride

    def test_sort_by_pickup_time_desc(self) -> None:
        now = timezone.now()
        r1 = RideFactory(pickup_time=now - timedelta(hours=3))
        r2 = RideFactory(pickup_time=now - timedelta(hours=1))
        rides = list(get_ride_list(filters=RideFilters(sort_by="pickup_time", sort_order="desc")))
        assert rides[0].id_ride == r2.id_ride
        assert rides[1].id_ride == r1.id_ride

    def test_sort_by_distance(self) -> None:
        # LA coordinates
        la_ride = RideFactory(pickup_latitude=34.0522, pickup_longitude=-118.2437)
        # NYC coordinates — much farther from LA
        nyc_ride = RideFactory(pickup_latitude=40.7128, pickup_longitude=-74.0060)
        rides = list(
            get_ride_list(
                filters=RideFilters(sort_by="distance", latitude=34.0522, longitude=-118.2437)
            )
        )
        assert rides[0].id_ride == la_ride.id_ride
        assert rides[1].id_ride == nyc_ride.id_ride

    def test_sort_by_distance_annotates_distance_field(self) -> None:
        RideFactory(pickup_latitude=34.0522, pickup_longitude=-118.2437)
        rides = list(
            get_ride_list(
                filters=RideFilters(sort_by="distance", latitude=34.0522, longitude=-118.2437)
            )
        )
        assert hasattr(rides[0], "distance")
        assert rides[0].distance == pytest.approx(0.0, abs=0.01)

    def test_sort_by_distance_without_coords_falls_back_to_default(self) -> None:
        now = timezone.now()
        RideFactory(pickup_time=now - timedelta(hours=2))
        RideFactory(pickup_time=now - timedelta(hours=1))
        rides = list(
            get_ride_list(filters=RideFilters(sort_by="distance", latitude=None, longitude=None))
        )
        # Falls back to default ordering: most recent first
        assert rides[0].pickup_time > rides[1].pickup_time

    # --- Prefetch: todays_ride_events ---

    def test_todays_ride_events_includes_recent_events(self) -> None:
        ride = RideFactory()
        RideEventFactory(id_ride=ride, description="recent")
        rides = list(get_ride_list(filters=RideFilters()))
        assert len(rides[0].todays_ride_events) == 1
        assert rides[0].todays_ride_events[0].description == "recent"

    def test_todays_ride_events_excludes_old_events(self) -> None:
        ride = RideFactory()
        event = RideEventFactory(id_ride=ride, description="old")
        # auto_now_add prevents setting created_at on save, so use update()
        RideEvent.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        rides = list(get_ride_list(filters=RideFilters()))
        assert len(rides[0].todays_ride_events) == 0

    def test_todays_ride_events_ordered_newest_first(self) -> None:
        ride = RideFactory()
        RideEventFactory(id_ride=ride, description="first")
        RideEventFactory(id_ride=ride, description="second")
        rides = list(get_ride_list(filters=RideFilters()))
        events = rides[0].todays_ride_events
        assert events[0].created_at >= events[1].created_at

    # --- Performance ---

    def test_query_count_is_two(self) -> None:
        """Ride list + related data should use exactly 2 SQL queries."""
        rider = UserFactory()
        driver = DriverFactory()
        for _ in range(5):
            ride = RideFactory(id_rider=rider, id_driver=driver)
            RideEventFactory(id_ride=ride)
            RideEventFactory(id_ride=ride)

        with CaptureQueriesContext(connection) as ctx:
            rides = list(get_ride_list(filters=RideFilters()))
            for r in rides:
                _ = r.id_rider.first_name
                _ = r.id_driver.last_name
                _ = r.todays_ride_events

        assert len(ctx.captured_queries) == 2


@pytest.mark.django_db
class TestGetUserList:
    def test_returns_all_users(self) -> None:
        UserFactory.create_batch(3)
        users = get_user_list()
        assert users.count() == 3

    def test_returns_empty_when_no_users(self) -> None:
        users = get_user_list()
        assert users.count() == 0
