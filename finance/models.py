from decimal import Decimal

from django.conf import settings
from django.db import models

from bookings.models import Booking


class Invoice(models.Model):
    """Folio for a booking. One invoice per booking, settled via Payments."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIAL = "partial", "Partially paid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"
        VOID = "void", "Void"

    number = models.CharField(max_length=24, unique=True, blank=True)
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="invoice")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    service = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Invoice {self.number or self.pk} · {self.booking.code}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number and self.pk:
            self.number = f"INV-{self.issued_at:%Y}-{self.pk:06d}"
            super().save(update_fields=["number"])

    @property
    def paid_amount(self) -> Decimal:
        annotated = getattr(self, "paid_total", None)
        if annotated is not None:  # list views annotate the ledger total
            return annotated
        # .all() (not .filter) so a prefetched payments cache is reused
        return sum((p.amount for p in self.payments.all()
                    if p.status == Payment.Status.COMPLETED), Decimal("0"))

    @property
    def balance(self) -> Decimal:
        return self.total - self.paid_amount

    def recalc_status(self) -> None:
        """Derive folio status strictly from the completed-payment ledger."""
        completed = self.payments.filter(status=Payment.Status.COMPLETED)
        paid = sum((p.amount for p in completed), Decimal("0"))
        refunds = sum((p.amount for p in completed if p.amount < 0), Decimal("0"))
        if refunds < 0 and paid <= 0:
            self.status = self.Status.REFUNDED      # money went back out in full
        elif self.total <= 0 and paid <= 0:
            self.status = self.Status.PAID          # zero-balance folio = settled
        elif paid <= 0:
            self.status = self.Status.OPEN
        elif paid >= self.total:
            self.status = self.Status.PAID
        else:
            self.status = self.Status.PARTIAL
        self.save(update_fields=["status"])


class Payment(models.Model):
    """A financial transaction. amount < 0 means a refund."""

    class Method(models.TextChoices):
        CARD = "card", "Credit card"
        CASH = "cash", "Cash"
        BANK = "bank_transfer", "Bank transfer"
        WALLET = "wallet", "E-wallet"

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments", null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=16, choices=Method.choices, default=Method.CARD)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.COMPLETED)
    reference = models.CharField(max_length=64, blank=True, help_text="Gateway/PSP reference")
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at", "status"])]

    def __str__(self):
        sign = "refund" if self.amount < 0 else "charge"
        return f"{sign} {self.amount} {self.currency} · {self.booking.code}"

    @property
    def is_refund(self) -> bool:
        return self.amount < 0
