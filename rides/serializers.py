from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Ride, RideEvent, User


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields: list[str] = [
            "id_user",
            "role",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        ]


class RideEventSerializer(serializers.ModelSerializer[RideEvent]):
    class Meta:
        model = RideEvent
        fields: list[str] = [
            "id_ride_event",
            "id_ride",
            "description",
            "created_at",
        ]


class RideSerializer(serializers.ModelSerializer[Ride]):
    """Read serializer — nested rider, driver, and today's ride events."""

    id_rider = UserSerializer(read_only=True)
    id_driver = UserSerializer(read_only=True)
    todays_ride_events = RideEventSerializer(many=True, read_only=True)
    distance = serializers.FloatField(read_only=True, required=False, default=None)

    class Meta:
        model = Ride
        fields: list[str] = [
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
            "distance",
        ]

    def to_representation(self, instance: Ride) -> dict[str, Any]:
        data: dict[str, Any] = super().to_representation(instance)
        if data.get("distance") is None:
            data.pop("distance", None)
        return data


class RideWriteSerializer(serializers.ModelSerializer[Ride]):
    """Write serializer — accepts FK ids for create/update."""

    class Meta:
        model = Ride
        fields: list[str] = [
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
        ]
