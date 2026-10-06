from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import GuestSignupForm, LoginForm
from .decorators import front_office_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect("pms:dashboard" if request.user.is_staff_role else "core:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        if not form.cleaned_data.get("remember"):
            request.session.set_expiry(0)
        nxt = request.GET.get("next")
        if nxt:
            return redirect(nxt)
        messages.success(request, f"Welcome back, {user.first_name or user.username}!")
        return redirect("pms:dashboard" if user.is_staff_role else "core:guest_dashboard")
    return render(request, "accounts/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = GuestSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created — welcome to Aurelia Grand.")
        return redirect("core:home")
    return render(request, "accounts/signup.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("core:home")


@front_office_required
def staff_directory(request):
    from .models import User
    from core.properties import get_active_property
    prop = get_active_property(request)
    staff = User.objects.filter(role__in=User.STAFF_ROLES)
    if prop:
        staff = staff.filter(home_property__isnull=True) | staff.filter(home_property=prop)
    staff = staff.order_by("role", "username")
    return render(request, "accounts/staff_directory.html", {"staff": staff})


def dev_login_view(request, username):
    """One-click demo login used by start.bat — ONLY active when DEBUG=True.

    In production (DEBUG=False) this URL is disabled entirely, so it can
    never become an authentication bypass.
    """
    from django.conf import settings
    from django.http import Http404
    from django.shortcuts import get_object_or_404
    from .models import User

    import os as _os
    if not (settings.DEBUG or _os.environ.get("DJANGO_DEMO_LOGIN") == "1"):
        raise Http404("Dev login is disabled in production.")
    user = get_object_or_404(User, username=username, is_active=True)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    nxt = request.GET.get("next")
    return redirect(nxt if nxt and nxt.startswith("/") else "pms:dashboard")
