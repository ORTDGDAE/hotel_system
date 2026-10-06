from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("payments/", views.payments_list, name="payments"),
    path("invoices/", views.invoices_list, name="invoices"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("reports/", views.reports, name="reports"),
]
