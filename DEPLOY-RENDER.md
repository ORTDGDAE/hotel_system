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

**Fix applied — as a separate companion file.**
`aurelia_collection_postgresql_latest.sql` is **byte-for-byte unmodified**
(md5 `8e37de4be0b91b5e2a16d291abb8d9b4`, identical to the original commit).
The repair ships alongside it as **`aurelia_collection_postgresql_sequences.sql`**,
run as a second step after the data import. It derives each value from `MAX(id)`
via `pg_get_serial_sequence()`, so it stays correct if the export is regenerated,
and re-running it is harmless — it only ever moves a sequence forward:

```sql
SELECT setval(pg_get_serial_sequence('"accounts_user"', 'id'),
              COALESCE((SELECT MAX("id") FROM "accounts_user"), 1), true);
```

Keeping the two files separate means the validated dump stays canonical and
diffable, and the repair can be skipped or re-applied independently.

## Final repository structure

Verified on a **fresh clone** of the pushed branch, in a clean virtualenv, with
no leftover build artifacts:

```
/                               <- Render Root Directory = BLANK
├── manage.py                   <- required at root
├── requirements.txt            <- required at root
├── render.yaml                 <- Blueprint (documentation; see duplicate warning)
├── render_start.sh             <- migrate -> collectstatic -> gunicorn on $PORT
├── Dockerfile  docker-compose.yml  docker/entrypoint.sh
├── config/                     <- Django project package (settings, urls, wsgi, asgi)
├── accounts/  analytics/  bookings/  core/  finance/  hotel/  operations/
│                               <- apps, each with migrations/ intact
├── templates/                  <- 36 templates
├── static/                     <- source static assets (img/, css/, js/)
├── aurelia_collection_postgresql_latest.sql      <- UNMODIFIED data dump
├── aurelia_collection_postgresql_sequences.sql   <- companion sequence repair
├── navicat/                    <- MySQL/SQLite export kit + Django fixtures
├── scripts/                    <- export, migration and deck-building utilities
├── ci/github-actions-ci.yml    <- parked CI workflow (see ci/README.md)
├── .gitignore  .gitattributes
└── README.md  CHANGELOG.md  QA-REPORT.md  DEPLOY-RENDER.md
```

`staticfiles/` (collectstatic output), `media/`, `aurelia_collection.db` and
`__pycache__/` are generated at runtime and gitignored — Render rebuilds them.

**On "media files":** nothing is missing. The project declares `MEDIA_ROOT` but
contains **no `FileField` or `ImageField`** anywhere, so it stores no
user-uploaded media. Every image the site serves is a versioned static asset
under `static/img/`, collected by WhiteNoise. `media/` is created on demand if
uploads are ever added.

## Do not create duplicate services

A web service and a PostgreSQL instance for this app **already exist**, created
manually. `render.yaml` declares a service named `aurelia-collection` and a
database named `aurelia-postgres` — running **New → Blueprint** would create a
*second* of each: two web services, two databases, one of them empty, both
billable, with an ambiguous DNS name.

The Blueprint file is kept as executable documentation and as a rebuild
starting point. To deploy, copy its `buildCommand`, `startCommand`,
`healthCheckPath` and `envVars` into the **existing** manual service. A header
comment in `render.yaml` says the same thing, so the warning travels with the
file.

The repository declares exactly one web service and one database; nothing in
this change provisions additional infrastructure.

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

# 2. import the data (Render Postgres allows external connections; use the
#    EXTERNAL Database URL, not the internal one)
psql "<EXTERNAL Database URL>" -v ON_ERROR_STOP=1 \
     -f aurelia_collection_postgresql_latest.sql

# 3. REQUIRED second step — repair the identity sequences (see defect #3 above)
psql "<EXTERNAL Database URL>" -v ON_ERROR_STOP=1 \
     -f aurelia_collection_postgresql_sequences.sql

# 4. verify
psql "<EXTERNAL Database URL>" -c \
  "SELECT last_value FROM accounts_user_id_seq;"   # -> 56
psql "<EXTERNAL Database URL>" -c \
  "SELECT last_value FROM hotel_room_id_seq;"      # -> 1851
psql "<EXTERNAL Database URL>" -c \
  "SELECT count(*) FROM hotel_room;"               # -> 369
