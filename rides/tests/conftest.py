from __future__ import annotations

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from rides.models import User

from .factories import AdminFactory, DriverFactory, UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user(db: None) -> User:
    return AdminFactory()


@pytest.fixture
def admin_token(admin_user: User) -> Token:
    return Token.objects.create(user=admin_user)


@pytest.fixture
def authenticated_client(api_client: APIClient, admin_token: Token) -> APIClient:
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {admin_token.key}")
    return api_client


@pytest.fixture
def rider(db: None) -> User:
    return UserFactory(role=User.Role.RIDER)


@pytest.fixture
def driver(db: None) -> User:
    return DriverFactory()
