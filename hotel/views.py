from datetime import date, timedelta

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from bookings.services import (available_rooms, bulk_overlaps, bulk_rate_rules,
                               price_stay, search_availability)
from .models import Property, RoomType


def _parse_date(value, default=None):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return default


def property_list(request):
    """The collection: every hotel in the group with from-prices."""
    from django.db.models import Count, Min, Q
    from hotel.models import Room
    props = (
        Property.objects.filter(is_active=True)
        .annotate(
            from_price_ann=Min("room_types__base_price", filter=Q(room_types__is_active=True)),
            rt_count=Count("room_types", filter=Q(room_types__is_active=True), distinct=True),
            sellable_ann=Count("rooms", filter=~Q(rooms__status__in=Room.BLOCKED_STATUSES), distinct=True),
        )
        .prefetch_related("room_types")
    )
    return render(request, "hotel/property_list.html", {"properties": props})


def room_list(request):
    """Public rooms page with optional date-driven availability + live pricing."""
    today = timezone.localdate()
    prop = None
    prop_slug = request.GET.get("property", "")
    if prop_slug:
        prop = get_object_or_404(Property, slug=prop_slug, is_active=True)
    check_in = _parse_date(request.GET.get("check_in"), today)
    check_out = _parse_date(request.GET.get("check_out"), today + timedelta(days=1))
    adults = max(int(request.GET.get("adults", 2) or 2), 1)
    children = max(int(request.GET.get("children", 0) or 0), 0)
    rooms = max(int(request.GET.get("rooms", 1) or 1), 1)

    if check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    if check_in < today:
        check_in, check_out = today, today + timedelta(days=1)

    dated = "check_in" in request.GET
    results = search_availability(check_in, check_out, adults, children, rooms, property=prop) if dated else []
    result_map = {r["room_type"].pk: r for r in results}

    room_types = RoomType.objects.filter(is_active=True).select_related("property").prefetch_related("amenities")
    rules = bulk_rate_rules(check_in, check_out)
    overlaps = bulk_overlaps(check_in, check_out)
    if prop:
        room_types = room_types.filter(property=prop)
    cards = []
    for rt in room_types:
        if dated:
            entry = result_map.get(rt.pk)
            pricing = entry["pricing"] if entry else price_stay(rt, check_in, check_out, rooms, rules=rules)
            avail = entry["available"] if entry else 0
        else:
            pricing = price_stay(rt, check_in, check_out, rooms, rules=rules)
            avail = available_rooms(rt, check_in, check_out, overlaps=overlaps)
        cards.append({"room_type": rt, "pricing": pricing, "available": avail})

    recommended_slugs = [
        "aurelia-grand-phnom-penh",
        "aurelia-angkor-sanctuary",
        "song-saa-private-island",
    ]
    return render(request, "hotel/room_list.html", {
        "cards": cards, "check_in": check_in, "check_out": check_out,
        "adults": adults, "children": children, "rooms": rooms, "dated": dated,
        "property": prop, "properties": Property.objects.filter(is_active=True),
        "recommended_slugs": recommended_slugs,
    })


def room_detail(request, slug):
    rt = get_object_or_404(RoomType, slug=slug, is_active=True)
    today = timezone.localdate()
    check_in = _parse_date(request.GET.get("check_in"), today)
    check_out = _parse_date(request.GET.get("check_out"), today + timedelta(days=2))
    if check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    pricing = price_stay(rt, check_in, check_out, 1)
    avail = available_rooms(rt, check_in, check_out)
    return render(request, "hotel/room_detail.html", {
        "room_type": rt, "pricing": pricing, "available": avail,
        "check_in": check_in, "check_out": check_out, "property": rt.property,
    })
