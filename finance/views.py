import datetime as dt
from decimal import Decimal

from django.db.models import DecimalField, Min, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from accounts.decorators import front_office_required, manager_required
from bookings.models import Booking
from bookings.services import occupancy_for_date
from core.pagination import paginate
from core.properties import get_active_property
from hotel.models import Property, RoomType

from . import services
from .models import Invoice, Payment


def invoice_tax_label(invoice):
    """Describe the tax rate represented by this invoice snapshot.

    Invoice totals are contractual snapshots.  Older demo folios may contain
    a service charge and a different tax rate from the current tax-only
    catalog, so a hard-coded ``Tax (5%)`` label is misleading on those folios.
    """
    tax_base = invoice.subtotal + invoice.service
    if tax_base <= 0:
        return "Tax"
    rate = (invoice.tax / tax_base * Decimal("100")).quantize(Decimal("0.01"))
    rate_text = format(rate, "f").rstrip("0").rstrip(".")
    return f"Tax ({rate_text}%)"


@front_office_required
def payments_list(request):
    prop = get_active_property(request)
    qs = Payment.objects.select_related("booking", "invoice", "created_by")
    if prop:
        qs = qs.filter(booking__room_type__property=prop)
    qs = qs.all()
    method = request.GET.get("method", "")
    if method:
        qs = qs.filter(method=method)
    total_charged = qs.filter(amount__gt=0).aggregate(t=Sum("amount"))["t"] or Decimal("0")
    total_refunded = qs.filter(amount__lt=0).aggregate(t=Sum("amount"))["t"] or Decimal("0")
    price_qs = RoomType.objects.filter(is_active=True)
    if prop:
        price_qs = price_qs.filter(property=prop)
    lowest_nightly_price = price_qs.aggregate(m=Min("base_price"))["m"] or Decimal("0")
    rate_property = prop or Property.objects.filter(is_active=True).first()
    service_rate = rate_property.service_rate if rate_property else Decimal("0")
    tax_rate = rate_property.tax_rate if rate_property else Decimal("0")
    page, query = paginate(request, qs, 25)
    return render(request, "finance/payments.html", {
        "payments": page, "page": page, "query": query, "method": method,
        "total_charged": total_charged, "total_refunded": -total_refunded,
        "lowest_nightly_price": lowest_nightly_price,
        "service_percent": int(service_rate * 100),
        "tax_percent": int(tax_rate * 100),
        "method_choices": Payment.Method.choices,
    })


@front_office_required
def invoices_list(request):
    prop = get_active_property(request)
    qs = Invoice.objects.select_related("booking", "booking__room_type", "booking__guest").annotate(
        paid_total=Coalesce(
            Sum("payments__amount", filter=Q(payments__status="completed")),
            Value(0), output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )
    if prop:
        qs = qs.filter(booking__room_type__property=prop)
    qs = qs.all()
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-issued_at", "-id")  # deterministic pagination (stable tie-break)
    page, query = paginate(request, qs, 25)
    return render(request, "finance/invoices.html", {
        "invoices": page, "page": page, "query": query, "status": status,
        "status_choices": Invoice.Status.choices,
        "outstanding": services.outstanding_balance(prop),
    })


@front_office_required
def invoice_detail(request, pk):
    prop = get_active_property(request)
    invoice_qs = Invoice.objects.select_related("booking", "booking__room_type", "booking__guest")
    if prop:
        invoice_qs = invoice_qs.filter(booking__room_type__property=prop)
    invoice = get_object_or_404(invoice_qs, pk=pk)
    return render(request, "finance/invoice_detail.html", {
        "invoice": invoice,
        "payments": invoice.payments.all(),
        "booking": invoice.booking,
        "tax_label": invoice_tax_label(invoice),
        "is_legacy_snapshot": invoice.service > 0,
    })


@manager_required
def reports(request):
    today = timezone_today()
    start = today - dt.timedelta(days=int(request.GET.get("days", 30)) - 1)
    prop = get_active_property(request)
    rev = services.revenue_range(start, today, prop)
    by_day = services.revenue_by_day(int(request.GET.get("days", 30)), prop)
    # revenue by room type (charged payments joined via booking)
    pay_qs = Payment.objects.filter(status="completed", amount__gt=0, created_at__date__gte=start)
    if prop:
        pay_qs = pay_qs.filter(booking__room_type__property=prop)
    by_type = (
        pay_qs
        .values("booking__room_type__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    # ADR: average grand_total per room-night of completed stays in range
    stays = Booking.objects.filter(check_out__gte=start, check_in__lte=today,
                                   status__in=["checked_in", "checked_out"])
    if prop:
        stays = stays.filter(room_type__property=prop)
    room_nights = sum(b.nights * b.rooms_count for b in stays)
    adr = (sum((b.grand_total for b in stays), Decimal("0")) / room_nights) if room_nights else Decimal("0")
    occupancy = occupancy_for_date(today, prop)
    return render(request, "finance/reports.html", {
        "revenue": rev, "by_day": by_day, "by_type": by_type,
        "adr": adr, "room_nights": room_nights, "occupancy": occupancy,
        "start": start, "today": today, "days": int(request.GET.get("days", 30)),
        "outstanding": services.outstanding_balance(prop),
    })


def timezone_today():
    from django.utils import timezone
    return timezone.localdate()
