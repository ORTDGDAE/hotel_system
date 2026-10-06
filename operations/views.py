import json
import time

from django.contrib import messages
from django.db.models import Max, Prefetch
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import front_office_required, staff_required
from accounts.models import User
from core.properties import get_active_property, scope_rooms
from hotel.models import Room

from . import services
from .models import HousekeepingTask, MaintenanceRequest


@front_office_required
def room_board(request):
    prop = get_active_property(request)
    open_tasks = HousekeepingTask.objects.filter(
        status__in=[HousekeepingTask.Status.PENDING, HousekeepingTask.Status.IN_PROGRESS]
    ).select_related("assigned_to", "booking")
    qs = scope_rooms(
        Room.objects.select_related("room_type").prefetch_related(
            Prefetch("housekeeping_tasks", queryset=open_tasks, to_attr="open_housekeeping_tasks")
        ),
        prop,
    ).all()
    status = request.GET.get("status", "")
    floor = request.GET.get("floor", "")
    if status:
        qs = qs.filter(status=status)
    if floor:
        qs = qs.filter(floor=floor)
    floors = sorted(Room.objects.values_list("floor", flat=True).distinct())
    rooms_by_floor = {}
    for room in qs:
        rooms_by_floor.setdefault(room.floor, []).append(room)
    counts = {}
    for choice, _ in Room.Status.choices:
        counts[choice] = scope_rooms(Room.objects.filter(status=choice), prop).count()
    return render(request, "operations/room_board.html", {
        "rooms_by_floor": rooms_by_floor, "floors": floors,
        "status": status, "floor": floor, "counts": counts,
        "status_choices": Room.Status.choices,
    })


@front_office_required
@require_POST
def room_status_update(request, pk):
    room_qs = Room.objects.all()
    prop = get_active_property(request)
    if prop:
        room_qs = room_qs.filter(room_type__property=prop)
    room = get_object_or_404(room_qs, pk=pk)
    new_status = request.POST.get("status")
    valid = {c[0] for c in Room.Status.choices}
    if new_status not in valid:
        messages.error(request, "Invalid status.")
        return redirect("operations:room_board")
    # Business rule: never override an occupied room from the board — use check-out.
    if room.status.startswith("occupied") and new_status not in (
        Room.Status.OCCUPIED_CLEAN, Room.Status.OCCUPIED_DIRTY, Room.Status.MAINTENANCE
    ):
        messages.error(request, f"Room {room.number} is occupied. Check the guest out first.")
        return redirect("operations:room_board")
    room.status = new_status
    room.save(update_fields=["status", "updated_at"])
    task = services.ensure_dirty_room_task(room)
    if task:
        assignment = (
            f" assigned to {task.assigned_to.get_full_name() or task.assigned_to.username}"
            if task.assigned_to else " awaiting manager assignment"
        )
        messages.success(
            request,
            f"Room {room.number} → {room.get_status_display()}. "
            f"Housekeeping task created or reused{assignment}.",
        )
    else:
        messages.success(request, f"Room {room.number} → {room.get_status_display()}.")
    return redirect("operations:room_board")


def _task_for_request(request, pk):
    """Load a task only from the property currently being operated."""
    task = get_object_or_404(
        HousekeepingTask.objects.select_related("room", "assigned_to", "booking", "room__room_type__property"),
        pk=pk,
    )
    prop = get_active_property(request)
    if prop and task.room.room_type.property_id != prop.pk:
        raise Http404("Task is outside the active property.")
    return task


def _can_operate_task(user, task):
    """Housekeeping operates only its assigned tasks; managers/admins override."""
    if user.is_manager_or_above:
        return True
    return user.role == User.Role.HOUSEKEEPING and task.assigned_to_id == user.pk


@staff_required
def task_board(request):
    prop = get_active_property(request)
    qs = HousekeepingTask.objects.select_related("room", "assigned_to", "booking", "room__room_type__property")
    if prop:
        qs = qs.filter(room__room_type__property=prop)
    is_housekeeping = request.user.role == User.Role.HOUSEKEEPING
    tab = request.GET.get("tab", "mine" if is_housekeeping else "open")
    if is_housekeeping:
        # Housekeeping sees only its own assigned work, never the unassigned queue
        # or another employee's workload.
        qs = qs.filter(assigned_to=request.user)
        if tab not in ("mine", "completed"):
            tab = "mine"
        if tab == "completed":
            qs = qs.filter(status="completed")
        else:
            qs = qs.filter(status__in=["pending", "in_progress"])
    elif tab == "open":
        qs = qs.filter(status__in=["pending", "in_progress"])
    elif tab == "completed":
        qs = qs.filter(status="completed")
    elif tab == "mine" and request.user.is_authenticated:
        qs = qs.filter(assigned_to=request.user, status__in=["pending", "in_progress"])
    pending = qs.filter(status="pending")
    in_progress = qs.filter(status="in_progress")
    completed = qs.filter(status="completed")[:20] if tab == "completed" else qs.filter(status="completed")[:8]
    housekeepers = User.objects.filter(role=User.Role.HOUSEKEEPING, is_active=True).select_related("home_property")
    if prop:
        housekeepers = housekeepers.filter(home_property__isnull=True) | housekeepers.filter(home_property=prop)
    return render(request, "operations/task_board.html", {
        "pending": pending, "in_progress": in_progress, "completed": completed, "tab": tab,
        "housekeepers": housekeepers.order_by("username"),
        "can_assign_tasks": request.user.is_manager_or_above,
        "can_operate_tasks": request.user.is_manager_or_above or is_housekeeping,
        "is_housekeeping": is_housekeeping,
    })


