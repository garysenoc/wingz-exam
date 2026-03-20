from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        RIDER = "rider", "Rider"
        DRIVER = "driver", "Driver"

    id_user: models.AutoField = models.AutoField(primary_key=True)
    role: models.CharField = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RIDER,
    )
    phone_number: models.CharField = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        db_table = "user"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN


class Ride(models.Model):
    """Ride linking a rider and driver with GPS coordinates."""

    class Status(models.TextChoices):
        EN_ROUTE = "en-route", "En Route"
        PICKUP = "pickup", "Pickup"
        DROPOFF = "dropoff", "Dropoff"

    id_ride: models.AutoField = models.AutoField(primary_key=True)
    status: models.CharField = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EN_ROUTE,
    )
    id_rider: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rides_as_rider",
        db_column="id_rider",
    )
    id_driver: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rides_as_driver",
        db_column="id_driver",
    )
    pickup_latitude: models.FloatField = models.FloatField()
    pickup_longitude: models.FloatField = models.FloatField()
    dropoff_latitude: models.FloatField = models.FloatField()
    dropoff_longitude: models.FloatField = models.FloatField()
    pickup_time: models.DateTimeField = models.DateTimeField()

    class Meta:
        db_table = "ride"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["pickup_time"]),
            # Composite index for filtering by status + sorting by pickup_time
            models.Index(fields=["status", "-pickup_time"]),
        ]

    def __str__(self) -> str:
        return f"Ride {self.id_ride}"


class RideEvent(models.Model):
    """Events that occur during a ride."""

    id_ride_event: models.AutoField = models.AutoField(primary_key=True)
    id_ride: models.ForeignKey = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name="ride_events",
        db_column="id_ride",
    )
    description: models.CharField = models.CharField(max_length=255)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ride_event"
        indexes = [
            models.Index(fields=["created_at"]),
            # Composite index for the Prefetch query:
            # WHERE id_ride IN (...) AND created_at >= [24h ago] ORDER BY created_at DESC
            models.Index(fields=["id_ride", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"RideEvent {self.id_ride_event}: {self.description}"
