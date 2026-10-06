from datetime import date, datetime, timedelta

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def money(value, currency="USD"):
    try:
        from decimal import Decimal
        v = Decimal(str(value))
    except Exception:
        return value
    symbol = {"USD": "$", "KHR": "៛"}.get(currency, currency + " ")
    return f"{symbol}{v:,.2f}"


@register.filter
def multiply(value, arg):
    """Multiply numeric template values, including string filter arguments.

    Django passes a filter argument such as ``booking.rooms_count`` to this
    function as a rendered string.  Multiplying a Decimal by that string
    raises TypeError, which previously made invoice line amounts fall back to
    the unmultiplied nightly rate.
    """
    try:
        from decimal import Decimal
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return value


@register.simple_tag
def daterange(start, days):
    """Iterate dates in templates: {% daterange start 7 as days %}"""
    return [start + timedelta(days=i) for i in range(days)]


@register.filter
def date_fmt(value, fmt="%a %d %b"):
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, (date, datetime)):
        return value.strftime(fmt)
    return value


@register.filter
def night_label(value):
    """'2026-09-10' → 'Wed 10 Sep'"""
    return date_fmt(value, "%a %d %b")


@register.filter
def pct_bar(value):
    try:
        return max(0, min(100, int(round(float(value)))))
    except Exception:
        return 0


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.simple_tag(takes_context=True)
def nav_active(context, prefix, exact=False):
    path = context["request"].path
    if exact:
        return "active" if path == prefix else ""
    return "active" if path.startswith(prefix) else ""
