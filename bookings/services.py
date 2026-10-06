"""
Booking domain services — the business-logic core.

Design rules:
  * Views never compute prices or availability directly; they call these functions.
  * All inventory mutations run inside a transaction with `select_for_update` on the
    RoomType row, which serialises concurrent bookings for the same type and makes
    double-booking impossible (row locks on Postgres; DB write lock on SQLite).
  * Prices are snapshotted onto the Booking at creation time — later rate changes
    never mutate existing reservations.
"""
from __future__ import annotations

import datetime as dt
import logging
import threading
from collections import defaultdict
from contextlib import nullcontext
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from hotel.models import Room, RoomType

from .models import Booking, RateRule, RoomAssignment

TWO_PLACES = Decimal("0.01")
MAX_STAY_NIGHTS = 30
WELCOME_DISCOUNT_RATE = Decimal("0.10")

logger = logging.getLogger("hotelops")

# Postgres serialises writers with SELECT ... FOR UPDATE on the inventory row.
# SQLite has no row locks, so we fall back to a process-level lock — together
# with its database write lock this keeps the check-then-insert atomic.
_SQLITE_INVENTORY_LOCK = threading.Lock()


def _inventory_lock():
    from django.db import connection
    return _SQLITE_INVENTORY_LOCK if connection.vendor == "sqlite" else nullcontext()


class BookingError(Exception):
    """Domain validation failure with a user-safe message."""


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Pricing engine
# --------------------------------------------------------------------------- #

def welcome_offer_eligible(user, source: str = Booking.Source.WEB) -> bool:
    """Return whether a registered guest can use the one-time 10% welcome offer."""
    if not user or not getattr(user, "is_authenticated", True):
        return False
    if source != Booking.Source.WEB or getattr(user, "role", "") != "guest":
        return False
    if not getattr(user, "email", "") or getattr(user, "welcome_offer_used", False):
        return False
    return not Booking.objects.filter(guest=user).exists()


def _rule_applies(rule, room_type: RoomType) -> bool:
    """Python mirror of applicable_rules_q for pre-fetched rule batches."""
    if rule.room_type_id is not None:
        return rule.room_type_id == room_type.pk
    if rule.property_id is not None:
        return rule.property_id == room_type.property_id
    return True


def nightly_rates(room_type: RoomType, check_in: dt.date, check_out: dt.date, rules=None) -> list[tuple[dt.date, Decimal]]:
    """Return [(night_date, rate)] applying seasonal/weekend/promo rules.

    Resolution per night:
      1. Start from the rack rate.
      2. Apply the highest-priority active SEASONAL/PROMO rule covering the night
         (room-specific beats property-wide at equal priority).
      3. Multiply by the best active WEEKEND rule if the night is Fri/Sat.
    """
    if rules is None:
        rules = list(
            RateRule.objects.filter(is_active=True, start_date__lt=check_out, end_date__gte=check_in)
            .filter(applicable_rules_q(room_type))
            .order_by("-priority", "start_date")
        )
    else:
        rules = [r for r in rules if _rule_applies(r, room_type)]
    out: list[tuple[dt.date, Decimal]] = []
    night = check_in
    base = Decimal(str(room_type.base_price))
    while night < check_out:
        rate = base
        for rule in rules:
            if rule.rule_type == RateRule.RuleType.WEEKEND:
                continue
            if rule.start_date <= night <= rule.end_date:
                rate = rate * Decimal(str(rule.multiplier))
                break  # highest-priority non-weekend rule wins
        if night.weekday() in (4, 5):  # Fri & Sat nights
            for rule in rules:
                if rule.rule_type == RateRule.RuleType.WEEKEND and rule.start_date <= night <= rule.end_date:
                    rate = rate * Decimal(str(rule.multiplier))
                    break
        out.append((night, _q(rate)))
        night += dt.timedelta(days=1)
    return out


def applicable_rules_q(room_type: RoomType):
    """Rule precedence scope: this room type > this property > whole chain."""
    from django.db.models import Q
    return (
        Q(room_type=room_type)
        | Q(room_type__isnull=True, property=room_type.property)
        | Q(room_type__isnull=True, property__isnull=True)
    )


