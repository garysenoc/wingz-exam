from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction

from .models import Ride, RideEvent, User

# ---------------------------------------------------------------------------
# Ride services
# ---------------------------------------------------------------------------


@transaction.atomic
def create_ride(
    *,
    status: str,
    id_rider: User,
    id_driver: User,
    pickup_latitude: float,
    pickup_longitude: float,
    dropoff_latitude: float,
    dropoff_longitude: float,
    pickup_time: datetime,
) -> Ride:
    """Create a new ride and its initial event."""
    ride: Ride = Ride.objects.create(
        status=status,
        id_rider=id_rider,
        id_driver=id_driver,
        pickup_latitude=pickup_latitude,
        pickup_longitude=pickup_longitude,
        dropoff_latitude=dropoff_latitude,
        dropoff_longitude=dropoff_longitude,
        pickup_time=pickup_time,
    )
    RideEvent.objects.create(
        id_ride=ride,
        description=f"Status changed to {status}",
    )
    return ride


@transaction.atomic
def update_ride(*, ride: Ride, data: dict[str, Any]) -> Ride:
    """Update ride fields. If status changes, log a RideEvent."""
    old_status: str = ride.status
    new_status: str | None = data.get("status")

    for field, value in data.items():
        setattr(ride, field, value)
    ride.save()

    if new_status and new_status != old_status:
        RideEvent.objects.create(
            id_ride=ride,
            description=f"Status changed to {new_status}",
        )

    return ride


# ---------------------------------------------------------------------------
# User services
# ---------------------------------------------------------------------------


def create_user(
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    role: str,
    phone_number: str = "",
    password: str | None = None,
) -> User:
    """Create a new user with an optional password."""
    user: User = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone_number=phone_number,
    )
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()
    user.save()
    return user
