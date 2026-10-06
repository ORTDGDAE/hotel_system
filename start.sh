#!/usr/bin/env bash
# One-click setup + start (macOS / Linux twin of start.bat)
set -e
cd "$(dirname "$0")"
echo "== Aurelia Collection — one-click setup & start =="

if command -v python3 >/dev/null; then PY=python3; else PY=python; fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/5] Creating virtual environment .venv ..."
  "$PY" -m venv .venv
else
  echo "[1/5] Reusing existing virtual environment .venv"
fi
VPY=.venv/bin/python

echo "[2/5] Installing dependencies ..."
"$VPY" -m pip install --upgrade pip -q
"$VPY" -m pip install -r requirements.txt

FRESH=0
[ -f aurelia_collection.db ] || FRESH=1
echo "[3/5] Applying database migrations ..."
"$VPY" manage.py migrate
if [ "$FRESH" = "1" ]; then
  echo "[3/5] Fresh database — seeding demo data (10 sanctuaries, bookings, staff) ..."
  "$VPY" manage.py seed_demo
else
  echo "[3/5] Existing database found — keeping your data (no re-seed)"
fi

URL="http://127.0.0.1:8000/auth/dev-login/admin/?next=/pms/"
echo "[4/5] Browser will open AUTOMATICALLY LOGGED IN as administrator ..."
( sleep 6
  if command -v xdg-open >/dev/null; then xdg-open "$URL"
  elif command -v open >/dev/null; then open "$URL"; fi ) &

echo "[5/5] Starting server at http://127.0.0.1:8000  (Ctrl+C to stop)"
echo "------------------------------------------------------------"
echo "  AUTO-LOGIN : admin  (browser opens already signed in)"
echo "  Password   : Aurelia2026!  (only needed for manual login)"
echo "  Other demo users (same password): manager (group-wide),"
echo "               manager.sr and pm.<hotel-slug> (property managers),"
echo "               housekeeping teams: housekeeping, housekeeping2, hk.<hotel-slug>-1..3,"
echo "               reception, guest"
echo "------------------------------------------------------------"
"$VPY" manage.py runserver 127.0.0.1:8000