def price_stay(room_type: RoomType, check_in: dt.date, check_out: dt.date, rooms: int = 1,
               rules=None, discount_rate: Decimal = Decimal("0")) -> dict:
    """Full price breakdown for a stay, before persistence.

    Discounts are applied to each contracted night before service and tax so
    the nightly snapshot, folio, cancellation fee, and displayed total agree.
    Existing callers default to no discount.
    """
    raw_nights = nightly_rates(room_type, check_in, check_out, rules=rules)
    discount_rate = max(Decimal("0"), min(Decimal(str(discount_rate)), Decimal("0.99")))
    nights = [(day, _q(rate * (Decimal("1") - discount_rate))) for day, rate in raw_nights]
    raw_per_room = sum((rate for _, rate in raw_nights), Decimal("0"))
    per_room = sum((rate for _, rate in nights), Decimal("0"))
    subtotal = _q(per_room * rooms)
    discount = _q((raw_per_room - per_room) * rooms)
    prop = room_type.property
    svc_rate = Decimal(str(prop.service_rate if prop else settings.HOTEL_SERVICE_RATE))
    tax_rate = Decimal(str(prop.tax_rate if prop else settings.HOTEL_TAX_RATE))
    service = _q(subtotal * svc_rate)
    tax = _q((subtotal + service) * tax_rate)
    total = _q(subtotal + service + tax)
    return {
        "nights": [{"date": d.isoformat(), "rate": str(r)} for d, r in nights],
        "night_count": len(nights),
        "per_room_total": _q(per_room),
        "rooms": rooms,
        "list_subtotal": _q(raw_per_room * rooms),
        "subtotal": subtotal,
        "discount": discount,
        "discount_rate": discount_rate,
        "service": service,
        "tax": tax,
        "total": total,
        "avg_nightly": _q(subtotal / max(len(nights) * rooms, 1)),
    }


# --------------------------------------------------------------------------- #
# Availability engine
# --------------------------------------------------------------------------- #

def _overlapping_bookings(room_type: RoomType, check_in: dt.date, check_out: dt.date,
                          exclude_booking_id: int | None = None):
    qs = Booking.objects.filter(
        room_type=room_type,
        status__in=Booking.ACTIVE_STATUSES,
        check_in__lt=check_out,   # overlap test on half-open [check_in, check_out)
        check_out__gt=check_in,
    )
    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)
    return qs


def booked_rooms(room_type: RoomType, check_in: dt.date, check_out: dt.date,
                 exclude_booking_id: int | None = None, overlaps=None) -> int:
    """Peak rooms of this type committed on any night of the range.

    `overlaps` may be a pre-fetched bulk_overlaps() batch (list of dicts with
    id/room_type_id/check_in/check_out/rooms_count) to avoid one query per type.
    """
    if overlaps is None:
        rows = _overlapping_bookings(room_type, check_in, check_out, exclude_booking_id).values(
            "check_in", "check_out", "rooms_count")
    else:
        rows = [r for r in overlaps
                if r["room_type_id"] == room_type.pk
                and (exclude_booking_id is None or r["id"] != exclude_booking_id)]
    per_night: defaultdict[dt.date, int] = defaultdict(int)
    for b in rows:
        night = max(b["check_in"], check_in)
        end = min(b["check_out"], check_out)
        while night < end:
            per_night[night] += b["rooms_count"]
            night += dt.timedelta(days=1)
    return max(per_night.values(), default=0)


def bulk_rate_rules(check_in: dt.date, check_out: dt.date) -> list:
    """All active rules overlapping the range, in precedence order (one query)."""
    return list(
        RateRule.objects.filter(is_active=True, start_date__lt=check_out, end_date__gte=check_in)
        .order_by("-priority", "start_date")
    )


def bulk_overlaps(check_in: dt.date, check_out: dt.date) -> list[dict]:
    """Every active booking overlapping the range, chain-wide (one query)."""
    return list(
        Booking.objects.filter(
            status__in=Booking.ACTIVE_STATUSES,
            check_in__lt=check_out, check_out__gt=check_in,
        ).values("id", "room_type_id", "check_in", "check_out", "rooms_count")
    )


