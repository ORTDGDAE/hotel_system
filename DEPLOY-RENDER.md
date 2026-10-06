# Render deployment runbook — Aurelia Collection

Written 2026-10-06 after tracing the failed deploy end to end.

## Why the deploy was failing

Three separate defects, found in this order. All three had to be fixed; fixing
only the folder would still have failed.

### 1. Render never unzips archives (the deploy blocker)

`github.com/ORTDGDAE/hotel_system` at `main` contained exactly two files:

```
PP_latest.zip                              22 MB
aurelia_collection_postgresql_latest.sql   393 KB
```

The Django project lived *inside* the zip at **`PP_latest/hotel_pms/`** — that
folder holds `manage.py`, `requirements.txt`, `config/`, `render.yaml` and
`render_start.sh`. Render clones the repo and runs your build command against
the working tree; it will not open a zip, and its **Root Directory** setting only
points at directories that physically exist in the git tree. So there was no
`requirements.txt` and no `manage.py` for any command to find — the build could
not succeed no matter what was typed into the dashboard.

**Fix applied:** `PP_latest/hotel_pms/` extracted to the repository root and
committed as real files; `PP_latest.zip` removed. The sibling folder
`PP_latest/image-search/` (12 MB of loose stock photos) was *not* carried over —
it is referenced nowhere in the codebase; the app serves its own images from
`static/img/`.

With the project at the root, Render's **Root Directory stays blank**.

### 2. `seed_demo` crashed on two `NameError`s (would have failed the next deploy)

`render_start.sh` runs under `set -eu` and seeds an empty database when
`SEED_DEMO=1`. A fresh Render Postgres is always empty, so seeding always ran —
and always died:

```
File "core/management/commands/seed_demo.py", line 409, in handle
    hk2.home_property = props[0]; hk2.save()
NameError: name 'hk2' is not defined. Did you mean: 'hk1'?
```

`housekeeping2` was created without being bound to a name, and `team` was
appended to before it was ever initialised. Under `set -eu` that aborts the
start command, so Gunicorn never launched and Render marked the deploy failed.

**Fix applied:** both lines corrected in `core/management/commands/seed_demo.py`.
Verified — seeding now completes: `10 properties, 24 room types, 369 rooms,
170 bookings, 100 payments, 21 tasks, 54 users`.

### 3. The SQL dump left every identity sequence at 1 (silent data-loss risk)

Not a deploy blocker — it surfaces *after* a successful import, so it would have
looked like a mystery production bug.

The dump opens with `TRUNCATE ... RESTART IDENTITY CASCADE`, which resets all
sequences to 1, then inserts rows with **explicit primary keys** — and contains
**zero `setval` calls**. Highest ids in the export:

| table | rows | max id |
|---|---|---|
| `hotel_room` | 369 | 1851 |
| `bookings_booking` | 170 | 1069 |
| `finance_invoice` | 170 | 1069 |
| `finance_payment` | 103 | 666 |
| `accounts_user` | 55 | 56 |
| `hotel_property` | 10 | 61 |

After import, the first row the application creates is offered `id = 1` and
PostgreSQL rejects it:

```
duplicate key value violates unique constraint "accounts_user_pkey"
```

A new guest signup fails immediately; a new booking fails immediately.
`hotel_room` is worse — ids 1–1500 are free, so new rooms insert successfully
for weeks and then start colliding.

**Fix applied:** an identity-repair block appended inside the dump's transaction,
immediately before `COMMIT;`. It is generated from `MAX(id)` per table via
`pg_get_serial_sequence()`, so it stays correct if the export is regenerated,
and re-running it is harmless:

```sql
SELECT setval(pg_get_serial_sequence('"accounts_user"', 'id'),
              COALESCE((SELECT MAX("id") FROM "accounts_user"), 1), true);
```

No existing line of the dump was modified — the block is purely additive.

## Render settings to paste (manual Web Service)

