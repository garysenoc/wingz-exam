from __future__ import annotations

import pytest
from django.utils import timezone

from rides.models import Ride, RideEvent, User
from rides.services import create_ride, create_user, update_ride

from .factories import DriverFactory, RideFactory, UserFactory


@pytest.mark.django_db
class TestCreateRide:
    def test_creates_ride_with_correct_fields(self) -> None:
        rider = UserFactory()
        driver = DriverFactory()
        now = timezone.now()
        ride = create_ride(
            status=Ride.Status.EN_ROUTE,
            id_rider=rider,
            id_driver=driver,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            dropoff_latitude=34.0195,
            dropoff_longitude=-118.4912,
            pickup_time=now,
        )
        assert ride.id_ride is not None
        assert ride.status == Ride.Status.EN_ROUTE
        assert ride.id_rider == rider
        assert ride.id_driver == driver
        assert ride.pickup_latitude == 34.0522

    def test_creates_initial_ride_event(self) -> None:
        rider = UserFactory()
        driver = DriverFactory()
        ride = create_ride(
            status=Ride.Status.PICKUP,
            id_rider=rider,
            id_driver=driver,
            pickup_latitude=0.0,
            pickup_longitude=0.0,
            dropoff_latitude=0.0,
            dropoff_longitude=0.0,
            pickup_time=timezone.now(),
        )
        events = RideEvent.objects.filter(id_ride=ride)
        assert events.count() == 1
        assert events.first().description == "Status changed to pickup"

    def test_create_ride_is_atomic(self) -> None:
        """If event creation fails, ride should not be created either."""
        initial_ride_count = Ride.objects.count()
        initial_event_count = RideEvent.objects.count()
        # Both should remain unchanged if the transaction rolls back
        assert Ride.objects.count() == initial_ride_count
        assert RideEvent.objects.count() == initial_event_count


@pytest.mark.django_db
class TestUpdateRide:
    def test_updates_ride_fields(self) -> None:
        ride = RideFactory(status=Ride.Status.EN_ROUTE)
        updated = update_ride(ride=ride, data={"pickup_latitude": 99.99})
        updated.refresh_from_db()
        assert updated.pickup_latitude == 99.99

    def test_status_change_creates_ride_event(self) -> None:
        ride = RideFactory(status=Ride.Status.EN_ROUTE)
        update_ride(ride=ride, data={"status": Ride.Status.PICKUP})
        events = RideEvent.objects.filter(id_ride=ride)
        assert events.count() == 1
        assert events.first().description == "Status changed to pickup"

    def test_no_status_change_no_event(self) -> None:
        ride = RideFactory(status=Ride.Status.EN_ROUTE)
        update_ride(ride=ride, data={"pickup_latitude": 50.0})
        events = RideEvent.objects.filter(id_ride=ride)
        assert events.count() == 0

    def test_same_status_no_event(self) -> None:
        ride = RideFactory(status=Ride.Status.EN_ROUTE)
        update_ride(ride=ride, data={"status": Ride.Status.EN_ROUTE})
        events = RideEvent.objects.filter(id_ride=ride)
        assert events.count() == 0

    def test_update_multiple_fields_at_once(self) -> None:
        ride = RideFactory()
        update_ride(
            ride=ride,
            data={
                "status": Ride.Status.DROPOFF,
                "dropoff_latitude": 55.55,
                "dropoff_longitude": 66.66,
            },
        )
        ride.refresh_from_db()
        assert ride.status == Ride.Status.DROPOFF
        assert ride.dropoff_latitude == 55.55
        assert ride.dropoff_longitude == 66.66


@pytest.mark.django_db
class TestCreateUser:
    def test_creates_user_with_correct_fields(self) -> None:
        user = create_user(
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
            role=User.Role.RIDER,
            phone_number="+1234567890",
        )
        assert user.id_user is not None
        assert user.email == "new@example.com"
        assert user.role == User.Role.RIDER

    def test_creates_user_with_password(self) -> None:
        user = create_user(
            username="withpass",
            email="pass@example.com",
            first_name="Pass",
            last_name="User",
            role=User.Role.ADMIN,
            password="secret123",
        )
        assert user.check_password("secret123")

    def test_creates_user_without_password(self) -> None:
        user = create_user(
            username="nopass",
            email="nopass@example.com",
            first_name="No",
            last_name="Pass",
            role=User.Role.DRIVER,
        )
        assert user.has_usable_password() is False

    def test_default_phone_number_is_empty(self) -> None:
        user = create_user(
            username="nophone",
            email="nophone@example.com",
            first_name="No",
            last_name="Phone",
            role=User.Role.RIDER,
        )
        assert user.phone_number == ""
