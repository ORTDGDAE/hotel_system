import datetime as dt
from calendar import monthrange
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import front_office_required, manager_required, staff_required
from finance.forms_helpers import payment_form_from_request
from finance.models import Invoice, Payment
from hotel.models import Property, Room, RoomType

from . import services
from .forms import (CheckInForm, GuestBookingForm, RateRuleForm, SearchForm,
                    StaffBookingForm)
from .models import Booking, RateRule
from .services import BookingError
from core.pagination import paginate
from core.properties import (get_active_property, properties_for_user,
                             scope_bookings, scope_rooms, set_active_property,
                             user_can_operate_property)
import uuid

# --------------------------------------------------------------------------- #
# Guest booking wizard
# --------------------------------------------------------------------------- #

@login_required
def book_room(request, slug):
    room_type = get_object_or_404(RoomType, slug=slug, is_active=True)
    today = timezone.localdate()

    # Idempotency: a double-clicked submit must never create two reservations.
    if request.method == "POST":
        token = request.POST.get("idem_token", "")
        done_pk = request.session.get(f"idem_done_{token}") if token else None
        if done_pk:
            messages.info(request, "That submission was already processed — here is your confirmation.")
            return redirect("bookings:confirmation", pk=done_pk)
        idem_token = token or uuid.uuid4().hex
    else:
        idem_token = request.session.setdefault("booking_token", uuid.uuid4().hex)

    def pdate(v, d):
        try:
            return dt.date.fromisoformat(v)
        except (TypeError, ValueError):
            return d

    check_in = pdate(request.GET.get("check_in") or request.POST.get("check_in"), today)
    check_out = pdate(request.GET.get("check_out") or request.POST.get("check_out"), today + dt.timedelta(days=1))
    rooms = max(int(request.GET.get("rooms") or request.POST.get("rooms") or 1), 1)
    adults = max(int(request.GET.get("adults") or request.POST.get("adults") or 2), 1)
    children = max(int(request.GET.get("children") or request.POST.get("children") or 0), 0)
    if check_in < today:
        check_in = today
    if check_out <= check_in:
        check_out = check_in + dt.timedelta(days=1)

    form = GuestBookingForm(request.POST or None, user=request.user)
    pricing = None
    welcome_discount = services.WELCOME_DISCOUNT_RATE if services.welcome_offer_eligible(request.user) else Decimal("0")
    avail = services.available_rooms(room_type, check_in, check_out)

    if request.method == "POST":
        try:
            services.validate_booking_request(room_type, check_in, check_out, rooms, adults, children)
            pricing = services.price_stay(room_type, check_in, check_out, rooms, discount_rate=welcome_discount)
        except BookingError as exc:
            messages.error(request, str(exc))
            return redirect("hotel:room_list")

        if form.is_valid():
            try:
                booking = services.create_booking(
                    room_type=room_type, check_in=check_in, check_out=check_out,
                    rooms=rooms, adults=adults, children=children,
                    guest=request.user,
                    guest_name=form.cleaned_data["guest_name"],
                    guest_email=form.cleaned_data["guest_email"],
                    guest_phone=form.cleaned_data.get("guest_phone", ""),
                    source=Booking.Source.WEB,
                    special_requests=form.cleaned_data.get("special_requests", ""),
                    created_by=request.user,
                )
            except BookingError as exc:
                messages.error(request, str(exc))
                pricing = services.price_stay(room_type, check_in, check_out, rooms, discount_rate=welcome_discount)
                return render(request, "bookings/book.html", _book_ctx(locals()))
            request.session[f"idem_done_{idem_token}"] = booking.pk
            request.session["booking_token"] = uuid.uuid4().hex  # rotate for next booking

            if form.cleaned_data.get("pay_now"):
                # Simulated payment gateway — swap for Stripe/Adyen SDK in production.
                from finance.services import record_payment
                record_payment(
                    booking, booking.grand_total,
                    method=form.cleaned_data.get("payment_method", "card"),
                    note="Prepaid at booking (simulated gateway)",
                    created_by=request.user,
                    reference=f"SIM-{booking.code}",
                )
            messages.success(request, f"Reservation {booking.code} confirmed!")
            return redirect("bookings:confirmation", pk=booking.pk)
    else:
        try:
            services.validate_booking_request(room_type, check_in, check_out, rooms, adults, children)
            pricing = services.price_stay(room_type, check_in, check_out, rooms, discount_rate=welcome_discount)
        except BookingError as exc:
            messages.error(request, str(exc))
            return redirect("hotel:room_list")

    return render(request, "bookings/book.html", _book_ctx(locals()))