def occupancy_series(start_day: dt.date, days: int, property=None) -> list[dict]:
    """Per-night occupancy for a span in TWO queries (vs 2 per day)."""
    rts = RoomType.objects.filter(is_active=True)
    if property:
        rts = rts.filter(property=property)
    total_rooms = rts.aggregate(n=Sum("total_rooms"))["n"] or 0
    end_day = start_day + dt.timedelta(days=days)
    rows = Booking.objects.filter(
        status__in=Booking.ACTIVE_STATUSES, check_in__lt=end_day, check_out__gt=start_day
    )
    if property:
        rows = rows.filter(room_type__property=property)
    per_night: defaultdict[dt.date, int] = defaultdict(int)
    for r in rows.values("check_in", "check_out", "rooms_count"):
        night = max(r["check_in"], start_day)
        end = min(r["check_out"], end_day)
        while night < end:
            per_night[night] += r["rooms_count"]
            night += dt.timedelta(days=1)
    out = []
    for i in range(days):
        day = start_day + dt.timedelta(days=i)
        occupied = min(per_night.get(day, 0), total_rooms)
        pct = round(occupied / total_rooms * 100, 1) if total_rooms else 0.0
        out.append({"day": day, "total": total_rooms, "occupied": occupied, "pct": pct})
    return out


def available_rooms(room_type: RoomType, check_in: dt.date, check_out: dt.date,
                    exclude_booking_id: int | None = None, overlaps=None) -> int:
    return max(room_type.total_rooms
               - booked_rooms(room_type, check_in, check_out, exclude_booking_id, overlaps=overlaps), 0)


def search_availability(check_in: dt.date, check_out: dt.date, adults: int = 1,
                        children: int = 0, rooms: int = 1, property=None) -> list[dict]:
    """Guest-facing search: sellable room types for the range, priced.
    `property` may be a Property instance or slug to scope one hotel."""
    from hotel.models import Property
    if isinstance(property, str):
        property = Property.objects.filter(slug=property).first()
    results = []
    guests = adults + children
    rts = RoomType.objects.filter(is_active=True).select_related("property").prefetch_related("amenities")
    if property:
        rts = rts.filter(property=property)
    rules = bulk_rate_rules(check_in, check_out)
    overlaps = bulk_overlaps(check_in, check_out)
    for rt in rts:
        if rt.max_guests * rooms < guests:
            continue
        avail = available_rooms(rt, check_in, check_out, overlaps=overlaps)
        if avail < rooms:
            continue
        pricing = price_stay(rt, check_in, check_out, rooms, rules=rules)
        results.append({"room_type": rt, "available": avail, "pricing": pricing})
    results.sort(key=lambda r: r["pricing"]["total"])
    return results


# --------------------------------------------------------------------------- #
# Booking lifecycle
# --------------------------------------------------------------------------- #

def validate_booking_request(room_type: RoomType, check_in: dt.date, check_out: dt.date,
                             rooms: int, adults: int, children: int,
                             exclude_booking_id: int | None = None) -> None:
    today = timezone.localdate()
    if check_out <= check_in:
        raise BookingError("Check-out must be after check-in.")
    if check_in < today:
        raise BookingError("Check-in date cannot be in the past.")
    if (check_out - check_in).days > MAX_STAY_NIGHTS:
        raise BookingError(f"Maximum stay length is {MAX_STAY_NIGHTS} nights.")
    if rooms < 1:
        raise BookingError("At least one room is required.")
    if adults < 1:
        raise BookingError("At least one adult is required.")
    if adults + children > room_type.max_guests * rooms:
        raise BookingError(
            f"{room_type.name} sleeps up to {room_type.max_guests} guests per room "
            f"({room_type.max_guests * rooms} for {rooms} rooms)."
        )