```

Step 3 is not optional. Skipping it leaves every sequence at 1 and the first
new booking or signup written through the app fails with a duplicate-key error.

`-v ON_ERROR_STOP=1` matters on both files: without it `psql` reports errors and
keeps going, leaving a half-loaded database that looks successful.

The dump truncates first, so re-running steps 2 and 3 is idempotent — but it
will discard anything created on Render since the last import.

## Verified locally before handing over

All of the below was run against a **fresh `git clone` of the pushed branch** in
a clean virtualenv — not against a working copy — so it reflects exactly what
Render will fetch.

### Build and boot (Render's own commands)

- `pip install -r requirements.txt` — Django 5.2.17, gunicorn 23.0.0,
  whitenoise 6.12.0, psycopg 3.3.6 (libpq 18.6), dj-database-url 2.3.0
- `python manage.py collectstatic --noinput` — 183 files, 455 post-processed
- `python manage.py check --fail-level WARNING` — no issues
- `python manage.py migrate` — all **36** migrations apply on a cold database
- `sh render_start.sh` from the repository root — Gunicorn boots on `$PORT`
  (confirmed the process is `gunicorn config.wsgi:application`, **not** runserver)
- `/healthz/` → `200 {"status":"ok","database":true}`
- `/`, `/hotels/`, `/static/img/logo.png` → 200; `/admin/` → 302 to login
- Cold boot on an **empty** database with `SEED_DEMO=0` — no crash, health green
- Restart with existing data and `SEED_DEMO=0` — 10 properties / 24 room types /
  369 rooms / 170 bookings preserved, **no re-seed**
- `ALLOWED_HOSTS` enforced (foreign `Host:` → 400)
- `/auth/dev-login/admin/` → **404** with `DJANGO_DEBUG=0`
- All shell scripts confirmed **LF**, not CRLF — `.gitattributes` now pins this,
  because CRLF in `render_start.sh` breaks `sh render_start.sh` on Linux with a
  misleading "not found"

### Against real PostgreSQL 16.2

A local PostgreSQL 16.2 server was stood up to close the gap that SQLite testing
leaves. Django connected through the **same `DATABASE_URL` code path Render uses**:

- `migrate` — 36 migrations applied on PostgreSQL
- `manage.py test` — **41 tests, OK** on PostgreSQL (same as SQLite)
- The data dump imported with `-v ON_ERROR_STOP=1` — **zero errors**, landing
  exactly on the snapshot the dump header declares: 55 users, 10 hotels,
  369 rooms, 170 bookings, 170 invoices, 103 payments
- Re-importing the dump a second time reproduced those same counts — **idempotent**
- The dump's schema is a perfect match for the migrated Django schema: every
  table and every column it writes exists, and every table it writes is in its
  own `TRUNCATE` list

### The sequence defect, demonstrated on PostgreSQL

Two databases were loaded identically; only one got the companion repair.
Then a new row was created through the Django ORM in each:

| | dump only | dump + `sequences.sql` |
|---|---|---|
| `accounts_user_id_seq` | 1 | 56 |
| `hotel_room_id_seq` | 1 | 1851 |
| create a new guest signup | ❌ `IntegrityError: duplicate key value violates unique constraint "accounts_user_pkey"` | ✅ `id=57` |
| create a new hotel | ⚠️ **silently succeeds with `id=1`** | ✅ `id=62` |

That third row is the dangerous one. `hotel_property` ids in the dump start at
52, so id 1 is free — a new hotel is created *successfully* with a wildly
wrong id, and the collision only surfaces weeks later once the sequence climbs
into the occupied range. Guest signups fail immediately instead.

### Two gotchas worth knowing

- **Never run the test suite with `DJANGO_DEBUG=0`.** It sets
  `SECURE_SSL_REDIRECT=1`, and the test client issues plain HTTP, so 13 tests
  fail with `301 != 200/302/404`. This is not a PostgreSQL or application bug —
  run `manage.py test` with `DJANGO_DEBUG` unset. (The parked CI workflow does
  this correctly.)
- **`manage.py test` teardown can error with `database "test_…" is being
  accessed by other users`.** `CONN_MAX_AGE=60` keeps connections open past the
  test run, so Django cannot drop the test database. The tests themselves have
  already passed at that point. Use `--keepdb`, or drop it manually with
  `DROP DATABASE … WITH (FORCE)`.

### Still unverified

Only one thing: a connection to **Render's own** Postgres instance, which is not
reachable from here. Everything up to that hop is proven — `DATABASE_URL`
parsing for both of Render's schemes (`postgres://` and `postgresql://`), each
resolving to `django.db.backends.postgresql` with `OPTIONS={'sslmode':'require'}`
and correctly URL-decoding special characters in the password, plus live
queries, migrations, the test suite and the data import against a real server.

The one difference on Render is TLS: `DATABASE_SSL_REQUIRE=1` demands it, and
Render's Postgres provides it. `/healthz/` executes a real `SELECT 1` and
returns **503** on failure, so it will report the live connection status
immediately after deploy.
