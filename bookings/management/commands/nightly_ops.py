"""Nightly automation job — schedule via cron / systemd timer / Celery beat:

    0 2 * * *  python manage.py nightly_ops
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.services import mark_no_shows, occupancy_for_date
from operations.services import generate_daily_service_tasks


class Command(BaseCommand):
    help = "Runs nightly hotel automation: no-show processing, daily housekeeping tasks, occupancy snapshot."

    def handle(self, *args, **options):
        today = timezone.localdate()
        no_shows = mark_no_shows()
        self.stdout.write(self.style.WARNING(f"Marked {len(no_shows)} booking(s) as no-show."))

        created = generate_daily_service_tasks()
        self.stdout.write(self.style.SUCCESS(f"Created {created} daily housekeeping task(s)."))

        occ = occupancy_for_date(today)
        self.stdout.write(f"Tonight's occupancy: {occ['occupied']}/{occ['total']} rooms ({occ['pct']}%)")
