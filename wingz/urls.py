"""
URL configuration for wingz project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.authtoken.views import ObtainAuthToken


@extend_schema(
    summary="Get auth token",
    description="Send username and password to receive an API token. No authentication required.",
    auth=[],
    request=inline_serializer(
        name="TokenRequest",
        fields={
            "username": serializers.CharField(default="admin"),
            "password": serializers.CharField(default="admin123"),
        },
    ),
    responses={
        200: inline_serializer(
            name="TokenResponse",
            fields={
                "token": serializers.CharField(),
            },
        ),
    },
    examples=[
        OpenApiExample(
            "Admin login",
            value={"username": "admin", "password": "admin123"},
            request_only=True,
        ),
    ],
)
class TokenAuthView(ObtainAuthToken):
    authentication_classes = []
    permission_classes = []


TokenView = csrf_exempt(TokenAuthView.as_view())

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rides.urls")),
    path("api-token-auth/", TokenView, name="api_token_auth"),
    path("api-auth/", include("rest_framework.urls")),
    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
