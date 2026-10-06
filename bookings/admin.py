from django.contrib import admin
from .models import Booking, RateRule, RoomAssignment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("code", "guest_name", "room_type", "check_in", "check_out", "rooms_count", "status", "grand_total")
    list_filter = ("status", "source", "room_type")
    search_fields = ("code", "guest_name", "guest_email")
    date_hierarchy = "check_in"
    readonly_fields = ("code", "rate_details", "created_at", "updated_at")


@admin.register(RateRule)
class RateRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "rule_type", "room_type", "start_date", "end_date", "multiplier", "priority", "is_active")
    list_filter = ("rule_type", "is_active")


admin.site.register(RoomAssignment)
