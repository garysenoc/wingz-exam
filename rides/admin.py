from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Ride, RideEvent, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display: list[str] = ["id_user", "email", "first_name", "last_name", "role"]
    list_filter: list[str] = ["role"]
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role", "phone_number")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Role", {"fields": ("role", "phone_number")}),)


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id_ride", "status", "id_rider", "id_driver", "pickup_time"]
    list_filter: list[str] = ["status"]
    raw_id_fields: list[str] = ["id_rider", "id_driver"]


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id_ride_event", "id_ride", "description", "created_at"]
    raw_id_fields: list[str] = ["id_ride"]