def _book_ctx(ns: dict) -> dict:
    return {
        "room_type": ns["room_type"], "check_in": ns["check_in"], "check_out": ns["check_out"],
        "rooms": ns["rooms"], "adults": ns["adults"], "children": ns["children"],
        "pricing": ns["pricing"], "avail": ns["avail"], "form": ns["form"],
        "idem_token": ns["idem_token"],
    }


@login_required
def confirmation(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("room_type", "invoice"), pk=pk, guest=request.user
    )
    return render(request, "bookings/confirmation.html", {"booking": booking})


@login_required
@require_POST
def cancel_my_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, guest=request.user)
    try:
        fee = services.cancellation_fee(booking)
        services.cancel_booking(booking, cancelled_by=request.user, reason=request.POST.get("reason", "Cancelled by guest"))
        if fee > 0:
            messages.warning(request, f"Reservation cancelled. A fee of ${fee:,.2f} was retained per policy.")
        else:
            messages.success(request, "Reservation cancelled free of charge. Refund issued.")
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "core:guest_dashboard")


# --------------------------------------------------------------------------- #
# Staff PMS
# --------------------------------------------------------------------------- #

@front_office_required
def switch_property(request):
    """Set the hotel in this staff session, respecting role scope."""
    requested = request.GET.get("property") or "all"
    if request.user.is_property_manager:
        # Property managers are permanently tied to their assigned hotel.
        set_active_property(request, request.user.home_property_id)
        messages.info(request, "Property Manager view is fixed to your assigned hotel.")
    elif requested == "all":
        set_active_property(request, "all")
    else:
        prop = properties_for_user(request.user).filter(pk=requested).first()
        if not prop or not user_can_operate_property(request.user, prop):
            messages.error(request, "You cannot operate that hotel.")
        else:
            set_active_property(request, prop.pk)
    nxt = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/pms/"
    if not nxt.startswith("/"):
        nxt = "/pms/"
    return redirect(nxt)


def _staff_booking_queryset(request, queryset=None):
    prop = get_active_property(request)
    return scope_bookings(queryset or Booking.objects.all(), prop)


@front_office_required
def pms_dashboard(request):
    today = timezone.localdate()
    prop = get_active_property(request)
    from django.db.models import Prefetch
    from .models import RoomAssignment
    _open_assignments = Prefetch(
        "room_assignments",
        queryset=RoomAssignment.objects.filter(released_at__isnull=True).select_related("room"),
    )
    _board_qs = lambda qs: qs.select_related("room_type", "invoice").prefetch_related(
        _open_assignments, "invoice__payments")
    arrivals = _board_qs(scope_bookings(Booking.objects.filter(status=Booking.Status.CONFIRMED, check_in=today), prop))
    departures = _board_qs(scope_bookings(Booking.objects.filter(status=Booking.Status.CHECKED_IN, check_out=today), prop))
    in_house = _board_qs(scope_bookings(Booking.objects.filter(status=Booking.Status.CHECKED_IN), prop))
    occ = services.occupancy_for_date(today, prop)
    week_ago = today - dt.timedelta(days=6)
    revenue_week = (
        Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date__gte=week_ago)
        .aggregate(net=Sum("amount"))["net"] or Decimal("0")
    )
    if prop:
        revenue_week = (
            Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date__gte=week_ago,
                                   booking__room_type__property=prop)
            .aggregate(net=Sum("amount"))["net"] or Decimal("0")
        )
    from operations.models import HousekeepingTask
    dirty_rooms = scope_rooms(Room.objects.filter(status__in=[Room.Status.VACANT_DIRTY, Room.Status.OCCUPIED_DIRTY]), prop).count()
    open_task_qs = HousekeepingTask.objects.filter(status__in=["pending", "in_progress"])
    if prop:
        open_task_qs = open_task_qs.filter(room__room_type__property=prop)
    open_tasks = open_task_qs.count()
    recent = _board_qs(scope_bookings(Booking.objects.select_related("guest"), prop)).order_by("-created_at")[:8]
    return render(request, "pms/dashboard.html", {
        "today": today, "arrivals": arrivals, "departures": departures,
        "in_house": in_house, "occupancy": occ, "revenue_week": revenue_week,
        "dirty_rooms": dirty_rooms, "open_tasks": open_tasks, "recent": recent,
        "now": timezone.localtime(),
    })


