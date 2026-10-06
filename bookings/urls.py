from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("book/<slug:slug>/", views.book_room, name="book"),
    path("confirmation/<int:pk>/", views.confirmation, name="confirmation"),
    path("cancel/<int:pk>/", views.cancel_my_booking, name="cancel_mine"),
]
