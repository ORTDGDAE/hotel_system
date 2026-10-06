from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from hotel.models import Amenity, RoomType


def home(request):
    today = timezone.localdate()
    featured = RoomType.objects.filter(is_active=True).prefetch_related("amenities")[:3]
    amenities = Amenity.objects.all()[:8]
    return render(request, "core/home.html", {
        "featured": featured,
        "amenities": amenities,
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "day_after": today + timedelta(days=2),
    })


@login_required
def guest_dashboard(request):
    from bookings.models import Booking
    user = request.user
    bookings = Booking.objects.filter(guest=user).select_related("room_type", "invoice")
    upcoming = [b for b in bookings if b.status in Booking.ACTIVE_STATUSES and b.check_out >= timezone.localdate()]
    past = [b for b in bookings if b not in upcoming][:10]
    return render(request, "core/guest_dashboard.html", {
        "upcoming": upcoming,
        "past": past,
        "total_stays": bookings.count(),
    })


def healthz(request):
    """Liveness/readiness probe for load balancers & orchestrators."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({"status": "ok" if db_ok else "degraded", "database": db_ok},
                        status=200 if db_ok else 503)


# Stylised border ring of the Kingdom of Cambodia (lon, lat) — decorative
# low-poly outline for the collection map (not survey-grade).
KH_OUTLINE = [
    (102.35, 13.00), (102.80, 13.55), (103.20, 13.95), (103.50, 14.35),
    (104.20, 14.42), (104.70, 14.42), (105.20, 14.35), (105.60, 14.55),
    (106.20, 14.60), (106.60, 14.30), (106.90, 13.90), (107.30, 13.40),
    (107.62, 12.90), (107.40, 12.30), (106.90, 11.70), (106.40, 11.10),
    (106.00, 10.90), (105.40, 10.88), (104.80, 10.50), (104.45, 10.38),
    (104.20, 10.48), (103.90, 10.50), (103.60, 10.52), (103.30, 10.60),
    (103.10, 10.90), (102.90, 11.20), (102.60, 11.70), (102.35, 12.30),
]


def collection_map(request):
    """Interactive Google-Maps-style collection map (self-contained SVG engine)."""
    import json
    from hotel.models import Property
    props = [p for p in Property.objects.filter(is_active=True)
             if p.latitude is not None and p.longitude is not None]
    lon0, lon1, lat0, lat1 = 102.2, 107.8, 9.9, 14.9
    w, h = 1000.0, 880.0

    def xy(lon, lat):
        return [round((lon - lon0) / (lon1 - lon0) * w, 1),
                round((lat1 - lat) / (lat1 - lat0) * h, 1)]

    def pts(coords):
        return " ".join(f"{x},{y}" for x, y in (xy(*c) for c in coords))

    geo = {
        "land": pts(KH_OUTLINE),
        "lake": pts([(103.55, 13.10), (103.85, 13.18), (104.20, 13.10),
                     (104.35, 12.95), (104.10, 12.80), (103.75, 12.90)]),
        "mekong": pts([(105.75, 14.40), (105.95, 13.85), (106.02, 12.95),
                       (105.85, 12.35), (105.45, 11.98), (105.20, 11.72),
                       (104.92, 11.57), (104.80, 11.30), (104.90, 11.05),
                       (105.20, 10.85)]),
        "tonle_river": pts([(104.30, 12.92), (104.60, 12.20), (104.92, 11.57)]),
        "cardamoms": pts([(102.90, 11.90), (103.30, 11.60), (103.80, 11.30),
                          (104.10, 10.95), (103.80, 10.80), (103.30, 11.10),
                          (102.95, 11.45)]),
        "bokor": pts([(104.00, 10.75), (104.30, 10.70), (104.45, 10.55),
                      (104.20, 10.50), (103.95, 10.60)]),
        "labels": [
            {"x": xy(102.85, 13.75), "t": "THAILAND"},
            {"x": xy(106.15, 14.62), "t": "LAOS"},
            {"x": xy(107.25, 12.10), "t": "VIETNAM"},
            {"x": xy(103.55, 10.02), "t": "GULF OF THAILAND"},
            {"x": xy(103.92, 13.00), "t": "Tonle Sap", "water": True},
        ],
    }
    data = []
    for p in props:
        data.append({
            "slug": p.slug, "name": p.name, "city": p.city, "stars": p.stars,
            "price": float(p.from_price or 0), "img": p.image_url,
            "tagline": p.tagline, "maps": p.maps_url,
            "lat": p.latitude, "lng": p.longitude,
            "x": xy(p.longitude, p.latitude)[0], "y": xy(p.longitude, p.latitude)[1],
        })
    return render(request, "core/map.html",
                  {"geo": geo, "props_json": json.dumps(data), "total": len(props)})
