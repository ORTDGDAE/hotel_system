from django.contrib import admin
from .models import HousekeepingTask, MaintenanceRequest


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ("room", "task_type", "status", "priority", "assigned_to", "created_at")
    list_filter = ("status", "task_type", "priority")


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "room", "severity", "status", "created_at")
    list_filter = ("status", "severity")
