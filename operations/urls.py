from django.urls import path
from . import views

app_name = "operations"

urlpatterns = [
    path("rooms/", views.room_board, name="room_board"),
    path("rooms/stream/", views.room_stream, name="room_stream"),
    path("rooms/<int:pk>/status/", views.room_status_update, name="room_status"),
    path("housekeeping/", views.task_board, name="task_board"),
    path("housekeeping/<int:pk>/assign/", views.task_assign, name="task_assign"),
    path("housekeeping/<int:pk>/start/", views.task_start, name="task_start"),
    path("housekeeping/<int:pk>/complete/", views.task_complete, name="task_complete"),
    path("maintenance/", views.maintenance_list, name="maintenance"),
    path("maintenance/create/", views.maintenance_create, name="maintenance_create"),
    path("maintenance/<int:pk>/resolve/", views.maintenance_resolve, name="maintenance_resolve"),
]
