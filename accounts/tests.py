import datetime as dt
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from finance.models import Invoice
from hotel.models import Property, Room, RoomType

from .models import User


class PropertyManagerScopeTests(TestCase):
    def setUp(self):
        self.hotel_a = Property.objects.create(name="Scope Hotel A", city="Phnom Penh")
        self.hotel_b = Property.objects.create(name="Scope Hotel B", city="Siem Reap")
        self.type_a = RoomType.objects.create(
            property=self.hotel_a, name="A Room", base_price=Decimal("100.00"), total_rooms=1,
        )
        self.type_b = RoomType.objects.create(
            property=self.hotel_b, name="B Room", base_price=Decimal("100.00"), total_rooms=1,
        )
        self.room_a = Room.objects.create(room_type=self.type_a, property=self.hotel_a, number="101", floor=1)
        self.room_b = Room.objects.create(room_type=self.type_b, property=self.hotel_b, number="201", floor=2)
        self.manager = User.objects.create_user(
            username="property-manager", password="test-password-123",
            role=User.Role.PROPERTY_MANAGER, home_property=self.hotel_a,
        )
        self.booking_a = self.make_booking(self.type_a, "A Guest")
        self.booking_b = self.make_booking(self.type_b, "B Guest")

    def make_booking(self, room_type, guest_name):
        start = timezone.localdate() + dt.timedelta(days=5)
        booking = Booking.objects.create(
            guest_name=guest_name, guest_email="guest@example.com", room_type=room_type,
            check_in=start, check_out=start + dt.timedelta(days=1), rooms_count=1,
            adults=1, status=Booking.Status.CONFIRMED,
            nightly_total=Decimal("100.00"), tax_total=Decimal("5.00"), grand_total=Decimal("105.00"),
            rate_details=[{"date": start.isoformat(), "rate": "100.00"}],
        )
        Invoice.objects.create(
            booking=booking, subtotal=Decimal("100.00"), tax=Decimal("5.00"), total=Decimal("105.00"),
        )
        return booking

    def setUp_session(self):
        self.client.force_login(self.manager)

    def test_property_manager_sees_only_home_hotel_rooms(self):
        self.setUp_session()
        response = self.client.get(reverse("operations:room_board"))
        self.assertEqual(response.status_code, 200)
        rooms = [room for rooms in response.context["rooms_by_floor"].values() for room in rooms]
        self.assertEqual({room.pk for room in rooms}, {self.room_a.pk})
        self.assertContains(response, "Scope Hotel A")
        self.assertNotContains(response, "201")

    def test_property_manager_cannot_switch_to_all_or_other_hotel(self):
        self.setUp_session()
        response = self.client.get(reverse("pms:switch_property"), {"property": "all"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("pms_active_property"), self.hotel_a.pk)
        response = self.client.get(reverse("pms:switch_property"), {"property": self.hotel_b.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("pms_active_property"), self.hotel_a.pk)

    def test_property_manager_cannot_open_other_hotel_booking_or_invoice(self):
        self.setUp_session()
        booking_response = self.client.get(reverse("pms:booking_detail", args=[self.booking_b.pk]))
        invoice_response = self.client.get(reverse("finance:invoice_detail", args=[self.booking_b.invoice.pk]))
        self.assertEqual(booking_response.status_code, 404)
        self.assertEqual(invoice_response.status_code, 404)

    def test_property_manager_sees_only_home_hotel_reservations(self):
        self.setUp_session()
        response = self.client.get(reverse("pms:reservations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking_a.code)
        self.assertNotContains(response, self.booking_b.code)

    def test_property_manager_gets_only_home_hotel_housekeeping_team(self):
        User.objects.create_user(
            username="hk-a", password="test-password-123", role=User.Role.HOUSEKEEPING,
            home_property=self.hotel_a,
        )
        User.objects.create_user(
            username="hk-b", password="test-password-123", role=User.Role.HOUSEKEEPING,
            home_property=self.hotel_b,
        )
        self.setUp_session()
        response = self.client.get(reverse("operations:task_board"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({u.username for u in response.context["housekeepers"]}, {"hk-a"})
