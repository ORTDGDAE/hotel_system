import datetime as dt
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from bookings import services
from hotel.models import Property, RoomType

from .views import invoice_tax_label


class InvoiceDisplayTests(TestCase):
    def test_tax_label_uses_the_invoice_snapshot_rate(self):
        class Snapshot:
            subtotal = Decimal("900.00")
            service = Decimal("45.00")
            tax = Decimal("94.50")

        self.assertEqual(invoice_tax_label(Snapshot()), "Tax (10%)")

    def test_tax_only_snapshot_is_labeled_five_percent(self):
        class Snapshot:
            subtotal = Decimal("900.00")
            service = Decimal("0.00")
            tax = Decimal("45.00")

        self.assertEqual(invoice_tax_label(Snapshot()), "Tax (5%)")


class InvoiceStatusTests(TestCase):
    """The ledger audit and Invoice.recalc_status share zero-balance rules."""

    def test_zero_balance_folio_is_settled_not_open(self):
        prop = Property.objects.create(name="Finance Test Hotel", city="Phnom Penh")
        room_type = RoomType.objects.create(
            property=prop,
            name="Finance Test Room",
            base_price=Decimal("100.00"),
            total_rooms=1,
        )
        guest = User.objects.create_user("finance-guest", password="test-password-123", role=User.Role.GUEST)
        start = timezone.localdate() + dt.timedelta(days=10)
        booking = services.create_booking(
            room_type=room_type,
            check_in=start,
            check_out=start + dt.timedelta(days=2),
            rooms=1,
            adults=1,
            children=0,
            guest=guest,
            guest_name="Finance Guest",
        )
        invoice = booking.invoice
        invoice.total = Decimal("0.00")
        invoice.save(update_fields=["total"])
        invoice.recalc_status()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
