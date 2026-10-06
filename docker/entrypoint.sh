#!/bin/sh
set -e
python manage.py migrate --noinput
# Seed demo data on first boot of an empty database (remove for real deployments)
python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from hotel.models import RoomType
if not RoomType.objects.exists() and os.environ.get("SEED_DEMO", "1") == "1":
    from django.core.management import call_command
    call_command("seed_demo")
PY
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${WEB_CONCURRENCY:-4}" --timeout 60 --access-logfile -
