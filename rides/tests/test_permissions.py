from __future__ import annotations

import pytest
from django.test import RequestFactory
from rest_framework.request import Request

from rides.models import User
from rides.permissions import IsAdminRole

from .factories import AdminFactory, DriverFactory, UserFactory


@pytest.mark.django_db
class TestIsAdminRole:
    def setup_method(self) -> None:
        self.permission = IsAdminRole()
        self.factory = RequestFactory()

    def _make_request(self, user: User | None = None) -> Request:
        django_request = self.factory.get("/")
        request = Request(django_request)
        if user:
            request.user = user
        return request

    def test_admin_user_allowed(self) -> None:
        admin = AdminFactory()
        request = self._make_request(admin)
        assert self.permission.has_permission(request, None) is True

    def test_rider_user_denied(self) -> None:
        rider = UserFactory(role=User.Role.RIDER)
        request = self._make_request(rider)
        assert self.permission.has_permission(request, None) is False

    def test_driver_user_denied(self) -> None:
        driver = DriverFactory()
        request = self._make_request(driver)
        assert self.permission.has_permission(request, None) is False

    def test_unauthenticated_user_denied(self) -> None:
        from django.contrib.auth.models import AnonymousUser

        django_request = self.factory.get("/")
        request = Request(django_request)
        request.user = AnonymousUser()
        assert self.permission.has_permission(request, None) is False

    def test_permission_message(self) -> None:
        assert "admin" in self.permission.message.lower()