def create_booking(*, room_type: RoomType, check_in: dt.date, check_out: dt.date, rooms: int,
                   adults: int, children: int, guest=None, guest_name: str = "", guest_email: str = "",
                   guest_phone: str = "", source: str = Booking.Source.WEB,
                   special_requests: str = "", created_by=None) -> Booking:
    """Atomically validate + price + persist a reservation without double-booking."""
    validate_booking_request(room_type, check_in, check_out, rooms, adults, children)
    if not (guest_name or (guest and guest.get_full_name())):
        raise BookingError("Guest name is required.")

    with _inventory_lock(), transaction.atomic():
        # Lock the inventory row so concurrent requests for this type serialise.
        locked_rt = RoomType.objects.select_for_update().get(pk=room_type.pk)
        if not locked_rt.is_active:
            raise BookingError("This room type is no longer bookable.")
        validate_booking_request(locked_rt, check_in, check_out, rooms, adults, children)
        avail = available_rooms(locked_rt, check_in, check_out)
        if avail < rooms:
            raise BookingError(
                f"Only {avail} × {locked_rt.name} left for those dates." if avail
                else f"Sorry — {locked_rt.name} is fully booked for those dates."
            )
        locked_guest = guest
        if guest and getattr(guest, "pk", None):
            from accounts.models import User
            locked_guest = User.objects.select_for_update().get(pk=guest.pk)
        offer_applies = welcome_offer_eligible(locked_guest, source=source)
        pricing = price_stay(
            locked_rt, check_in, check_out, rooms,
            discount_rate=WELCOME_DISCOUNT_RATE if offer_applies else Decimal("0"),
        )
        name = guest_name or (locked_guest.get_full_name() if locked_guest else "")
        booking = Booking.objects.create(
            guest=locked_guest,
            guest_name=name,
            guest_email=guest_email or (locked_guest.email if locked_guest else ""),
            guest_phone=guest_phone or (getattr(locked_guest, "phone", "") or ""),
            room_type=locked_rt,
            check_in=check_in,
            check_out=check_out,
            rooms_count=rooms,
            adults=adults,
            children=children,
            source=source,
            special_requests=special_requests,
            currency=settings.HOTEL_CURRENCY,
            nightly_total=pricing["subtotal"],
            discount_total=pricing["discount"],
            service_total=pricing["service"],
            tax_total=pricing["tax"],
            grand_total=pricing["total"],
            rate_details=pricing["nights"],
            created_by=created_by,
            status=Booking.Status.CONFIRMED,
        )
        if offer_applies:
            locked_guest.welcome_offer_used = True
            locked_guest.save(update_fields=["welcome_offer_used"])

    from finance.services import ensure_invoice  # lazy import avoids app cycles
    ensure_invoice(booking)
    _notify_booking_created(booking)
    logger.info("booking.created code=%s type=%s nights=%s total=%s source=%s",
                booking.code, booking.room_type_id, booking.nights, booking.grand_total, booking.source)
    return booking


def cancellation_fee(booking: Booking) -> Decimal:
    """Free before the deadline; afterwards the first night's room charge is retained."""
    if booking.status != Booking.Status.CONFIRMED:
        raise BookingError("Only confirmed reservations can be cancelled.")
    if timezone.localdate() <= booking.cancellation_deadline:
        return Decimal("0.00")
    details = booking.rate_details_parsed
    first_night = Decimal(details[0]["rate"]) if details else booking.nightly_total / max(booking.nights, 1)
    return _q(first_night * booking.rooms_count)


def cancel_booking(booking: Booking, *, cancelled_by=None, reason: str = "") -> Booking:
    fee = cancellation_fee(booking)
    with transaction.atomic():
        locked = Booking.objects.select_for_update().get(pk=booking.pk)
        if locked.status != Booking.Status.CONFIRMED:
            raise BookingError("Only confirmed reservations can be cancelled.")
        locked.status = Booking.Status.CANCELLED
        locked.cancellation_reason = reason
        locked.cancellation_fee = fee
        locked.save(update_fields=["status", "cancellation_reason", "cancellation_fee", "updated_at"])

    from finance.services import process_cancellation  # lazy
    process_cancellation(locked, fee)
    _notify_booking_cancelled(locked, fee)
    logger.info("booking.cancelled code=%s fee=%s", locked.code, fee)
    return locked