@front_office_required
def reservations(request):
    prop = get_active_property(request)
    qs = scope_bookings(Booking.objects.select_related("room_type", "guest"), prop)
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(guest_name__icontains=q) | Q(guest_email__icontains=q))
    if date_from:
        qs = qs.filter(check_in__gte=date_from)
    if date_to:
        qs = qs.filter(check_out__lte=date_to)
    page, query = paginate(request, qs, 25)
    return render(request, "pms/reservations.html", {
        "bookings": page, "page": page, "query": query, "status": status, "q": q,
        "date_from": date_from, "date_to": date_to,
        "status_choices": Booking.Status.choices,
    })


@front_office_required
def reservation_detail(request, pk):
    booking = get_object_or_404(
        _staff_booking_queryset(
            request,
            Booking.objects.select_related("room_type", "guest", "invoice", "created_by"),
        ),
        pk=pk,
    )
    checkin_form = None
    if booking.status == Booking.Status.CONFIRMED and booking.check_in <= timezone.localdate():
        checkin_form = CheckInForm(booking=booking)
    free_rooms = Room.objects.filter(room_type=booking.room_type, status=Room.Status.VACANT_CLEAN).order_by("number")
    return render(request, "pms/booking_detail.html", {
        "booking": booking,
        "checkin_form": checkin_form,
        "free_rooms": free_rooms,
        "payments": booking.payments.all(),
        "invoice": getattr(booking, "invoice", None),
    })


@front_office_required
@require_POST
def reservation_check_in(request, pk):
    booking = get_object_or_404(_staff_booking_queryset(request), pk=pk)
    form = CheckInForm(request.POST, booking=booking)
    if form.is_valid():
        try:
            services.check_in_booking(booking, user=request.user,
                                      room_numbers=[r.number for r in form.cleaned_data["rooms"]])
            messages.success(request, f"{booking.guest_name} checked in to "
                                      f"{', '.join(r.number for r in form.cleaned_data['rooms'])}.")
            return redirect("pms:booking_detail", pk=pk)
        except BookingError as exc:
            messages.error(request, str(exc))
    else:
        for err in form.errors.get("rooms", form.errors.values()):
            messages.error(request, err if isinstance(err, str) else " ".join(err))
    return redirect("pms:booking_detail", pk=pk)


@front_office_required
@require_POST
def reservation_check_out(request, pk):
    booking = get_object_or_404(_staff_booking_queryset(request), pk=pk)
    try:
        services.check_out_booking(booking, user=request.user)
        invoice = getattr(booking, "invoice", None)
        messages.success(request, f"Checked out {booking.guest_name}."
                                  + (f" Folio {invoice.number} settled — ${invoice.paid_amount:,.2f} collected." if invoice else ""))
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect("pms:booking_detail", pk=pk)


@front_office_required
@require_POST
def reservation_cancel(request, pk):
    booking = get_object_or_404(_staff_booking_queryset(request), pk=pk)
    try:
        services.cancel_booking(booking, cancelled_by=request.user,
                                reason=request.POST.get("reason", "Cancelled by staff"))
        messages.success(request, f"Reservation {booking.code} cancelled; folio adjusted automatically.")
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect("pms:booking_detail", pk=pk)


