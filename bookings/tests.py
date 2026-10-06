"""Business-logic tests: pricing, availability, lifecycle, cancellation, concurrency."""
import datetime as dt
from decimal import Decimal

from concurrent.futures import ThreadPoolExecutor

from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import User
from hotel.models import Property, Room, RoomType

from . import services
from .forms import GuestBookingForm
from .models import Booking, RateRule
from .services import BookingError


def make_property(name="Test Hotel", **kw):
    return Property.objects.create(name=name, city="Testville", country="Testland",
                                   slug=f"test-{Property.objects.count()}-{name.split()[-1].lower()}", **kw)


def make_type(name="Deluxe", price="100.00", total=3, **kw):
    prop = kw.pop("property", None) or Property.objects.first() or make_property()
    return RoomType.objects.create(property=prop, name=name, base_price=Decimal(price),
                                   total_rooms=total, **kw)


class GuestBookingFormTests(TestCase):
    def base_data(self, **overrides):
        data = {
            "guest_name": "Sokha Chan",
            "guest_email": "sokha.chan@example.com",
            "guest_phone": "+855 12 345 678",
            "special_requests": "",
            "pay_now": "on",
            "payment_method": "card",
        }
        data.update(overrides)
        return data

    def test_phone_number_is_required(self):
        form = GuestBookingForm(data=self.base_data(guest_phone=""))
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["guest_phone"])

    def test_phone_number_accepts_international_format(self):
        form = GuestBookingForm(data=self.base_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_number_rejects_letters(self):
        form = GuestBookingForm(data=self.base_data(guest_phone="call me"))
        self.assertFalse(form.is_valid())
        self.assertIn("guest_phone", form.errors)


class PricingTests(TestCase):
    def setUp(self):
        self.rt = make_type(price="100.00")
        self.today = timezone.localdate()

    def test_flat_rates_and_totals(self):
        # Pick a Mon→Thu window (3 nights, no weekend nights)
        monday = self.today + dt.timedelta(days=(7 - self.today.weekday()) % 7)
        p = services.price_stay(self.rt, monday, monday + dt.timedelta(days=3), rooms=2)
        self.assertEqual(p["subtotal"], Decimal("600.00"))          # 100 × 3 × 2
        self.assertEqual(p["service"], Decimal("0.00"))             # tax-only pricing
        self.assertEqual(p["tax"], Decimal("30.00"))                # 5% of 600
        self.assertEqual(p["total"], Decimal("630.00"))
        self.assertEqual(p["night_count"], 3)

    def test_weekend_premium(self):
        saturday = self.today + dt.timedelta(days=(5 - self.today.weekday()) % 7)
        RateRule.objects.create(name="WK", rule_type="weekend", start_date=saturday - dt.timedelta(days=1),
                                end_date=saturday + dt.timedelta(days=30), multiplier=Decimal("1.2"))
        rates = dict(services.nightly_rates(self.rt, saturday, saturday + dt.timedelta(days=2)))
        self.assertEqual(rates[saturday], Decimal("120.00"))        # Sat night premium
        self.assertEqual(rates[saturday + dt.timedelta(days=1)], Decimal("100.00"))  # Sun night flat

    def test_seasonal_beats_lower_priority(self):
        start = self.today + dt.timedelta(days=10)
        RateRule.objects.create(name="Low", rule_type="seasonal", start_date=start,
                                end_date=start + dt.timedelta(days=5), multiplier=Decimal("1.1"), priority=1)
        RateRule.objects.create(name="High", rule_type="seasonal", start_date=start,
                                end_date=start + dt.timedelta(days=5), multiplier=Decimal("1.5"), priority=10)
        rates = dict(services.nightly_rates(self.rt, start, start + dt.timedelta(days=2)))
        self.assertTrue(all(v == Decimal("150.00") for v in rates.values()))


class WelcomeOfferTests(TestCase):
    def setUp(self):
        self.rt = make_type(price="100.00", total=3)
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            "new-guest", password="x", role="guest", email="new@example.com",
            first_name="New", last_name="Guest",
        )

    def test_registered_guest_gets_one_time_ten_percent_offer(self):
        first = services.create_booking(
            room_type=self.rt, check_in=self.today + dt.timedelta(days=5),
            check_out=self.today + dt.timedelta(days=7), rooms=1, adults=1,
            children=0, guest=self.user, guest_name="New Guest",
        )
        self.assertEqual(first.discount_total, Decimal("20.00"))
        self.assertEqual(first.nightly_total, Decimal("180.00"))
        self.assertTrue(first.rate_details_parsed[0]["rate"] == "90.00")
        self.user.refresh_from_db()
        self.assertTrue(self.user.welcome_offer_used)

        second = services.create_booking(
            room_type=self.rt, check_in=self.today + dt.timedelta(days=10),
            check_out=self.today + dt.timedelta(days=12), rooms=1, adults=1,
            children=0, guest=self.user, guest_name="New Guest",
        )
        self.assertEqual(second.discount_total, Decimal("0.00"))


