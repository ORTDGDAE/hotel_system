"""Transactional email helpers. Console backend in dev; swap EMAIL_BACKEND in prod."""
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail


def _send(subject: str, body: str, to: list[str]) -> None:
    if not to or not any(to):
        return
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [t for t in to if t], fail_silently=True)


def send_booking_confirmation(booking) -> None:
    nights = "\n".join(
        f"  {n['date']}  ·  ${Decimal(n['rate']):,.2f}" for n in booking.rate_details_parsed
    )
    prop = booking.room_type.property
    _send(
        f"Reservation {booking.code} confirmed — {prop.name}",
        (
            f"Dear {booking.guest_name},\n\n"
            f"Your reservation is confirmed.\n\n"
            f"  Confirmation code : {booking.code}\n"
            f"  Room type         : {booking.room_type.name} × {booking.rooms_count}\n"
            f"  Check-in          : {booking.check_in} (from {settings.DEFAULT_CHECK_IN_HOUR}:00)\n"
            f"  Check-out         : {booking.check_out} (by {settings.DEFAULT_CHECK_OUT_HOUR}:00)\n"
            f"  Guests            : {booking.adults} adults, {booking.children} children\n\n"
            f"Nightly rates:\n{nights}\n\n"
            f"  Rooms subtotal    : ${booking.nightly_total:,.2f}\n"
            f"  Service           : ${booking.service_total:,.2f}\n"
            f"  Tax (5%)          : ${booking.tax_total:,.2f}\n"
            f"  Total             : ${booking.grand_total:,.2f}\n\n"
            f"  Hotel             : {prop.name}, {prop.city}\n"
            f"Free cancellation until {booking.cancellation_deadline}.\n\n"
            f"— {prop.name} Reservations · Aurelia Collection"
        ),
        [booking.guest_email],
    )


def send_cancellation_notice(booking, fee: Decimal) -> None:
    refund_line = (
        f"A cancellation fee of ${fee:,.2f} applies. Any remaining collected amount has been refunded."
        if fee > 0
        else "No cancellation fee applies. Any collected amount has been refunded in full."
    )
    _send(
        f"Reservation {booking.code} cancelled",
        f"Dear {booking.guest_name},\n\nYour reservation {booking.code} has been cancelled.\n{refund_line}\n\n— {booking.room_type.property.name} · Aurelia Collection",
        [booking.guest_email],
    )


def send_checkout_receipt(booking) -> None:
    invoice = getattr(booking, "invoice", None)
    lines = ""
    if invoice:
        lines = f"Invoice {invoice.number} · Total ${invoice.total:,.2f} · Paid ${invoice.paid_amount:,.2f}"
    _send(
        f"Thank you for staying with us — {booking.code}",
        f"Dear {booking.guest_name},\n\nWe hope you enjoyed your stay at {booking.room_type.property.name}.\n{lines}\n\n— Aurelia Collection",
        [booking.guest_email],
    )
