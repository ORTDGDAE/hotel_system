from django.conf import settings
from django.db import models
from django.utils import timezone

from bookings.models import Booking
from hotel.models import Room


class HousekeepingTask(models.Model):
    class TaskType(models.TextChoices):
        CHECKOUT_CLEAN = "checkout_clean", "Check-out clean"
        DAILY_SERVICE = "daily_service", "Daily service"
        DEEP_CLEAN = "deep_clean", "Deep clean"
        INSPECTION = "inspection", "Inspection"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="housekeeping_tasks")
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    task_type = models.CharField(max_length=16, choices=TaskType.choices, default=TaskType.CHECKOUT_CLEAN)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-priority", "created_at"]
        indexes = [models.Index(fields=["status", "task_type"])]

    def __str__(self):
        return f"{self.get_task_type_display()} · Room {self.room.number}"

    def priority_rank(self) -> int:
        return {"urgent": 3, "high": 2, "normal": 1, "low": 0}[self.priority]

    @property
    def status_tone(self) -> str:
        return {self.Status.PENDING: "warning", self.Status.IN_PROGRESS: "info", self.Status.COMPLETED: "success"}[self.status]


class MaintenanceRequest(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="maintenance_requests")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} · Room {self.room.number}"

    @property
    def status_tone(self) -> str:
        return {self.Status.OPEN: "danger", self.Status.IN_PROGRESS: "warning", self.Status.RESOLVED: "success"}[self.status]

    def save(self, *args, **kwargs):
        # Business rule: critical/high maintenance blocks the room from selling.
        super().save(*args, **kwargs)
        room = self.room
        if self.status == self.Status.RESOLVED:
            if room.status == Room.Status.MAINTENANCE and not self._has_open_siblings():
                room.status = Room.Status.VACANT_DIRTY
                room.save(update_fields=["status", "updated_at"])
                self.completed_at = timezone.now()
        elif self.severity in (self.Severity.HIGH, self.Severity.CRITICAL):
            if room.status not in Room.BLOCKED_STATUSES and not room.status.startswith("occupied"):
                room.status = Room.Status.MAINTENANCE
                room.save(update_fields=["status", "updated_at"])

    def _has_open_siblings(self) -> bool:
        return (
            MaintenanceRequest.objects.filter(room=self.room, status=self.Status.OPEN)
            .exclude(pk=self.pk)
            .exists()
        )
