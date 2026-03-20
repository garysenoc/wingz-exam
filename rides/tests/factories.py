from __future__ import annotations

import factory
from django.utils import timezone

from rides.models import Ride, RideEvent, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = factory.Faker("phone_number")
    role = User.Role.RIDER
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class AdminFactory(UserFactory):
    role = User.Role.ADMIN
    username = factory.Sequence(lambda n: f"admin_{n}")


class DriverFactory(UserFactory):
    role = User.Role.DRIVER
    username = factory.Sequence(lambda n: f"driver_{n}")


class RideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ride

    status = Ride.Status.EN_ROUTE
    id_rider = factory.SubFactory(UserFactory)
    id_driver = factory.SubFactory(DriverFactory)
    pickup_latitude = 34.0522
    pickup_longitude = -118.2437
    dropoff_latitude = 34.0195
    dropoff_longitude = -118.4912
    pickup_time = factory.LazyFunction(timezone.now)


class RideEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RideEvent

    id_ride = factory.SubFactory(RideFactory)
    description = factory.Faker("sentence")
    created_at = factory.LazyFunction(timezone.now)
