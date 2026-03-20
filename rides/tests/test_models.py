from __future__ import annotations

import pytest

from rides.models import Ride, RideEvent, User

from .factories import DriverFactory, RideEventFactory, RideFactory, UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_str_returns_full_name(self) -> None:
        user = UserFactory(first_name="Alice", last_name="Smith")
        assert str(user) == "Alice Smith"

    def test_is_admin_true_for_admin_role(self) -> None:
        user = UserFactory(role=User.Role.ADMIN)
        assert user.is_admin is True

    def test_is_admin_false_for_rider_role(self) -> None:
        user = UserFactory(role=User.Role.RIDER)
        assert user.is_admin is False

    def test_is_admin_false_for_driver_role(self) -> None:
        user = UserFactory(role=User.Role.DRIVER)
        assert user.is_admin is False

    def test_default_role_is_rider(self) -> None:
        user = UserFactory()
        assert user.role == User.Role.RIDER

    def test_user_db_table_name(self) -> None:
        assert User._meta.db_table == "user"

    def test_unique_username_constraint(self) -> None:
        UserFactory(username="duplicate")
        with pytest.raises(Exception):  # noqa: B017
            UserFactory(username="duplicate")


@pytest.mark.django_db
class TestRideModel:
    def test_str_returns_ride_id(self) -> None:
        ride = RideFactory()
        assert str(ride) == f"Ride {ride.id_ride}"

    def test_default_status_is_en_route(self) -> None:
        ride = RideFactory()
        assert ride.status == Ride.Status.EN_ROUTE

    def test_ride_db_table_name(self) -> None:
        assert Ride._meta.db_table == "ride"

    def test_ride_has_status_index(self) -> None:
        index_fields = [idx.fields for idx in Ride._meta.indexes]
        assert ["status"] in index_fields

    def test_ride_has_pickup_time_index(self) -> None:
        index_fields = [idx.fields for idx in Ride._meta.indexes]
        assert ["pickup_time"] in index_fields

    def test_ride_rider_relationship(self) -> None:
        rider = UserFactory(role=User.Role.RIDER)
        ride = RideFactory(id_rider=rider)
        assert ride.id_rider == rider
        assert ride in rider.rides_as_rider.all()

    def test_ride_driver_relationship(self) -> None:
        driver = DriverFactory()
        ride = RideFactory(id_driver=driver)
        assert ride.id_driver == driver
        assert ride in driver.rides_as_driver.all()

    def test_cascade_delete_rider_deletes_ride(self) -> None:
        ride = RideFactory()
        ride.id_rider.delete()
        assert not Ride.objects.filter(id_ride=ride.id_ride).exists()

    def test_all_status_choices_valid(self) -> None:
        for status_value, _ in Ride.Status.choices:
            ride = RideFactory(status=status_value)
            assert ride.status == status_value


@pytest.mark.django_db
class TestRideEventModel:
    def test_str_returns_description(self) -> None:
        event = RideEventFactory(description="Status changed to pickup")
        assert "Status changed to pickup" in str(event)

    def test_ride_event_db_table_name(self) -> None:
        assert RideEvent._meta.db_table == "ride_event"

    def test_ride_event_has_created_at_index(self) -> None:
        index_fields = [idx.fields for idx in RideEvent._meta.indexes]
        assert ["created_at"] in index_fields

    def test_cascade_delete_ride_deletes_events(self) -> None:
        ride = RideFactory()
        RideEventFactory(id_ride=ride)
        RideEventFactory(id_ride=ride)
        ride.delete()
        assert RideEvent.objects.count() == 0

    def test_ride_events_related_name(self) -> None:
        ride = RideFactory()
        event = RideEventFactory(id_ride=ride)
        assert event in ride.ride_events.all()