@staff_required
@require_POST
def task_assign(request, pk):
    task = _task_for_request(request, pk)
    if not request.user.is_manager_or_above:
        messages.error(request, "Only a Manager or Administrator can assign housekeeping tasks.")
        return redirect("operations:task_board")

    assignee_id = request.POST.get("assigned_to", "").strip()
    if not assignee_id:
        task.assigned_to = None
        task.save(update_fields=["assigned_to"])
        messages.success(request, f"Unassigned: {task}.")
        return redirect("operations:task_board")

    assignee = get_object_or_404(
        User.objects.filter(role=User.Role.HOUSEKEEPING, is_active=True).select_related("home_property"),
        pk=assignee_id,
    )
    prop = get_active_property(request)
    if prop and assignee.home_property_id not in (None, prop.pk):
        messages.error(request, "The selected housekeeper belongs to another property.")
        return redirect("operations:task_board")
    task.assigned_to = assignee
    task.save(update_fields=["assigned_to"])
    messages.success(request, f"Assigned {task} to {assignee.get_full_name() or assignee.username}.")
    return redirect("operations:task_board")


@staff_required
@require_POST
def task_start(request, pk):
    task = _task_for_request(request, pk)
    if not _can_operate_task(request.user, task):
        messages.error(request, "This task is assigned to another housekeeper.")
        return redirect("operations:task_board")
    if task.status == HousekeepingTask.Status.PENDING:
        services.start_task(task, request.user)
        messages.success(request, f"Started: {task}")
    return redirect("operations:task_board")


@staff_required
@require_POST
def task_complete(request, pk):
    task = _task_for_request(request, pk)
    if not _can_operate_task(request.user, task):
        messages.error(request, "This task is assigned to another housekeeper.")
        return redirect("operations:task_board")
    if task.status != HousekeepingTask.Status.COMPLETED:
        services.complete_task(task, request.user)
        messages.success(request, f"Completed: {task}. Room {task.room.number} returned to sellable stock."
                         if task.room.status == Room.Status.VACANT_CLEAN else f"Completed: {task}.")
    return redirect("operations:task_board")


@front_office_required
def maintenance_list(request):
    prop = get_active_property(request)
    items = MaintenanceRequest.objects.select_related("room", "reported_by")
    if prop:
        items = items.filter(room__room_type__property=prop)
    items = items.all()
    tab = request.GET.get("tab", "open")
    if tab == "open":
        items = items.exclude(status="resolved")
    rooms = scope_rooms(Room.objects.order_by("number"), prop)
    return render(request, "operations/maintenance.html", {
        "items": items, "tab": tab, "rooms": rooms,
        "severity_choices": MaintenanceRequest.Severity.choices,
    })


@front_office_required
@require_POST
def maintenance_create(request):
    room_qs = scope_rooms(Room.objects.all(), get_active_property(request))
    room = get_object_or_404(room_qs, pk=request.POST.get("room"))
    title = request.POST.get("title", "").strip()
    if not title:
        messages.error(request, "Title is required.")
        return redirect("operations:maintenance")
    item = MaintenanceRequest.objects.create(
        room=room, title=title,
        description=request.POST.get("description", ""),
        severity=request.POST.get("severity", "medium"),
        reported_by=request.user,
    )
    messages.success(request, f"Maintenance request logged for Room {room.number}."
                     + (" Room blocked from inventory." if item.severity in ("high", "critical") else ""))
    return redirect("operations:maintenance")


@front_office_required
@require_POST
def maintenance_resolve(request, pk):
    item_qs = MaintenanceRequest.objects.all()
    prop = get_active_property(request)
    if prop:
        item_qs = item_qs.filter(room__room_type__property=prop)
    item = get_object_or_404(item_qs, pk=pk)
    item.status = MaintenanceRequest.Status.RESOLVED
    item.save()
    messages.success(request, f"Resolved: {item.title} (Room {item.room.number}).")
    return redirect("operations:maintenance")


@front_office_required
def room_stream(request):
    """Server-Sent Events feed of live room-status changes.

    The server polls the rooms table signature every 2s and pushes the full
    board state when it changes; clients patch tiles in place (soft real-time
    with zero JS dependencies). At scale, swap the poll for a Channels/Redis
    pub-sub notification — the client contract stays identical.
    """
    # Keep the stream aligned with the board's active-property scope. The
    # board renders one property (or the whole chain), so the SSE payload must
    # never leak rooms from another property into the client-side patch loop.
    prop = get_active_property(request)
    rooms_qs = scope_rooms(Room.objects.all(), prop)

    def events():
        last = None
        while True:
            sig = rooms_qs.aggregate(m=Max("updated_at"))["m"]
            sig = sig.isoformat() if sig else ""
            if sig != last:
                rooms = [
                    {"id": r.pk, "number": r.number, "status": r.status,
                     "label": r.get_status_display(), "tone": r.status_tone()}
                    for r in rooms_qs
                ]
                yield "data: " + json.dumps(rooms) + "\n\n"
                last = sig
            time.sleep(2)

    response = StreamingHttpResponse(events(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
