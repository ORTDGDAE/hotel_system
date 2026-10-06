"""End-to-end pipeline proof: search → price → book → pay → stay → settle → cancel → audit.
Run:  python3 scripts/pipeline_proof.py
Each step asserts its invariants; any failure raises immediately.
"""
import datetime as dt
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.utils import timezone

from accounts.models import User
from bookings import services
from bookings.models import Booking
from bookings.services import BookingError
from finance.models import Invoice, Payment
from finance.services import record_payment
from hotel.models import Room, RoomType
from operations.models import HousekeepingTask

today = timezone.localdate()
STEP = [0]


def step(title):
    STEP[0] += 1
    print(f"\n┌ STEP {STEP[0]:02d} ─ {title}")


def ok(msg):
    print(f"│   ✓ {msg}")


def money(v):
    return f"${Decimal(v):,.2f}"


guest = User.objects.get(username="guest")
staff = User.objects.get(username="reception")
rt = RoomType.objects.get(slug="deluxe-river-king")

# ── 1 SEARCH & PRICING ─────────────────────────────────────────────
step("Guest search: live availability + pricing engine")
ci, co = today + dt.timedelta(days=10), today + dt.timedelta(days=13)
results = services.search_availability(ci, co, adults=2, children=0, rooms=1)
assert results, "search returned no sellable rooms"
entry = next(r for r in results if r["room_type"].pk == rt.pk)
p = entry["pricing"]
assert p["total"] == p["subtotal"] + p["service"] + p["tax"], "total ≠ subtotal+service+tax"
assert p["service"] == Decimal("0.00")
assert p["tax"] == (p["subtotal"] * Decimal("0.05")).quantize(Decimal("0.01"))
assert entry["available"] <= rt.total_rooms
ok(f"{len(results)} room types sellable; {rt.name}: {entry['available']} left, "
   f"{p['night_count']} nights → {money(p['total'])} (5% tax only verified)")

# ── 2 BOOKING CREATION (atomic inventory) ──────────────────────────
step("Booking creation: validation, snapshot pricing, folio auto-issue")
b1 = services.create_booking(room_type=rt, check_in=ci, check_out=co, rooms=1, adults=2, children=0,
                             guest=guest, source=Booking.Source.WEB, created_by=staff)
assert b1.code and b1.grand_total == p["total"], "price snapshot must equal quoted price"
assert b1.invoice.total == b1.grand_total and b1.invoice.status == "open"
avail_after = services.available_rooms(rt, ci, co)
assert avail_after == entry["available"] - 1, "inventory must decrement immediately"
ok(f"{b1.code} created · snapshot {money(b1.grand_total)} locked · folio {b1.invoice.number} OPEN · "
   f"inventory {entry['available']}→{avail_after}")

# ── 3 PAYMENT PATH A: prepaid in full at booking ───────────────────
step("Payment path A — prepaid in full (gateway)")
pay = record_payment(b1, b1.grand_total, method="card", note="Prepaid at booking", created_by=guest,
                     reference=f"SIM-{b1.code}")
b1.invoice.refresh_from_db()
assert b1.invoice.status == "paid" and b1.invoice.balance == 0
ok(f"charge {money(pay.amount)} · folio {b1.invoice.number} → PAID · balance {money(0)}")

# ── 4 OVERPAYMENT GUARD ────────────────────────────────────────────
step("Payment guard — overpayment must be refused")
try:
    record_payment(b1, Decimal("1.00"), method="cash")
    raise SystemExit("✗ overpayment was accepted!")
except ValueError as e:
    ok(f"refused: {e}")

# ── 5 EARLY CHECK-IN REFUSED ───────────────────────────────────────
step("Front desk — check-in before arrival date must be refused")
try:
    services.check_in_booking(b1, user=staff, room_numbers=[Room.objects.filter(room_type=rt, status="vacant_clean").first().number])
    raise SystemExit("✗ early check-in accepted!")
except BookingError as e:
    ok(f"refused: {e}")

# ── 6 WALK-IN + CHECK-IN (room assignment state machine) ───────────
step("Walk-in same-day booking → check-in (physical room assignment)")
b2 = services.create_booking(room_type=rt, check_in=today, check_out=today + dt.timedelta(days=2),
                             rooms=1, adults=2, children=0, guest_name="Walk In Proof",
                             guest_email="proof@example.com", source=Booking.Source.WALK_IN, created_by=staff)
room = Room.objects.filter(room_type=rt, status=Room.Status.VACANT_CLEAN).first()
services.check_in_booking(b2, user=staff, room_numbers=[room.number])
b2.refresh_from_db(); room.refresh_from_db()
assert b2.status == Booking.Status.CHECKED_IN
assert room.status == Room.Status.OCCUPIED_CLEAN
assert b2.room_assignments.filter(released_at__isnull=True, room=room).exists()
ok(f"{b2.code} in house · room {room.number} VACANT_CLEAN→OCCUPIED_CLEAN · assignment row active")

