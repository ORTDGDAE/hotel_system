#!/bin/sh
set -eu

python manage.py migrate --noinput

# Seed only an empty Render database. Existing data is preserved on restarts.
python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.management import call_command
from hotel.models import RoomType

if os.environ.get("SEED_DEMO", "1") == "1" and not RoomType.objects.exists():
    call_command("seed_demo")
PY

python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 60 \
  --access-logfile -
