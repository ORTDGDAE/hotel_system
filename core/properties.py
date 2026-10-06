"""Session-scoped active property for the PMS (chain switcher)."""
from hotel.models import Property

SESSION_KEY = "pms_active_property"


def user_can_operate_property(user, prop) -> bool:
    """Return whether a staff user may operate the selected hotel."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_group_manager_or_above", False):
        return True
    return bool(getattr(user, "home_property_id", None) == getattr(prop, "pk", None))


def properties_for_user(user):
    """Hotels available in the staff property selector."""
    qs = Property.objects.filter(is_active=True)
    if getattr(user, "is_group_manager_or_above", False):
        return qs
    if getattr(user, "home_property_id", None):
        return qs.filter(pk=user.home_property_id)
    return qs.none()


def get_active_property(request):
    """Property the staff member is operating, or None for group-wide access."""
    user = getattr(request, "user", None)
    # A property manager is permanently scoped to the assigned home hotel;
    # never allow a stale ``all`` session value to widen that scope.
    if getattr(user, "is_property_manager", False):
        return getattr(user, "home_property", None)
    pk = request.session.get(SESSION_KEY)
    if pk == "all" or pk is None:
        return getattr(user, "home_property", None) if pk is None else None
    return Property.objects.filter(pk=pk, is_active=True).first()


def set_active_property(request, pk):
    request.session[SESSION_KEY] = pk or "all"


def scope_rooms(qs, prop):
    return qs.filter(room_type__property=prop) if prop else qs


def scope_bookings(qs, prop):
    return qs.filter(room_type__property=prop) if prop else qs