@front_office_required
@require_POST
def reservation_payment(request, pk):
    from finance.services import record_payment
    booking = get_object_or_404(_staff_booking_queryset(request), pk=pk)
    form = payment_form_from_request(request)
    if form.is_valid():
        try:
            record_payment(
                booking, form.cleaned_data["amount"], form.cleaned_data["method"],
                note=form.cleaned_data.get("note", "Front-desk payment"), created_by=request.user,
            )
            messages.success(request, f"Payment of ${form.cleaned_data['amount']:,.2f} recorded.")
        except ValueError as exc:
            messages.error(request, str(exc))
    else:
        messages.error(request, "Invalid payment details.")
    return redirect("pms:booking_detail", pk=pk)


@front_office_required
def reservation_new(request):
    form = StaffBookingForm(request.POST or None)
    prop = get_active_property(request)
    if prop:
        form.fields["room_type"].queryset = RoomType.objects.filter(is_active=True, property=prop)
    preview = None
    if request.method == "POST":
        token = request.POST.get("idem_token", "")
        done_pk = request.session.get(f"idem_done_{token}") if token else None
        if done_pk:
            messages.info(request, "Duplicate submission ignored — reservation already created.")
            return redirect("pms:booking_detail", pk=done_pk)
        idem_token = token or uuid.uuid4().hex
    else:
        idem_token = request.session.setdefault("booking_token", uuid.uuid4().hex)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        rt = data["room_type"]
        try:
            services.validate_booking_request(rt, data["check_in"], data["check_out"],
                                              data["rooms_count"], data["adults"], data["children"])
            booking = services.create_booking(
                room_type=rt, check_in=data["check_in"], check_out=data["check_out"],
                rooms=data["rooms_count"], adults=data["adults"], children=data["children"],
                guest=data.get("guest"), guest_name=data["guest_name"],
                guest_email=data.get("guest_email", ""), guest_phone=data.get("guest_phone", ""),
                source=data["source"], special_requests=data.get("special_requests", ""),
                created_by=request.user,
            )
            request.session[f"idem_done_{idem_token}"] = booking.pk
            request.session["booking_token"] = uuid.uuid4().hex
            messages.success(request, f"Reservation {booking.code} created for {booking.guest_name}.")
            return redirect("pms:booking_detail", pk=booking.pk)
        except BookingError as exc:
            messages.error(request, str(exc))
    elif form.data:
        pass
    # live price preview for the currently selected params
    try:
        rt_id = request.GET.get("room_type") or (form.data.get("room_type") if form.data else None)
        ci = request.GET.get("check_in") or (form.data.get("check_in") if form.data else None)
        co = request.GET.get("check_out") or (form.data.get("check_out") if form.data else None)
        if rt_id and ci and co:
            rt_qs = RoomType.objects.filter(pk=rt_id, is_active=True)
            if prop:
                rt_qs = rt_qs.filter(property=prop)
            rt = rt_qs.get()
            preview = services.price_stay(rt, dt.date.fromisoformat(ci), dt.date.fromisoformat(co),
                                          int(request.GET.get("rooms") or form.data.get("rooms_count") or 1))
    except Exception:
        preview = None
    return render(request, "pms/booking_new.html", {"form": form, "preview": preview,
                                                    "room_types": RoomType.objects.filter(is_active=True),
                                                    "idem_token": idem_token})



from django.http import JsonResponse


def price_api(request):
    """JSON price preview for the staff new-booking form (staff-only)."""
    if not (request.user.is_authenticated and request.user.is_staff_role and request.user.role != request.user.Role.HOUSEKEEPING):
        return JsonResponse({"error": "auth"}, status=403)
    try:
        rt_qs = RoomType.objects.filter(pk=int(request.GET.get("room_type", 0)), is_active=True)
        prop = get_active_property(request)
        if prop:
            rt_qs = rt_qs.filter(property=prop)
        rt = rt_qs.get()
        ci = dt.date.fromisoformat(request.GET.get("check_in", ""))
        co = dt.date.fromisoformat(request.GET.get("check_out", ""))
        rooms = max(int(request.GET.get("rooms", 1)), 1)
        pricing = services.price_stay(rt, ci, co, rooms)
        return JsonResponse({
            "night_count": pricing["night_count"], "rooms": rooms,
            "subtotal": f"{pricing['subtotal']:,.2f}", "service": f"{pricing['service']:,.2f}",
            "tax": f"{pricing['tax']:,.2f}", "total": f"{pricing['total']:,.2f}",
            "available": services.available_rooms(rt, ci, co),
        })
    except Exception:
        return JsonResponse({"error": "invalid"}, status=400)


