from django.conf import settings


def site_context(request):
    from core.properties import properties_for_user
    ctx = {
        "HOTEL_NAME": "Aurelia Collection",
        "HOTEL_TAGLINE": "10 sanctuaries · Cambodia",
        "CURRENCY": settings.HOTEL_CURRENCY,
        "properties": properties_for_user(request.user),
    }
    if getattr(request.user, "is_staff_role", False):
        from core.properties import get_active_property
        ctx["active_property"] = get_active_property(request)
    return ctx
