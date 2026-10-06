from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("my-stays/", views.guest_dashboard, name="guest_dashboard"),
    path("map/", views.collection_map, name="collection_map"),
    path("healthz/", views.healthz, name="healthz"),
]
