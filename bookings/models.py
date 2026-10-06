import json
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from hotel.models import Property, Room, RoomType


class RateRule(models.Model):
    """Pricing rule engine input: seasonal date ranges, weekend premiums, promos."""

    class RuleType(models.TextChoices):
        SEASONAL = "seasonal", "Seasonal range"
        WEEKEND = "weekend", "Weekend premium (Fri–Sat)"
        PROMO = "promo", "Promotion / discount"

    name = models.CharField(max_length=120)
    rule_type = models.CharField(max_length=12, choices=RuleType.choices, default=RuleType.SEASONAL)
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="rate_rules",
        null=True, blank=True, help_text="Blank = chain-wide; set for one hotel",
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="rate_rules",
        null=True, blank=True, help_text="Blank = every room type in scope",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    multiplier = models.DecimalField(
        max_digits=5, decimal_places=3, validators=[MinValueValidator(Decimal("0.05"))],
        help_text="1.250 = +25%, 0.850 = −15%",
    )
    priority = models.PositiveSmallIntegerField(default=0, help_text="Higher wins on conflicts")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority", "start_date"]
        constraints = [
            models.CheckConstraint(check=models.Q(end_date__gte=models.F("start_date")), name="rate_rule_valid_range"),
        ]

    def __str__(self):
        scope = self.room_type.name if self.room_type else "All rooms"
        return f"{self.name} · {scope} · ×{self.multiplier}"


class Booking(models.Model):
    """A reservation: N rooms of one type for a date range. Source of truth for inventory."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked in"
        CHECKED_OUT = "checked_out", "Checked out"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No-show"

    class Source(models.TextChoices):
        WEB = "web", "Website"
        PHONE = "phone", "Phone"
        WALK_IN = "walk_in", "Walk-in"
        OTA = "ota", "OTA / Agency"

    # Inventory-blocking statuses (occupy rooms, count toward availability)
    ACTIVE_STATUSES = [Status.CONFIRMED, Status.CHECKED_IN]

    code = models.CharField(max_length=24, unique=True, blank=True)
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings",
        null=True, blank=True, help_text="Null for walk-in reservations",
    )
    guest_name = models.CharField(max_length=160)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=32, blank=True)

    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    rooms_count = models.PositiveSmallIntegerField(default=1)
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CONFIRMED)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.WEB)

    # Money snapshot (never recompute after booking — prices are contractual)
    currency = models.CharField(max_length=8, default="USD")
    nightly_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"), help_text="Welcome or promotion discount applied to room subtotal")
    service_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    rate_details = models.JSONField(default=list, blank=True, help_text="[{date, rate}] per night")

    cancellation_reason = models.TextField(blank=True)
    cancellation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    special_requests = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-check_in", "-created_at"]
        indexes = [
            models.Index(fields=["status", "check_in", "check_out"]),
            models.Index(fields=["room_type", "check_in", "check_out"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(check_out__gt=models.F("check_in")), name="booking_valid_range"),
        ]

    def __str__(self):
        return f"{self.code or 'draft'} · {self.room_type.name} · {self.check_in}→{self.check_out}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.code and self.pk:
            self.code = f"AG-{self.check_in.year}-{self.pk:06d}"
            super().save(update_fields=["code"])

    def get_absolute_url(self):
        return reverse("pms:booking_detail", args=[self.pk])

    # ---- derived properties -------------------------------------------------
    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_upcoming_arrival(self) -> bool:
        return self.status == self.Status.CONFIRMED and self.check_in >= timezone.localdate()

    @property
    def cancellation_deadline(self) -> date:
        return self.check_in - timedelta(days=self.room_type.cancellation_days)

    @property
    def is_free_cancellation(self) -> bool:
        return self.status == self.Status.CONFIRMED and timezone.localdate() <= self.cancellation_deadline

    @property
    def rate_details_parsed(self):
        return self.rate_details if isinstance(self.rate_details, list) else json.loads(self.rate_details or "[]")

    @property
    def assigned_rooms(self):
        cache = getattr(self, "_prefetched_objects_cache", {})
        if "room_assignments" in cache:
            # view prefetched the open assignments with their rooms
            return [a.room for a in cache["room_assignments"]]
        return [a.room for a in self.room_assignments.filter(released_at__isnull=True).select_related("room")]

    def status_tone(self) -> str:
        return {
            self.Status.CONFIRMED: "info",
            self.Status.CHECKED_IN: "success",
            self.Status.CHECKED_OUT: "muted",
            self.Status.CANCELLED: "danger",
            self.Status.NO_SHOW: "warning",
        }[self.status]


class RoomAssignment(models.Model):
    """Links a booking to specific physical rooms during a stay."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="room_assignments")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "room"],
                condition=models.Q(released_at__isnull=True),
                name="unique_active_assignment",
            )
        ]

    def __str__(self):
        return f"{self.room.number} → {self.booking.code}"
