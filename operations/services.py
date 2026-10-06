"""Housekeeping automation triggered by booking lifecycle events."""
from __future__ import annotations

from django.utils import timezone

from hotel.models import Room

from .models import HousekeepingTask


def _open_cleaning_task(room: Room):
    return room.housekeeping_tasks.filter(
        status__in=[HousekeepingTask.Status.PENDING, HousekeepingTask.Status.IN_PROGRESS]
    ).order_by("-priority", "created_at").first()


def ensure_dirty_room_task(room: Room, booking=None) -> HousekeepingTask | None:
    """Keep every dirty room connected to one visible cleaning workflow.

    A vacant-dirty room needs a check-out clean; an occupied-dirty room gets
    daily service.  Existing open work is reused so changing a room to dirty
    from the room board cannot create duplicate tasks.
    """
    if room.status not in (Room.Status.VACANT_DIRTY, Room.Status.OCCUPIED_DIRTY):
        return None

    is_checkout = room.status == Room.Status.VACANT_DIRTY
    task_type = (
        HousekeepingTask.TaskType.CHECKOUT_CLEAN
        if is_checkout else HousekeepingTask.TaskType.DAILY_SERVICE
    )
    priority = (
        HousekeepingTask.Priority.URGENT
        if is_checkout else HousekeepingTask.Priority.NORMAL
    )
    task = _open_cleaning_task(room)
    if task:
        # A room checked out while daily service was open must be promoted to
        # the urgent check-out workflow instead of receiving a duplicate card.
        updates = []
        if is_checkout and task.task_type != task_type:
            task.task_type = task_type
            updates.append("task_type")
        if is_checkout and task.priority != priority:
            task.priority = priority
            updates.append("priority")
        if booking and task.booking_id != booking.pk:
            task.booking = booking
            updates.append("booking")
        if updates:
            task.save(update_fields=updates)
        return task

    return HousekeepingTask.objects.create(
        room=room,
        booking=booking,
        task_type=task_type,
        priority=priority,
    )


def create_checkout_tasks(rooms: list[Room], booking=None) -> list[HousekeepingTask]:
    """Every checked-out room gets one urgent clean task."""
    return [
        ensure_dirty_room_task(room, booking=booking)
        for room in rooms
    ]


def complete_task(task: HousekeepingTask, user) -> HousekeepingTask:
    task.status = HousekeepingTask.Status.COMPLETED
    task.completed_at = timezone.now()
    if not task.assigned_to:
        task.assigned_to = user
    task.save(update_fields=["status", "completed_at", "assigned_to"])

    room = task.room
    # Business rule: finishing a clean of a vacant room returns it to sellable stock.
    if task.task_type in (
        HousekeepingTask.TaskType.CHECKOUT_CLEAN,
        HousekeepingTask.TaskType.DEEP_CLEAN,
        HousekeepingTask.TaskType.DAILY_SERVICE,
    ) and room.status == Room.Status.VACANT_DIRTY:
        room.status = Room.Status.VACANT_CLEAN
        room.save(update_fields=["status", "updated_at"])
    return task


def start_task(task: HousekeepingTask, user) -> HousekeepingTask:
    task.status = HousekeepingTask.Status.IN_PROGRESS
    task.started_at = timezone.now()
    task.assigned_to = user
    task.save(update_fields=["status", "started_at", "assigned_to"])
    return task


def generate_daily_service_tasks() -> int:
    """Nightly job: queue light service for every occupied room without a pending task."""
    created = 0
    occupied = Room.objects.filter(status__in=[Room.Status.OCCUPIED_CLEAN, Room.Status.OCCUPIED_DIRTY])
    for room in occupied:
        has_open = room.housekeeping_tasks.filter(
            status__in=[HousekeepingTask.Status.PENDING, HousekeepingTask.Status.IN_PROGRESS]
        ).exists()
        if not has_open:
            HousekeepingTask.objects.create(
                room=room,
                task_type=HousekeepingTask.TaskType.DAILY_SERVICE,
                priority=HousekeepingTask.Priority.NORMAL,
            )
            created += 1
    return created