def check_in_booking(booking: Booking, *, user, room_numbers: list[str]) -> Booking:
    """Front-desk check-in: assign physical rooms and flip their status."""
    today = timezone.localdate()
    with transaction.atomic():
        locked = Booking.objects.select_for_update().get(pk=booking.pk)
        if locked.status != Booking.Status.CONFIRMED:
            raise BookingError(f"Reservation is {locked.get_status_display().lower()} — cannot check in.")
        if locked.check_in > today:
            raise BookingError("Arrival date is in the future — cannot check in yet.")
        if len(set(room_numbers)) != locked.rooms_count:
            raise BookingError(f"Please assign exactly {locked.rooms_count} room(s).")

        rooms = list(
            Room.objects.select_for_update()
            .filter(number__in=room_numbers, room_type=locked.room_type)
        )
        if len(rooms) != locked.rooms_count:
            raise BookingError("One or more selected rooms do not exist or are of a different type.")
        for room in rooms:
            if room.status != Room.Status.VACANT_CLEAN:
                raise BookingError(
                    f"Room {room.number} is not ready ({room.get_status_display()}). "
                    "Pick a vacant & clean room."
                )
            room.status = Room.Status.OCCUPIED_CLEAN
            room.save(update_fields=["status", "updated_at"])
            RoomAssignment.objects.create(booking=locked, room=room, assigned_by=user)

        locked.status = Booking.Status.CHECKED_IN
        locked.save(update_fields=["status", "updated_at"])

    from finance.services import ensure_invoice
    ensure_invoice(locked)
    return locked


def check_out_booking(booking: Booking, *, user) -> Booking:
    """Check-out: release rooms, dirty them, queue housekeeping, settle the folio."""
    with transaction.atomic():
        locked = Booking.objects.select_for_update().get(pk=booking.pk)
        if locked.status != Booking.Status.CHECKED_IN:
            raise BookingError("Only checked-in reservations can be checked out.")

        assignments = locked.room_assignments.filter(released_at__isnull=True).select_related("room")
        rooms = [Room.objects.select_for_update().get(pk=a.room_id) for a in assignments]
        now = timezone.now()
        for assignment, room in zip(assignments, rooms):
            assignment.released_at = now
            assignment.save(update_fields=["released_at"])
            room.status = Room.Status.VACANT_DIRTY
            room.save(update_fields=["status", "updated_at"])

        locked.status = Booking.Status.CHECKED_OUT
        locked.save(update_fields=["status", "updated_at"])

    # Downstream automation: housekeeping + folio settlement.
    from operations.services import create_checkout_tasks
    create_checkout_tasks(rooms, booking=locked)
    from finance.services import settle_folio
    settle_folio(locked)
    _notify_checkout(locked)
    return locked


def mark_no_shows(as_of: dt.date | None = None) -> list[Booking]:
    """Automation: confirmed bookings whose arrival day has passed → no-show."""
    as_of = as_of or timezone.localdate()
    no_shows = []
    for booking in Booking.objects.filter(status=Booking.Status.CONFIRMED, check_in__lt=as_of):
        booking.status = Booking.Status.NO_SHOW
        booking.cancellation_reason = "Auto-marked no-show by nightly job."
        booking.save(update_fields=["status", "cancellation_reason", "updated_at"])
        no_shows.append(booking)
    return no_shows


# --------------------------------------------------------------------------- #
# Occupancy / reporting helpers (used by analytics + PMS dashboard)
# --------------------------------------------------------------------------- #

def occupancy_for_date(day: dt.date, property=None) -> dict:
    """Rooms occupied vs sellable on a given night, chain-wide or per property."""
    # Sellable stock = the same RoomType counter the availability engine enforces.
    rts = RoomType.objects.filter(is_active=True)
    if property:
        rts = rts.filter(property=property)
    total_rooms = rts.aggregate(n=Sum("total_rooms"))["n"] or 0
    occ = Booking.objects.filter(
        status__in=Booking.ACTIVE_STATUSES, check_in__lte=day, check_out__gt=day
    )
    if property:
        occ = occ.filter(room_type__property=property)
    occupied = occ.aggregate(n=Sum("rooms_count"))["n"] or 0
    pct = round(occupied / total_rooms * 100, 1) if total_rooms else 0.0
    return {"total": total_rooms, "occupied": min(occupied, total_rooms), "pct": pct}


# --------------------------------------------------------------------------- #
# Notifications (console email in dev; swap backend for SES/SMTP in prod)
# --------------------------------------------------------------------------- #

def _notify_booking_created(booking: Booking) -> None:
    from core.emails import send_booking_confirmation
    send_booking_confirmation(booking)


def _notify_booking_cancelled(booking: Booking, fee: Decimal) -> None:
    from core.emails import send_cancellation_notice
    send_cancellation_notice(booking, fee)


def _notify_checkout(booking: Booking) -> None:
    from core.emails import send_checkout_receipt
    send_checkout_receipt(booking)
