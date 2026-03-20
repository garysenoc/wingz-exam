from __future__ import annotations

import pytest
from django.utils import timezone

from rides.models import Ride
from rides.selectors import RideFilters, get_ride_list
from rides.serializers import (
    RideEventSerializer,
    RideSerializer,
    RideWriteSerializer,
    UserSerializer,
)

from .factories import (
    DriverFactory,
    RideEventFactory,
    RideFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestUserSerializer:
    def test_serializes_expected_fields(self) -> None:
        user = UserFactory(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            role="rider",
            phone_number="+1234567890",
        )
        data = UserSerializer(user).data
        assert data["id_user"] == user.id_user
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"
        assert data["email"] == "alice@example.com"
        assert data["role"] == "rider"
        assert data["phone_number"] == "+1234567890"

    def test_does_not_expose_password(self) -> None:
        user = UserFactory()
        data = UserSerializer(user).data
        assert "password" not in data


@pytest.mark.django_db
class TestRideEventSerializer:
    def test_serializes_expected_fields(self) -> None:
        event = RideEventFactory(description="Status changed to pickup")
        data = RideEventSerializer(event).data
        assert data["id_ride_event"] == event.id_ride_event
        assert data["description"] == "Status changed to pickup"
        assert "created_at" in data
        assert "id_ride" in data


@pytest.mark.django_db
class TestRideSerializer:
    def test_serializes_nested_rider_and_driver(self) -> None:
        RideFactory()
        rides = list(get_ride_list(filters=RideFilters()))
        data = RideSerializer(rides[0]).data
        assert "id_user" in data["id_rider"]
        assert "id_user" in data["id_driver"]

    def test_serializes_todays_ride_events(self) -> None:
        ride = RideFactory()
        RideEventFactory(id_ride=ride, description="test event")
        rides = list(get_ride_list(filters=RideFilters()))
        data = RideSerializer(rides[0]).data
        assert len(data["todays_ride_events"]) == 1
        assert data["todays_ride_events"][0]["description"] == "test event"

    def test_distance_omitted_when_none(self) -> None:
        RideFactory()
        rides = list(get_ride_list(filters=RideFilters()))
        data = RideSerializer(rides[0]).data
        assert "distance" not in data

    def test_distance_included_when_annotated(self) -> None:
        RideFactory(pickup_latitude=34.0522, pickup_longitude=-118.2437)
        rides = list(
            get_ride_list(
                filters=RideFilters(sort_by="distance", latitude=34.0522, longitude=-118.2437)
            )
        )
        data = RideSerializer(rides[0]).data
        assert "distance" in data
        assert data["distance"] == pytest.approx(0.0, abs=0.01)

    def test_serializes_all_expected_fields(self) -> None:
        RideFactory()
        rides = list(get_ride_list(filters=RideFilters()))
        data = RideSerializer(rides[0]).data
        expected_keys = {
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "todays_ride_events",
        }
        assert expected_keys.issubset(data.keys())


@pytest.mark.django_db
class TestRideWriteSerializer:
    def test_accepts_fk_ids(self) -> None:
        rider = UserFactory()
        driver = DriverFactory()
        data = {
            "status": Ride.Status.EN_ROUTE,
            "id_rider": rider.id_user,
            "id_driver": driver.id_user,
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
            "dropoff_latitude": 34.0195,
            "dropoff_longitude": -118.4912,
            "pickup_time": timezone.now().isoformat(),
        }
        serializer = RideWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_rejects_missing_required_fields(self) -> None:
        serializer = RideWriteSerializer(data={})
        assert serializer.is_valid() is False
        assert "id_rider" in serializer.errors
        assert "id_driver" in serializer.errors

    def test_rejects_invalid_status(self) -> None:
        rider = UserFactory()
        driver = DriverFactory()
        data = {
            "status": "invalid_status",
            "id_rider": rider.id_user,
            "id_driver": driver.id_user,
            "pickup_latitude": 34.0,
            "pickup_longitude": -118.0,
            "dropoff_latitude": 34.0,
            "dropoff_longitude": -118.0,
            "pickup_time": timezone.now().isoformat(),
        }
        serializer = RideWriteSerializer(data=data)
        assert serializer.is_valid() is False
        assert "status" in serializer.errors