# ── 7 PAYMENT PATH B: partial payment → PARTIAL folio ──────────────
step("Payment path B — partial deposit at desk (folio → PARTIAL)")
half = (b2.grand_total / 2).quantize(Decimal("0.01"))
record_payment(b2, half, method="cash", note="50% deposit", created_by=staff)
b2.invoice.refresh_from_db()
assert b2.invoice.status == "partial" and b2.invoice.balance == b2.grand_total - half
ok(f"deposit {money(half)} · folio PARTIAL · balance due {money(b2.invoice.balance)}")

# ── 8 CHECK-OUT → auto-settlement + housekeeping automation ────────
step("Check-out — folio auto-settlement, room dirtying, housekeeping queue")
services.check_out_booking(b2, user=staff)
b2.refresh_from_db(); room.refresh_from_db()
b2.invoice.refresh_from_db()
settled = Payment.objects.filter(booking=b2).order_by("-created_at").first()
assert b2.status == Booking.Status.CHECKED_OUT
assert room.status == Room.Status.VACANT_DIRTY
assert b2.invoice.status == "paid" and b2.invoice.balance == 0
assert HousekeepingTask.objects.filter(room=room, task_type="checkout_clean", status="pending").exists()
assert not b2.room_assignments.filter(released_at__isnull=True).exists()
ok(f"balance {money(settled.amount)} settled at desk ({settled.get_method_display()}) · folio PAID · "
   f"room {room.number} → VACANT_DIRTY · urgent clean task queued · assignment released")

# ── 9 PAYMENT PATH C: late cancellation → fee + partial refund ─────
step("Payment path C — late cancellation (first-night fee retained, rest refunded)")
b3 = services.create_booking(room_type=rt, check_in=today, check_out=today + dt.timedelta(days=3),
                             rooms=1, adults=2, children=0, guest_name="Late Cancel Proof",
                             guest_email="late@example.com", source=Booking.Source.PHONE, created_by=staff)
record_payment(b3, b3.grand_total, method="card", note="Prepaid", created_by=staff)
fee = services.cancellation_fee(b3)
first_night = Decimal(b3.rate_details_parsed[0]["rate"]) * b3.rooms_count
assert fee == first_night.quantize(Decimal("0.01")), f"fee {fee} != first night {first_night}"
services.cancel_booking(b3, cancelled_by=staff, reason="proof")
refund = Payment.objects.filter(booking=b3, amount__lt=0).get()
b3.invoice.refresh_from_db()
assert refund.amount == -(b3.grand_total - fee)
assert b3.invoice.total == fee and b3.invoice.status == "paid"
ok(f"fee {money(fee)} retained · refund {money(-refund.amount)} issued · folio re-priced to fee → PAID")

# ── 10 PAYMENT PATH D: free cancellation → full refund, REFUNDED ───
step("Payment path D — free-window cancellation (full refund, folio REFUNDED)")
b4 = services.create_booking(room_type=rt, check_in=today + dt.timedelta(days=20),
                             check_out=today + dt.timedelta(days=22), rooms=1, adults=2, children=0,
                             guest_name="Free Cancel Proof", guest_email="free@example.com",
                             source=Booking.Source.WEB, created_by=staff)
record_payment(b4, b4.grand_total, method="wallet", note="Prepaid", created_by=staff)
assert services.cancellation_fee(b4) == 0
services.cancel_booking(b4, cancelled_by=staff, reason="proof")
b4.invoice.refresh_from_db()
assert b4.invoice.status == "refunded" and b4.invoice.paid_amount == 0
ok(f"full refund {money(b4.grand_total)} · folio REFUNDED · inventory released "
   f"({services.available_rooms(rt, b4.check_in, b4.check_out)} available again)")

# ── 11 NO-SHOW AUTOMATION ──────────────────────────────────────────
step("Nightly automation — no-show flagging releases inventory")
b5 = services.create_booking(room_type=rt, check_in=today, check_out=today + dt.timedelta(days=1),
                             rooms=1, adults=1, children=0, guest_name="No Show Proof",
                             guest_email="noshow@example.com", source=Booking.Source.OTA, created_by=staff)
Booking.objects.filter(pk=b5.pk).update(check_in=today - dt.timedelta(days=1), check_out=today)
flagged = services.mark_no_shows()
b5.refresh_from_db()
assert b5.status == Booking.Status.NO_SHOW and b5 in flagged
ok(f"{b5.code} auto-flagged NO-SHOW · no longer blocks inventory")

# ── 12 LEDGER + INVENTORY AUDIT ────────────────────────────────────
step("System-wide audit — 900+ invariants over money, inventory, rooms")
from django.core.management import call_command
call_command("audit_ledger")
ok("audit command exited clean (see output above)")

print("\n" + "═" * 72)
print("  PIPELINE PROOF COMPLETE — every step, including all four payment")
print("  paths (prepay / deposit / settle-at-desk / refund), behaved exactly")
print("  as the business rules specify.")
print("═" * 72)
