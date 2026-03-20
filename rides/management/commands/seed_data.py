from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from rides.models import Ride, RideEvent, User


class Command(BaseCommand):
    help: str = "Seed database with sample data for testing"

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Seeding database...")

        # Create admin user
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "role": User.Role.ADMIN,
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@wingz.com",
                "phone_number": "+1234567890",
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            token = Token.objects.create(user=admin)
            self.stdout.write(f"  Admin created. Token: {token.key}")
        else:
            token, _ = Token.objects.get_or_create(user=admin)
            self.stdout.write(f"  Admin already exists. Token: {token.key}")

        # Create riders
        riders: list[User] = []
        for i, (first, last, email) in enumerate(
            [
                ("Alice", "Smith", "alice@example.com"),
                ("Bob", "Jones", "bob@example.com"),
            ],
            start=1,
        ):
            rider, _ = User.objects.get_or_create(
                username=f"rider{i}",
                defaults={
                    "role": User.Role.RIDER,
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "phone_number": f"+100000000{i}",
                },
            )
            riders.append(rider)

        # Create drivers
        drivers: list[User] = []
        for i, (first, last, email) in enumerate(
            [
                ("Chris", "Hamilton", "chris@example.com"),
                ("Howard", "Young", "howard@example.com"),
                ("Randy", "Williams", "randy@example.com"),
            ],
            start=1,
        ):
            driver, _ = User.objects.get_or_create(
                username=f"driver{i}",
                defaults={
                    "role": User.Role.DRIVER,
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "phone_number": f"+200000000{i}",
                },
            )
            drivers.append(driver)

        now = timezone.now()

        # Create rides with various statuses and locations
        rides_data: list[dict[str, Any]] = [
            {
                "status": Ride.Status.EN_ROUTE,
                "id_rider": riders[0],
                "id_driver": drivers[0],
                "pickup_latitude": 34.0522,
                "pickup_longitude": -118.2437,
                "dropoff_latitude": 34.0195,
                "dropoff_longitude": -118.4912,
                "pickup_time": now - timedelta(hours=2),
            },
            {
                "status": Ride.Status.PICKUP,
                "id_rider": riders[1],
                "id_driver": drivers[1],
                "pickup_latitude": 40.7128,
                "pickup_longitude": -74.0060,
                "dropoff_latitude": 40.7580,
                "dropoff_longitude": -73.9855,
                "pickup_time": now - timedelta(hours=1),
            },
            {
                "status": Ride.Status.DROPOFF,
                "id_rider": riders[0],
                "id_driver": drivers[2],
                "pickup_latitude": 37.7749,
                "pickup_longitude": -122.4194,
                "dropoff_latitude": 37.3382,
                "dropoff_longitude": -121.8863,
                "pickup_time": now - timedelta(hours=3),
            },
            {
                "status": Ride.Status.PICKUP,
                "id_rider": riders[1],
                "id_driver": drivers[0],
                "pickup_latitude": 41.8781,
                "pickup_longitude": -87.6298,
                "dropoff_latitude": 41.8827,
                "dropoff_longitude": -87.6233,
                "pickup_time": now - timedelta(minutes=30),
            },
            {
                "status": Ride.Status.DROPOFF,
                "id_rider": riders[0],
                "id_driver": drivers[1],
                "pickup_latitude": 29.7604,
                "pickup_longitude": -95.3698,
                "dropoff_latitude": 29.7176,
                "dropoff_longitude": -95.4028,
                "pickup_time": now - timedelta(days=2),
            },
        ]

        for ride_data in rides_data:
            ride, created = Ride.objects.get_or_create(
                id_rider=ride_data["id_rider"],
                id_driver=ride_data["id_driver"],
                pickup_time=ride_data["pickup_time"],
                defaults=ride_data,
            )
            if created:
                # Add ride events — some within last 24h, some older
                RideEvent.objects.create(
                    id_ride=ride,
                    description="Status changed to pickup",
                    created_at=ride.pickup_time,
                )
                RideEvent.objects.create(
                    id_ride=ride,
                    description="Driver en route",
                    created_at=ride.pickup_time - timedelta(minutes=10),
                )
                if ride.status == Ride.Status.DROPOFF:
                    RideEvent.objects.create(
                        id_ride=ride,
                        description="Status changed to dropoff",
                        created_at=ride.pickup_time + timedelta(hours=1, minutes=15),
                    )

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