@front_office_required
def calendar(request):
    today = timezone.localdate()
    prop = get_active_property(request) or RoomType.objects.first().property
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    days_in_month = monthrange(year, month)[1]
    first = dt.date(year, month, 1)
    last = dt.date(year, month, days_in_month)

    bookings = Booking.objects.filter(
        status__in=Booking.ACTIVE_STATUSES, check_in__lte=last, check_out__gte=first,
        room_type__property=prop,
    ).select_related("room_type")

    total_sellable = sum(rt.total_rooms for rt in RoomType.objects.filter(is_active=True, property=prop)) or 1
    cells = []
    for d in range(1, days_in_month + 1):
        day = dt.date(year, month, d)
        arrivals = [b for b in bookings if b.check_in == day and b.status == Booking.Status.CONFIRMED]
        departures = [b for b in bookings if b.check_out == day and b.status == Booking.Status.CHECKED_IN]
        in_house = sum(b.rooms_count for b in bookings if b.check_in <= day < b.check_out)
        cells.append({
            "date": day, "arrivals": arrivals, "departures": departures,
            "in_house": in_house, "occ": round(in_house / total_sellable * 100),
            "is_today": day == today, "is_past": day < today,
        })
    # leading blanks for weekday alignment (Monday-first)
    lead = first.weekday()
    prev_month = (first - dt.timedelta(days=1))
    next_month = (last + dt.timedelta(days=1))
    return render(request, "pms/calendar.html", {
        "cells": cells, "lead": lead, "lead_range": range(lead), "year": year, "month": month,
        "month_name": first.strftime("%B %Y"),
        "prev": {"year": prev_month.year, "month": prev_month.month},
        "next": {"year": next_month.year, "month": next_month.month},
    })


@manager_required
def rates(request):
    from django.db.models import Q
    prop = get_active_property(request)
    rules = RateRule.objects.select_related("room_type", "property")
    rules = rules.filter(Q(property=prop) | Q(property__isnull=True)) if prop else rules.all()
    room_types = RoomType.objects.filter(is_active=True)
    if prop:
        room_types = room_types.filter(property=prop)
    form = RateRuleForm(request.POST or None, prefix="rule")
    if prop and not request.user.is_group_manager_or_above:
        form.fields["property"].queryset = Property.objects.filter(pk=prop.pk)
        form.fields["room_type"].queryset = RoomType.objects.filter(is_active=True, property=prop)
    if request.method == "POST" and form.is_valid():
        rule = form.save(commit=False)
        if prop and not rule.property:
            rule.property = prop
        rule.save()
        messages.success(request, f"Rate rule “{rule.name}” saved.")
        return redirect("pms:rates")
    return render(request, "pms/rates.html", {
        "rules": rules, "room_types": room_types, "form": form,
    })


@manager_required
@require_POST
def rate_rule_toggle(request, pk):
    rule = get_object_or_404(RateRule, pk=pk)
    prop = get_active_property(request)
    if prop and not request.user.is_group_manager_or_above and rule.property_id != prop.pk:
        messages.error(request, "You can only change pricing rules for your assigned hotel.")
        return redirect("pms:rates")
    rule.is_active = not rule.is_active
    rule.save(update_fields=["is_active"])
    messages.success(request, f"Rule “{rule.name}” {'activated' if rule.is_active else 'deactivated'}.")
    return redirect("pms:rates")


@manager_required
@require_POST
def rate_rule_delete(request, pk):
    rule = get_object_or_404(RateRule, pk=pk)
    prop = get_active_property(request)
    if prop and not request.user.is_group_manager_or_above and rule.property_id != prop.pk:
        messages.error(request, "You can only delete pricing rules for your assigned hotel.")
        return redirect("pms:rates")
    rule.delete()
    messages.success(request, "Rate rule deleted.")
    return redirect("pms:rates")
