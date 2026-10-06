from django.urls import path
from . import views

app_name = "pms"

urlpatterns = [
    path("", views.pms_dashboard, name="dashboard"),
    path("switch/", views.switch_property, name="switch_property"),
    path("reservations/", views.reservations, name="reservations"),
    path("reservations/new/", views.reservation_new, name="booking_new"),
    path("reservations/<int:pk>/", views.reservation_detail, name="booking_detail"),
    path("reservations/<int:pk>/check-in/", views.reservation_check_in, name="check_in"),
    path("reservations/<int:pk>/check-out/", views.reservation_check_out, name="check_out"),
    path("reservations/<int:pk>/cancel/", views.reservation_cancel, name="cancel"),
    path("reservations/<int:pk>/payment/", views.reservation_payment, name="payment"),
    path("calendar/", views.calendar, name="calendar"),
    path("rates/", views.rates, name="rates"),
    path("api/price/", views.price_api, name="price_api"),
    path("rates/<int:pk>/toggle/", views.rate_rule_toggle, name="rate_rule_toggle"),
    path("rates/<int:pk>/delete/", views.rate_rule_delete, name="rate_rule_delete"),
]
