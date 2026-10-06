from django.contrib import admin
from .models import Amenity, RoomType, Room


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ("name",)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "base_price", "max_guests", "total_rooms", "is_active")
    list_filter = ("is_active", "bed_type")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("amenities",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "room_type", "floor", "status", "updated_at")
    list_filter = ("status", "floor", "room_type")
    search_fields = ("number",)
