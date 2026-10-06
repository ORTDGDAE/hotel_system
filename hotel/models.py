from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS-84 points, in kilometres."""
    from math import asin, cos, radians, sin, sqrt
    p1, p2 = radians(lat1), radians(lat2)
    dp = p2 - p1
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(a))


class Property(models.Model):
    """A physical hotel in the collection. Inventory, pricing taxes and PMS
    scoping all hang off this model — the platform is multi-property native."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=160, blank=True)
    vibe_tags = models.CharField(max_length=160, blank=True, default="",
                                 help_text="Comma-separated destination categories, e.g. 'Temples, History, Culture'")
    description = models.TextField(blank=True)
    city = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default="Cambodia")
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    stars = models.PositiveSmallIntegerField(default=5, choices=[(i, f"{i}★") for i in range(3, 6)])
    currency = models.CharField(max_length=8, default="USD")
    service_rate = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal("0.000"),
                                       help_text="Service charge; default 0% because the Cambodia demo uses tax only")
    tax_rate = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal("0.050"),
                                   help_text="VAT/GST, e.g. 0.050 = 5%")
    check_in_hour = models.PositiveSmallIntegerField(default=14)
    check_out_hour = models.PositiveSmallIntegerField(default=12)
    image_url = models.URLField(blank=True)
    latitude = models.FloatField(null=True, blank=True, help_text="WGS-84 decimal degrees (Google Maps source)")
    longitude = models.FloatField(null=True, blank=True, help_text="WGS-84 decimal degrees (Google Maps source)")
    is_active = models.BooleanField(default=True)

    @property
    def maps_url(self) -> str:
        """Key-free Google Maps browser/app link for this property's pin."""
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude:.5f},{self.longitude:.5f}"
        return ""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "properties"

    def __str__(self):
        return f"{self.name} · {self.city}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def vibe_list(self):
        return [t.strip() for t in self.vibe_tags.split(",") if t.strip()]

    def sellable_rooms(self) -> int:
        if hasattr(self, "sellable_ann"):  # list views annotate this
            return self.sellable_ann
        return self.rooms.exclude(status__in=Room.BLOCKED_STATUSES).count()

    @property
    def from_price(self):
        if hasattr(self, "from_price_ann"):  # list views annotate this
            return self.from_price_ann
        from django.db.models import Min
        return self.room_types.filter(is_active=True).aggregate(m=Min("base_price"))["m"]


class Amenity(models.Model):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, default="ri-vip-diamond-line", help_text="Remix Icon class shown in UI")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "amenities"

    def __str__(self):
        return self.name


class RoomType(models.Model):
    """Sellable inventory class (e.g. Deluxe King). `total_rooms` = sellable count."""

    class BedType(models.TextChoices):
        KING = "king", "1 King Bed"
        TWIN = "twin", "2 Twin Beds"
        DOUBLE = "double", "1 Double Bed"
        SUITE = "suite", "King + Living Area"

    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="room_types")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Nightly rack rate before rules/taxes.",
    )
    max_guests = models.PositiveSmallIntegerField(default=2)
    total_rooms = models.PositiveSmallIntegerField(default=1, help_text="Physical inventory of this type")
    size_sqm = models.PositiveSmallIntegerField(default=30)
    floor_range = models.CharField(max_length=32, blank=True, help_text="e.g. 3–8")
    bed_type = models.CharField(max_length=16, choices=BedType.choices, default=BedType.KING)
    amenities = models.ManyToManyField(Amenity, blank=True)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    cancellation_days = models.PositiveSmallIntegerField(
        default=2, help_text="Free cancellation up to N days before arrival"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["base_price", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("hotel:room_detail", args=[self.slug])



class Room(models.Model):
    """A physical room. Status is the housekeeping/front-desk state machine."""

    class Status(models.TextChoices):
        VACANT_CLEAN = "vacant_clean", "Vacant · Clean"
        VACANT_DIRTY = "vacant_dirty", "Vacant · Dirty"
        OCCUPIED_CLEAN = "occupied_clean", "Occupied · Clean"
        OCCUPIED_DIRTY = "occupied_dirty", "Occupied · Dirty"
        MAINTENANCE = "maintenance", "Under Maintenance"
        OUT_OF_ORDER = "out_of_order", "Out of Order"

    BLOCKED_STATUSES = {Status.MAINTENANCE, Status.OUT_OF_ORDER}

    number = models.CharField(max_length=12, help_text="Unique within its property")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="rooms",
                                 null=True, blank=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="room_set")
    floor = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VACANT_CLEAN)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["floor", "number"]
        constraints = [
            models.UniqueConstraint(fields=["property", "number"], name="unique_room_number_per_property"),
        ]

    def __str__(self):
        return f"{self.property.slug[:4] if self.property else ''} Room {self.number} · {self.room_type.name}"

    def save(self, *args, **kwargs):
        if not self.property_id:
            self.property = self.room_type.property
        super().save(*args, **kwargs)

    def is_sellable(self) -> bool:
        return self.status not in self.BLOCKED_STATUSES

    def status_tone(self) -> str:
        return {
            self.Status.VACANT_CLEAN: "success",
            self.Status.VACANT_DIRTY: "warning",
            self.Status.OCCUPIED_CLEAN: "info",
            self.Status.OCCUPIED_DIRTY: "warning",
            self.Status.MAINTENANCE: "danger",
            self.Status.OUT_OF_ORDER: "danger",
        }[self.status]


class Attraction(models.Model):
    """A top nearby thing-to-do for a property (sourced from Booking.com's
    destination attraction data; blurbs are original)."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="attractions")
    name = models.CharField(max_length=120)
    blurb = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=40, default="ri-map-pin-2-line")
    distance = models.CharField(max_length=24, blank=True)
    sort = models.PositiveSmallIntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def distance_km(self):
        """Auto-computed haversine distance from the parent property (km).
        Plain method on purpose: the FK field named `property` shadows the
        built-in `property` decorator inside this class body."""
        p = self.property
        if None in (self.latitude, self.longitude, p.latitude, p.longitude):
            return None
        return haversine_km(p.latitude, p.longitude, self.latitude, self.longitude)

    def maps_url(self) -> str:
        """Key-free Google Maps browser/app link for this attraction.

        This remains a plain method because the model's ForeignKey named
        `property` shadows Python's built-in `property` decorator.
        """
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude:.5f},{self.longitude:.5f}"
        return ""

    def distance_label(self) -> str:
        """Human chip text: metres under 1 km, else one-decimal kilometres."""
        d = self.distance_km()
        if d is None:
            return ""
        if d < 1:
            return f"{max(int(round(d * 1000)), 50)} m from hotel"
        return f"{d:.1f} km from hotel"

    class Meta:
        ordering = ["sort", "name"]

    def __str__(self):
        return f"{self.name} ({self.property.slug})"
