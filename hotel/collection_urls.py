from django.urls import path
from . import views

app_name = "collection"

urlpatterns = [
    path("", views.property_list, name="property_list"),
]
