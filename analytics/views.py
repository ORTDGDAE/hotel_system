import datetime as dt
from collections import Counter, defaultdict
from decimal import Decimal

from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import manager_required
from core.properties import get_active_property
from bookings.models import Booking
from bookings.services import occupancy_for_date, occupancy_series
from finance.models import Payment
from hotel.models import RoomType


@manager_required
def overview(request):
    today = timezone.localdate()
    days = 30
    start = today - dt.timedelta(days=days - 1)
    prop = get_active_property(request)

    def bscope(qs):
        return qs.filter(room_type__property=prop) if prop else qs

    def pscope(qs):
        return qs.filter(booking__room_type__property=prop) if prop else qs

    # --- KPI cards ---------------------------------------------------------
    # One 2-query series covers today's KPI, the 30-day average AND the chart.
    occ_days = occupancy_series(start, days, prop)
    occ = occ_days[-1]
    window_bookings = bscope(Booking.objects.filter(created_at__date__gte=start))
    stays = bscope(Booking.objects.filter(check_out__gte=start, check_in__lte=today,
                                   status__in=["checked_in", "checked_out"]))
    room_nights = sum(b.nights * b.rooms_count for b in stays) or 0
    total_sellable = sum(rt.total_rooms for rt in RoomType.objects.filter(is_active=True, **( {"property": prop} if prop else {}))) or 1
    occupancy_30 = round(sum(s["pct"] for s in occ_days) / days, 1)
    revenue = pscope(Payment.objects.filter(status="completed", amount__gt=0,
                                     created_at__date__gte=start)).aggregate(t=Sum("amount"))["t"] or Decimal("0")
    adr = (revenue / room_nights) if room_nights else Decimal("0")
    revpar = revenue / (total_sellable * days)

    # --- charts data ---------------------------------------------------------
    # bookings created per day
    per_day = defaultdict(int)
    for b in window_bookings:
        per_day[b.created_at.date()] += 1
    chart_days = [(start + dt.timedelta(days=i)) for i in range(days)]
    bookings_series = [per_day.get(d, 0) for d in chart_days]

    # revenue per day
    rev_day = defaultdict(Decimal)
    for p in pscope(Payment.objects.filter(status="completed", created_at__date__gte=start)).values("created_at", "amount"):
        rev_day[p["created_at"].date()] += p["amount"]
    revenue_series = [float(rev_day.get(d, Decimal("0"))) for d in chart_days]

    # source mix
    sources = Counter(bscope(Booking.objects.filter(created_at__date__gte=start)).values_list("source", flat=True))
    source_labels = [dict(Booking.Source.choices).get(k, k) for k in sources]

    # room type performance (revenue + nights)
    type_rows = (
        bscope(Booking.objects.filter(check_out__gte=start, status__in=["checked_in", "checked_out"]))
        .values("room_type__name")
        .annotate(nights=Sum("rooms_count"), revenue=Sum("grand_total"))
        .order_by("-revenue")
    )

    # occupancy per day series
    occ_series = [s["pct"] for s in occ_days]

    # funnel / status mix
    status_counts = Counter(bscope(Booking.objects.filter(created_at__date__gte=start)).values_list("status", flat=True))

    return render(request, "analytics/overview.html", {
        "today": today, "days": days, "start": start,
        "kpis": {
            "occupancy_today": occ["pct"], "occupancy_30": occupancy_30,
            "revenue_30": revenue, "adr": adr, "revpar": revpar,
            "room_nights": room_nights, "bookings_30": window_bookings.count(),
            "cancellations_30": status_counts.get("cancelled", 0) + status_counts.get("no_show", 0),
        },
        "chart_labels": [d.strftime("%d %b") for d in chart_days],
        "bookings_series": bookings_series,
        "revenue_series": revenue_series,
        "occ_series": occ_series,
        "source_labels": source_labels,
        "source_values": list(sources.values()),
        "type_rows": type_rows,
        "status_counts": status_counts,
        "total_sellable": total_sellable,
        "scope_name": prop.name if prop else "All properties",
    })