class AvailabilityTests(TestCase):
    def setUp(self):
        self.rt = make_type(total=3)
        self.today = timezone.localdate()
        self.user = User.objects.create_user("g", password="x", role="guest", first_name="G", last_name="T")

    def book(self, ci_offset, nights, rooms=1, status="confirmed"):
        ci = self.today + dt.timedelta(days=ci_offset)
        return services.create_booking(room_type=self.rt, check_in=ci,
                                       check_out=ci + dt.timedelta(days=nights),
                                       rooms=rooms, adults=rooms, children=0,
                                       guest=self.user, guest_name="G T")

    def test_overlap_math(self):
        self.book(0, 3, rooms=2)          # days 0,1,2 → 2 rooms
        self.book(2, 3, rooms=1)          # days 2,3,4 → +1
        self.assertEqual(services.available_rooms(self.rt, self.today, self.today + dt.timedelta(days=1)), 1)
        self.assertEqual(services.booked_rooms(self.rt, self.today + dt.timedelta(days=2),
                                               self.today + dt.timedelta(days=3)), 3)
        self.assertEqual(services.available_rooms(self.rt, self.today + dt.timedelta(days=5),
                                                  self.today + dt.timedelta(days=6)), 3)

    def test_cannot_overbook(self):
        self.book(0, 2, rooms=2)
        self.book(0, 2, rooms=1)
        with self.assertRaises(BookingError):
            self.book(1, 1, rooms=1)      # would exceed inventory on night 1

    def test_cancelled_frees_inventory(self):
        b = self.book(0, 2, rooms=3)
        self.assertEqual(services.available_rooms(self.rt, self.today, self.today + dt.timedelta(days=2)), 0)
        services.cancel_booking(b, reason="test")
        self.assertEqual(services.available_rooms(self.rt, self.today, self.today + dt.timedelta(days=2)), 3)

    def test_adjacent_stays_do_not_conflict(self):
        self.book(0, 2, rooms=3)          # nights 0,1
        b = self.book(2, 2, rooms=3)      # nights 2,3 — checkout day reuse is fine
        self.assertEqual(b.status, Booking.Status.CONFIRMED)

    def test_guest_capacity_validation(self):
        with self.assertRaises(BookingError):
            services.create_booking(room_type=self.rt, check_in=self.today,
                                    check_out=self.today + dt.timedelta(days=1),
                                    rooms=1, adults=self.rt.max_guests + 1, children=0,
                                    guest=self.user, guest_name="G T")

    def test_past_dates_rejected(self):
        with self.assertRaises(BookingError):
            services.create_booking(room_type=self.rt, check_in=self.today - dt.timedelta(days=1),
                                    check_out=self.today, rooms=1, adults=1, children=0,
                                    guest=self.user, guest_name="G T")


