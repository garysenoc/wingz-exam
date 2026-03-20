from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from rides.models import Ride, RideEvent, User

from .factories import (
    DriverFactory,
    RideEventFactory,
    RideFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestRideViewSetAuthentication:
    def test_unauthenticated_returns_401(self, api_client: APIClient) -> None:
        response = api_client.get("/api/rides/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_returns_403(self, api_client: APIClient) -> None:
        rider = UserFactory(role=User.Role.RIDER)
        from rest_framework.authtoken.models import Token

        token = Token.objects.create(user=rider)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = api_client.get("/api/rides/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_returns_200(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.get("/api/rides/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestRideViewSetList:
    def test_list_returns_all_rides(self, authenticated_client: APIClient) -> None:
        RideFactory.create_batch(3)
        response = authenticated_client.get("/api/rides/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_list_includes_nested_rider(self, authenticated_client: APIClient) -> None:
        RideFactory()
        response = authenticated_client.get("/api/rides/")
        ride_data = response.data["results"][0]
        assert "id_user" in ride_data["id_rider"]
        assert "first_name" in ride_data["id_rider"]

    def test_list_includes_nested_driver(self, authenticated_client: APIClient) -> None:
        RideFactory()
        response = authenticated_client.get("/api/rides/")
        ride_data = response.data["results"][0]
        assert "id_user" in ride_data["id_driver"]

    def test_list_includes_todays_ride_events(self, authenticated_client: APIClient) -> None:
        ride = RideFactory()
        RideEventFactory(id_ride=ride, description="test event")
        response = authenticated_client.get("/api/rides/")
        ride_data = response.data["results"][0]
        assert len(ride_data["todays_ride_events"]) == 1


@pytest.mark.django_db
class TestRideViewSetPagination:
    def test_pagination_default_page_size(self, authenticated_client: APIClient) -> None:
        RideFactory.create_batch(15)
        response = authenticated_client.get("/api/rides/")
        assert len(response.data["results"]) == 10
        assert response.data["count"] == 15
        assert response.data["next"] is not None

    def test_pagination_custom_page_size(self, authenticated_client: APIClient) -> None:
        RideFactory.create_batch(5)
        response = authenticated_client.get("/api/rides/?page_size=2")
        assert len(response.data["results"]) == 2
        assert response.data["count"] == 5

    def test_pagination_page_2(self, authenticated_client: APIClient) -> None:
        RideFactory.create_batch(5)
        response = authenticated_client.get("/api/rides/?page_size=2&page=2")
        assert len(response.data["results"]) == 2
        assert response.data["previous"] is not None


@pytest.mark.django_db
class TestRideViewSetFiltering:
    def test_filter_by_status(self, authenticated_client: APIClient) -> None:
        RideFactory(status=Ride.Status.PICKUP)
        RideFactory(status=Ride.Status.EN_ROUTE)
        response = authenticated_client.get("/api/rides/?status=pickup")
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "pickup"

    def test_filter_by_rider_email(self, authenticated_client: APIClient) -> None:
        rider = UserFactory(email="findme@example.com")
        RideFactory(id_rider=rider)
        RideFactory()  # different rider
        response = authenticated_client.get("/api/rides/?rider_email=findme@example.com")
        assert response.data["count"] == 1

    def test_filter_combined(self, authenticated_client: APIClient) -> None:
        rider = UserFactory(email="both@example.com")
        RideFactory(id_rider=rider, status=Ride.Status.PICKUP)
        RideFactory(id_rider=rider, status=Ride.Status.EN_ROUTE)
        RideFactory(status=Ride.Status.PICKUP)
        response = authenticated_client.get(
            "/api/rides/?status=pickup&rider_email=both@example.com"
        )
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestRideViewSetSorting:
    def test_sort_by_pickup_time_asc(self, authenticated_client: APIClient) -> None:
        now = timezone.now()
        RideFactory(pickup_time=now - timedelta(hours=2))
        RideFactory(pickup_time=now - timedelta(hours=1))
        response = authenticated_client.get("/api/rides/?sort_by=pickup_time&order=asc")
        results = response.data["results"]
        assert results[0]["pickup_time"] < results[1]["pickup_time"]

    def test_sort_by_pickup_time_desc(self, authenticated_client: APIClient) -> None:
        now = timezone.now()
        RideFactory(pickup_time=now - timedelta(hours=2))
        RideFactory(pickup_time=now - timedelta(hours=1))
        response = authenticated_client.get("/api/rides/?sort_by=pickup_time&order=desc")
        results = response.data["results"]
        assert results[0]["pickup_time"] > results[1]["pickup_time"]

    def test_sort_by_distance(self, authenticated_client: APIClient) -> None:
        # LA
        RideFactory(pickup_latitude=34.0522, pickup_longitude=-118.2437)
        # NYC
        RideFactory(pickup_latitude=40.7128, pickup_longitude=-74.0060)
        response = authenticated_client.get(
            "/api/rides/?sort_by=distance&latitude=34.0522&longitude=-118.2437"
        )
        results = response.data["results"]
        assert results[0]["distance"] < results[1]["distance"]

    def test_sort_by_distance_with_pagination(self, authenticated_client: APIClient) -> None:
        RideFactory(pickup_latitude=34.0522, pickup_longitude=-118.2437)
        RideFactory(pickup_latitude=37.7749, pickup_longitude=-122.4194)
        RideFactory(pickup_latitude=40.7128, pickup_longitude=-74.0060)
        response = authenticated_client.get(
            "/api/rides/?sort_by=distance&latitude=34.0522&longitude=-118.2437&page_size=2"
        )
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 2
        assert response.data["next"] is not None

    def test_sort_by_distance_missing_coords_fallback(
        self, authenticated_client: APIClient
    ) -> None:
        RideFactory.create_batch(2)
        response = authenticated_client.get("/api/rides/?sort_by=distance")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestRideViewSetCRUD:
    def test_create_ride(self, authenticated_client: APIClient) -> None:
        rider = UserFactory()
        driver = DriverFactory()
        data = {
            "status": "en-route",
            "id_rider": rider.id_user,
            "id_driver": driver.id_user,
            "pickup_latitude": 34.0522,
            "pickup_longitude": -118.2437,
            "dropoff_latitude": 34.0195,
            "dropoff_longitude": -118.4912,
            "pickup_time": timezone.now().isoformat(),
        }
        response = authenticated_client.post("/api/rides/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Ride.objects.count() == 1
        # Service should also create a RideEvent
        assert RideEvent.objects.count() == 1

    def test_retrieve_ride(self, authenticated_client: APIClient) -> None:
        ride = RideFactory()
        response = authenticated_client.get(f"/api/rides/{ride.id_ride}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id_ride"] == ride.id_ride

    def test_delete_ride(self, authenticated_client: APIClient) -> None:
        ride = RideFactory()
        response = authenticated_client.delete(f"/api/rides/{ride.id_ride}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Ride.objects.count() == 0

    def test_retrieve_nonexistent_ride_returns_404(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.get("/api/rides/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserViewSet:
    def test_list_users(self, authenticated_client: APIClient) -> None:
        UserFactory.create_batch(3)
        response = authenticated_client.get("/api/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_user(self, authenticated_client: APIClient) -> None:
        user = UserFactory()
        response = authenticated_client.get(f"/api/users/{user.id_user}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id_user"] == user.id_user

    def test_unauthenticated_returns_401(self, api_client: APIClient) -> None:
        response = api_client.get("/api/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
