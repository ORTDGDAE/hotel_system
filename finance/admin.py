from django.contrib import admin
from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "booking", "status", "total", "issued_at")
    list_filter = ("status",)
    search_fields = ("number", "booking__code", "booking__guest_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "currency", "method", "status", "created_at")
    list_filter = ("method", "status")
    search_fields = ("booking__code", "reference")
