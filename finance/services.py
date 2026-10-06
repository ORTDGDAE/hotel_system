"""Finance services: folio lifecycle + reporting. Called by booking services."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from bookings.models import Booking

from .models import Invoice, Payment


def ensure_invoice(booking: Booking) -> Invoice:
    """Create (or refresh while unpaid) the folio mirroring the booking snapshot."""
    invoice, created = Invoice.objects.get_or_create(
        booking=booking,
        defaults={
            "subtotal": booking.nightly_total,
            "service": booking.service_total,
            "tax": booking.tax_total,
            "total": booking.grand_total,
        },
    )
    return invoice


def record_payment(booking: Booking, amount: Decimal, method: str = Payment.Method.CARD,
                   *, note: str = "", created_by=None, reference: str = "") -> Payment:
    if amount == 0:
        raise ValueError("Payment amount cannot be zero.")
    with transaction.atomic():
        invoice = ensure_invoice(booking)
        if amount > 0 and amount > invoice.balance + Decimal("0.004"):
            raise ValueError(
                f"Amount exceeds the outstanding balance of {invoice.balance} {invoice.booking.currency}."
            )
        payment = Payment.objects.create(
            invoice=invoice, booking=booking, amount=amount, method=method,
            note=note, created_by=created_by, reference=reference,
            status=Payment.Status.COMPLETED,
        )
        invoice.recalc_status()
    return payment


def process_cancellation(booking: Booking, fee: Decimal) -> None:
    """Refund collected money minus the cancellation fee; adjust the folio."""
    invoice = ensure_invoice(booking)
    paid = invoice.paid_amount
    if paid <= 0:
        invoice.recalc_status()
        return
    refund_amount = paid - fee
    invoice.total = fee  # guest's final liability is the fee only
    invoice.subtotal = fee
    invoice.service = Decimal("0")
    invoice.tax = Decimal("0")
    invoice.save(update_fields=["total", "subtotal", "service", "tax"])
    if refund_amount > 0:
        Payment.objects.create(
            invoice=invoice, booking=booking, amount=-refund_amount,
            method=Payment.Method.CARD, status=Payment.Status.COMPLETED,
            note=f"Auto-refund on cancellation (fee retained: {fee})",
        )
    invoice.recalc_status()


def settle_folio(booking: Booking) -> Invoice:
    """On check-out, charge any remaining balance to the folio as pay-at-hotel."""
    invoice = ensure_invoice(booking)
    if invoice.balance > 0:
        Payment.objects.create(
            invoice=invoice, booking=booking, amount=invoice.balance,
            method=Payment.Method.CASH, status=Payment.Status.COMPLETED,
            note="Settled at check-out",
        )
    invoice.recalc_status()
    return invoice


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def revenue_range(start: dt.date, end: dt.date, property=None) -> dict:
    """Completed charges (excluding refunds) within [start, end] by created date."""
    qs = Payment.objects.filter(
        status=Payment.Status.COMPLETED,
        created_at__date__gte=start,
        created_at__date__lte=end,
    )
    if property:
        qs = qs.filter(booking__room_type__property=property)
    charges = qs.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    refunds = qs.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return {"charges": charges, "refunds": refunds, "net": charges + refunds}


def revenue_by_day(days: int = 30, property=None) -> list[dict]:
    today = timezone.localdate()
    start = today - dt.timedelta(days=days - 1)
    qs0 = Payment.objects.filter(
            status=Payment.Status.COMPLETED, created_at__date__gte=start
        )
    if property:
        qs0 = qs0.filter(booking__room_type__property=property)
    rows = (
        qs0
        .extra({"day": "date(created_at)"})
        .values("day")
        .annotate(net=Sum("amount"))
        .order_by("day")
    )
    by_day = {r["day"]: r["net"] for r in rows}
    out = []
    d = start
    while d <= today:
        out.append({"day": d, "net": by_day.get(d, Decimal("0"))})
        d += dt.timedelta(days=1)
    return out


def outstanding_balance(property=None) -> Decimal:
    """Open folio balances for a hotel or the full collection.

    Two queries total: the open-folio set plus one prefetch of their payment
    ledgers (Invoice.paid_amount reuses the prefetch cache). Summing
    max(balance, 0) is numerically identical to the previous per-row guard.
    """
    open_invoices = (
        Invoice.objects
        .exclude(status__in=[Invoice.Status.PAID, Invoice.Status.VOID, Invoice.Status.REFUNDED])
        .prefetch_related("payments")
    )
    if property:
        open_invoices = open_invoices.filter(booking__room_type__property=property)
    total = Decimal("0")
    for inv in open_invoices:
        total += max(inv.balance, Decimal("0"))
    return total
