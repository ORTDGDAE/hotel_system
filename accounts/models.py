from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with hotel roles driving RBAC across guest + staff apps."""

    class Role(models.TextChoices):
        GUEST = "guest", "Guest"
        RECEPTIONIST = "receptionist", "Receptionist"
        HOUSEKEEPING = "housekeeping", "Housekeeping"
        MANAGER = "manager", "Group Manager"
        PROPERTY_MANAGER = "property_manager", "Property Manager"
        ADMIN = "admin", "Administrator"

    STAFF_ROLES = {Role.RECEPTIONIST, Role.HOUSEKEEPING, Role.MANAGER, Role.PROPERTY_MANAGER, Role.ADMIN}

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.GUEST)
    home_property = models.ForeignKey(
        "hotel.Property", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="staff", help_text="Home hotel for staff; blank = chain-wide (head office)",
    )
    phone = models.CharField(max_length=32, blank=True)
    avatar_initials = models.CharField(max_length=4, blank=True)
    welcome_offer_used = models.BooleanField(default=False, help_text="10% first-stay welcome offer has been consumed")

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_staff_role(self) -> bool:
        return self.role in self.STAFF_ROLES

    @property
    def is_manager_or_above(self) -> bool:
        return self.role in {self.Role.MANAGER, self.Role.PROPERTY_MANAGER, self.Role.ADMIN}

    @property
    def is_group_manager_or_above(self) -> bool:
        """Can operate across the full hotel collection."""
        return self.role in {self.Role.MANAGER, self.Role.ADMIN}

    @property
    def is_property_manager(self) -> bool:
        return self.role == self.Role.PROPERTY_MANAGER

    def save(self, *args, **kwargs):
        if not self.avatar_initials:
            name = self.get_full_name() or self.username
            parts = [p for p in name.split() if p]
            self.avatar_initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
        super().save(*args, **kwargs)