class LifecycleTests(TestCase):
    def setUp(self):
        self.rt = make_type(total=2)
        Room.objects.create(number="101", room_type=self.rt, floor=1, status=Room.Status.VACANT_CLEAN)
        Room.objects.create(number="102", room_type=self.rt, floor=1, status=Room.Status.VACANT_CLEAN)
        self.today = timezone.localdate()
        self.staff = User.objects.create_user("rec", password="x", role="receptionist")
        self.guest = User.objects.create_user("g", password="x", role="guest", first_name="G", last_name="T")

    def new_booking(self, offset=0, nights=2):
        ci = self.today + dt.timedelta(days=offset)
        return services.create_booking(room_type=self.rt, check_in=ci, check_out=ci + dt.timedelta(days=nights),
                                       rooms=1, adults=2, children=0, guest=self.guest, guest_name="G T")

    def test_check_in_out_flow(self):
        b = self.new_booking()
        # invoice created automatically
        self.assertTrue(hasattr(b, "invoice"))
        self.assertEqual(b.invoice.total, b.grand_total)

        services.check_in_booking(b, user=self.staff, room_numbers=["101"])
        b.refresh_from_db()
        self.assertEqual(b.status, Booking.Status.CHECKED_IN)
        room = Room.objects.get(number="101")
        self.assertEqual(room.status, Room.Status.OCCUPIED_CLEAN)

        services.check_out_booking(b, user=self.staff)
        b.refresh_from_db()
        room.refresh_from_db()
        self.assertEqual(b.status, Booking.Status.CHECKED_OUT)
        self.assertEqual(room.status, Room.Status.VACANT_DIRTY)
        # housekeeping task auto-created
        self.assertTrue(room.housekeeping_tasks.filter(task_type="checkout_clean", status="pending").exists())
        # folio settled
        b.invoice.refresh_from_db()
        self.assertEqual(b.invoice.status, "paid")

    def test_check_in_requires_clean_room(self):
        b = self.new_booking()
        r = Room.objects.get(number="101")
        r.status = Room.Status.VACANT_DIRTY
        r.save()
        with self.assertRaises(BookingError):
            services.check_in_booking(b, user=self.staff, room_numbers=["101"])

    def test_free_cancellation_full_refund(self):
        from finance.models import Payment
        b = self.new_booking(offset=10)   # far future → free cancel
        Payment.objects.create(booking=b, invoice=b.invoice, amount=b.grand_total, method="card", status="completed")
        b.invoice.recalc_status()
        services.cancel_booking(b, reason="changed plans")
        b.refresh_from_db()
        self.assertEqual(b.cancellation_fee, Decimal("0"))
        refund = Payment.objects.get(booking=b, amount__lt=0)
        self.assertEqual(refund.amount, -b.grand_total)

    def test_late_cancellation_keeps_first_night(self):
        from finance.models import Payment
        b = self.new_booking(offset=0, nights=3)   # arrival today → past free window (2 days)
        Payment.objects.create(booking=b, invoice=b.invoice, amount=b.grand_total, method="card", status="completed")
        fee = services.cancellation_fee(b)
        self.assertEqual(fee, Decimal("100.00"))   # first night × 1 room
        services.cancel_booking(b, reason="late")
        refund = Payment.objects.get(booking=b, amount__lt=0)
        self.assertEqual(refund.amount, -(b.grand_total - fee))

    def test_no_show_automation(self):
        b = self.new_booking(offset=0)
        Booking.objects.filter(pk=b.pk).update(check_in=self.today - dt.timedelta(days=1),
                                               check_out=self.today)
        flagged = services.mark_no_shows()
        self.assertIn(b.pk, [x.pk for x in flagged])
        b.refresh_from_db()
        self.assertEqual(b.status, Booking.Status.NO_SHOW)

    def test_housekeeping_completion_returns_room_to_sellable(self):
        from operations.services import complete_task
        b = self.new_booking()
        services.check_in_booking(b, user=self.staff, room_numbers=["101"])
        services.check_out_booking(b, user=self.staff)
        room = Room.objects.get(number="101")
        task = room.housekeeping_tasks.first()
        complete_task(task, self.staff)
        room.refresh_from_db()
        self.assertEqual(room.status, Room.Status.VACANT_CLEAN)


class ConcurrencyTests(TransactionTestCase):
    """Hammers create_booking from parallel threads: inventory must never oversell."""

    def test_parallel_bookings_never_oversell(self):
        rt = make_type(name="Race", price="80.00", total=2)
        user = User.objects.create_user("racer", password="x", role="guest", first_name="R", last_name="T")
        today = timezone.localdate()

        def attempt(i):
            try:
                services.create_booking(room_type=rt, check_in=today + dt.timedelta(days=10),
                                        check_out=today + dt.timedelta(days=12),
                                        rooms=1, adults=1, children=0, guest=user, guest_name=f"Racer {i}")
                return True
            except BookingError:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))

        self.assertEqual(sum(results), 2, "exactly the 2 available rooms may be sold")
        self.assertEqual(services.available_rooms(rt, today + dt.timedelta(days=10),
                                                  today + dt.timedelta(days=12)), 0)
        self.assertEqual(Booking.objects.filter(room_type=rt, status="confirmed").count(), 2)


