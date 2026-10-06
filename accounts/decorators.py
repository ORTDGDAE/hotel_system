from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import User


def staff_required(view_func):
    """Any hotel staff role (receptionist, housekeeping, manager, admin)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("accounts:login")
        if not user.is_staff_role:
            messages.error(request, "You do not have permission to access staff areas.")
            return redirect("core:home")
        if user.is_property_manager and not user.home_property_id:
            messages.error(request, "Your Property Manager account is not assigned to a hotel yet.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return _wrapped


def front_office_required(view_func):
    """Front-office and management pages; housekeeping stays on assigned work."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("accounts:login")
        if not user.is_staff_role:
            messages.error(request, "You do not have permission to access staff areas.")
            return redirect("core:home")
        if user.role == User.Role.HOUSEKEEPING:
            messages.info(request, "Housekeeping access is limited to your assigned tasks.")
            return redirect("operations:task_board")
        if user.is_property_manager and not user.home_property_id:
            messages.error(request, "Your Property Manager account is not assigned to a hotel yet.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return _wrapped


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("accounts:login")
        if not user.is_manager_or_above:
            messages.error(request, "Manager privileges required.")
            return redirect("pms:dashboard")
        if user.is_property_manager and not user.home_property_id:
            messages.error(request, "Your Property Manager account is not assigned to a hotel yet.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return _wrapped
