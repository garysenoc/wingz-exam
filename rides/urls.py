from __future__ import annotations

from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .views import RideViewSet, UserViewSet

router: DefaultRouter = DefaultRouter()
router.register(r"rides", RideViewSet, basename="ride")
router.register(r"users", UserViewSet, basename="user")

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include(router.urls)),
]