| Field | Value |
|---|---|
| Runtime | **Python 3** |
| Branch | `main` (merge `arena/96943623-hotel-system` first) |
| **Root Directory** | *(leave blank)* |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `sh render_start.sh` |
| Health Check Path | `/healthz/` |
| Plan | Free |

`render_start.sh` then runs `migrate`, conditionally seeds, collects static
files, and execs Gunicorn bound to `0.0.0.0:$PORT`.

### Environment variables

| Key | Value | Notes |
|---|---|---|
| `DATABASE_URL` | *from the Postgres instance* | Use **Internal Database URL** |
| `DJANGO_SECRET_KEY` | *(Generate)* | |
| `DJANGO_DEBUG` | `0` | `1` would disable all the production hardening |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` | Leading dot = wildcard subdomain |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` | Without this, every POST 403s |
| `DATABASE_SSL_REQUIRE` | `1` | Render Postgres needs TLS |
| `SEED_DEMO` | `0` | You are importing the real dump; seeding is wasted work it then truncates |
| `WEB_CONCURRENCY` | `2` | Free tier is 512 MB; 2 workers fits |

Do **not** set `DJANGO_DEMO_LOGIN=1`. Along with `DEBUG=0` it is the only thing
that enables `/auth/dev-login/<username>/`, a passwordless login. Verified it
returns **404** with the settings above.

## Importing the data (the step you deferred)

Run these **after** the deploy is green, so `migrate` has built the schema —
the dump is data-only and assumes the tables exist.

```bash
# 1. confirm the deploy is healthy
curl https://<your-service>.onrender.com/healthz/
#    -> {"status": "ok", "database": true}

# 2. import (Render Postgres allows external connections; use the EXTERNAL URL)
psql "<EXTERNAL Database URL>" -v ON_ERROR_STOP=1 \
     -f aurelia_collection_postgresql_latest.sql

# 3. verify the sequence repair took effect
psql "<EXTERNAL Database URL>" -c \
  "SELECT last_value FROM accounts_user_id_seq; SELECT count(*) FROM hotel_room;"
#    -> last_value must be 56, count must be 369
```

`-v ON_ERROR_STOP=1` matters: without it `psql` reports errors and keeps going,
leaving a half-loaded database that looks successful.

The dump truncates first, so re-running it is idempotent — but it will discard
anything created on Render since the last import.

## Verified locally before handing over

Reproduced Render's environment exactly (Python 3.11, `DJANGO_DEBUG=0`,
`DATABASE_SSL_REQUIRE=1`, `SEED_DEMO=0`, Gunicorn on `$PORT`):

- `pip install -r requirements.txt` — Django 5.2.17, gunicorn 23.0.0,
  whitenoise 6.12.0, psycopg 3.3.6, dj-database-url 2.3.0
- `python manage.py check` — no issues
- `python manage.py migrate` — all 34 migrations apply on a cold database
- `python manage.py collectstatic` — 183 files, 455 post-processed
- `sh render_start.sh` — Gunicorn boots, `/healthz/` → `200 {"status":"ok","database":true}`
- `python manage.py test` — **41 tests, OK**
- Cold boot with `SEED_DEMO=0` on an empty database — no crash, health check green
- Restart with existing data and `SEED_DEMO=0` — data preserved, no re-seed
- `/`, `/hotels/`, `/admin/`, `/static/img/logo.png` all serve correctly
- `ALLOWED_HOSTS` enforced (foreign `Host:` → 400)
- `/auth/dev-login/admin/` → 404 in production mode
- All shell scripts confirmed **LF**, not CRLF — `.gitattributes` now pins this,
  because CRLF in `render_start.sh` breaks `sh render_start.sh` on Linux with a
  misleading "not found"

### Still unverified

`DATABASE_URL` parsing was validated for both of Render's URL schemes
(`postgres://` and `postgresql://`) — both resolve to
`django.db.backends.postgresql` with `OPTIONS={'sslmode': 'require'}` and
correctly URL-decode special characters in the password. An **actual connection
to Render's Postgres was not possible from here**; `/healthz/` is the probe that
will report it, since it executes a real `SELECT 1` and returns 503 on failure.