class MultiPropertyTests(TestCase):
    """Chain behaviour: inventory, pricing and rules are isolated per property."""

    def setUp(self):
        self.p1 = make_property("Alpha Grand", service_rate=Decimal("0.05"), tax_rate=Decimal("0.10"))
        self.p2 = make_property("Beta Beach", service_rate=Decimal("0.10"), tax_rate=Decimal("0.07"))
        self.rt1 = make_type(name="Alpha Room", price="100.00", total=2, property=self.p1)
        self.rt2 = make_type(name="Beta Room", price="100.00", total=2, property=self.p2)
        self.today = timezone.localdate()
        self.user = User.objects.create_user("g", password="x", role="guest", first_name="G", last_name="T")

    def book(self, rt, offset=0, nights=2, rooms=2):
        ci = self.today + dt.timedelta(days=offset + 5)
        return services.create_booking(room_type=rt, check_in=ci, check_out=ci + dt.timedelta(days=nights),
                                       rooms=rooms, adults=rooms, children=0, guest=self.user, guest_name="G T")

    def test_inventory_isolated_between_properties(self):
        self.book(self.rt1, rooms=2)   # sell out Alpha
        self.assertEqual(services.available_rooms(self.rt1, self.today + dt.timedelta(days=5),
                                                  self.today + dt.timedelta(days=7)), 0)
        self.assertEqual(services.available_rooms(self.rt2, self.today + dt.timedelta(days=5),
                                                  self.today + dt.timedelta(days=7)), 2)

    def test_per_property_tax_and_service_rates(self):
        ci = self.today + dt.timedelta(days=10)
        co = ci + dt.timedelta(days=2)  # 2 nights, avoid weekend variance by checking components
        p1 = services.price_stay(self.rt1, ci, co, 1)
        p2 = services.price_stay(self.rt2, ci, co, 1)
        self.assertEqual(p1["service"], (p1["subtotal"] * Decimal("0.05")).quantize(Decimal("0.01")))
        self.assertEqual(p1["tax"], ((p1["subtotal"] + p1["service"]) * Decimal("0.10")).quantize(Decimal("0.01")))
        self.assertEqual(p2["service"], (p2["subtotal"] * Decimal("0.10")).quantize(Decimal("0.01")))
        self.assertEqual(p2["tax"], ((p2["subtotal"] + p2["service"]) * Decimal("0.07")).quantize(Decimal("0.01")))
        self.assertNotEqual(p1["total"], p2["total"])

    def test_rule_scoping_property_vs_chain(self):
        ci = self.today + dt.timedelta(days=15)
        RateRule.objects.create(name="Chain promo", rule_type="seasonal", start_date=ci,
                                end_date=ci + dt.timedelta(days=5), multiplier=Decimal("0.5"), priority=1)
        RateRule.objects.create(name="Beta only", rule_type="seasonal", property=self.p2, start_date=ci,
                                end_date=ci + dt.timedelta(days=5), multiplier=Decimal("2.0"), priority=10)
        r1 = dict(services.nightly_rates(self.rt1, ci, ci + dt.timedelta(days=1)))
        r2 = dict(services.nightly_rates(self.rt2, ci, ci + dt.timedelta(days=1)))
        self.assertEqual(r1[ci], Decimal("50.00"))    # chain promo applies
        self.assertEqual(r2[ci], Decimal("200.00"))   # property rule outranks chain rule

    def test_occupancy_scoped_per_property(self):
        self.book(self.rt1, rooms=2)
        occ1 = services.occupancy_for_date(self.today + dt.timedelta(days=5), self.p1)
        occ_all = services.occupancy_for_date(self.today + dt.timedelta(days=5))
        self.assertEqual(occ1["occupied"], 2)
        self.assertEqual(occ_all["total"], 4)   # both properties' sellable rooms
