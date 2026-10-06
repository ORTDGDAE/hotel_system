# Aurelia Grand — Hotel Booking & Property Management System

A real-world, scalable hotel platform in **Django 5.2**: guest booking experience,
front-desk PMS, housekeeping/operations, finance & folios, analytics, and nightly
automation — with concurrency-safe inventory and a rules-driven pricing engine.

## Quick start

**One click (Windows):** double-click **`start.bat`** — it creates the
virtualenv, installs dependencies, migrates the local SQLite database, runs the
ledger audit, starts the server, and opens the public homepage **signed out**.
The staff dashboard remains protected at `/pms/` and requires a normal sign-in.
`install.bat` performs the same database setup without starting the server.
MySQL/MariaDB remains available explicitly with `set AURELIA_DB=mysql` and the
private `mysql.local.bat` settings. macOS/Linux: `./start.sh` does the same for
the default SQLite configuration.

Manual:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # realistic demo dataset
python manage.py runserver 0.0.0.0:8000
```

### Demo accounts (password: `Aurelia2026!`)
| User | Role | Sees |
|---|---|---|
| `admin` | Administrator | Everything + Django admin |
| `manager` | Group Manager | All hotels: PMS, rates, finance reports, analytics |
| `manager.sr` | Property Manager | Aurelia Angkor Sanctuary only |
| `pm.<hotel-slug>` | Property Manager | One assigned hotel only (same demo password) |
| `reception` | Receptionist (legacy flagship alias) | PMS, reservations, calendar, operations for Aurelia Grand Phnom Penh |
| `reception.<hotel-slug>` | Receptionist | One dedicated Reception account for each of the 10 assigned hotels |
| `housekeeping` / `housekeeping2` | Housekeeping | Grand Phnom Penh housekeeping team |
| `hk.<hotel-slug>-1..3` | Housekeeping | Three cleaners grouped under that hotel’s Property Manager |
| `guest` | Guest | Public site, My Stays, self-service cancellation |

## Database & Navicat

The Windows one-click scripts default to **SQLite** for a no-credential,
no-prompt launch. MySQL/MariaDB is an explicit option with
`AURELIA_DB=mysql`, using a database named `aurelia`; the application and
Navicat can connect to that same database. The SQLite file
**`aurelia_collection.db`** remains the safe local database and the source
snapshot for MySQL import. MySQL connection values are `MYSQL_HOST`,
`MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` (or
`MYSQL_PWD`). Safe starter templates are provided in `mysql.env.example` and
`mysql.local.bat.example`. Copy the latter to `mysql.local.bat`, replace the
password and any Navicat-specific values, and use `set AURELIA_DB=mysql` before
launching. Keep the real local file private.

A current **Navicat kit** lives in `navicat/`: 

| File | What it is |
|---|---|
| `navicat/aurelia_collection.db` | copy of the live SQLite DB — opens directly in Navicat |
| `navicat/aurelia_collection.postgres.sql` | full structure + data for PostgreSQL 12+ ("Run SQL File…") |
| `navicat/aurelia_collection.mysql.sql` | full structure + data for MySQL 8+ / MariaDB 10.4+ |
| `navicat/fixtures/aurelia_collection.json` | Django fixture for any backend (`manage.py loaddata`) |
| `navicat/fixtures/aurelia_collection_render_latest.json` | current 55-user / 10-hotel Render fixture |
| `Aurelia_Collection_PostgreSQL_Latest_Data.sql` | current PostgreSQL data-only import; run after Django migrations |
| `render.yaml` | Render web service + managed PostgreSQL Blueprint |
| `render_start.sh` | migrate, seed an empty database, collect static files, start Gunicorn |

Step-by-step connection/import instructions (including the green
"Test Connection" checklist) are in **`navicat/NAVICAT-GUIDE.md`**.
Regenerate the kit any time with `python3 scripts/export_navicat_kit.py`.

### Render.com deployment

This project now includes a Render Blueprint. In Render, choose **New → Blueprint**
and connect the repository containing this folder. Render will provision the web
service and a managed PostgreSQL database from `render.yaml`. The web service
reads Render's `DATABASE_URL`, runs migrations, seeds only an empty database with
the current 10-hotel demo dataset, collects static files, and starts Gunicorn on
Render's `$PORT`. The health check is `/healthz/`.

For a manual import instead, run migrations and load
`navicat/fixtures/aurelia_collection_render_latest.json` with
`python manage.py loaddata` after setting `DATABASE_URL`. This fixture contains
369 rooms, 24 room types, 170 bookings, 170 invoices, 103 payments, 55 users,
and 10 hotel-specific Reception accounts.

## Architecture

```
config/            settings, urls (DEBUG-hardened; Postgres/HTTPS-ready)
accounts/          custom User + role-based access control (guest→admin)
hotel/             sellable inventory: RoomType, physical Room, Amenity
bookings/          Booking, RoomAssignment, RateRule + domain services
                   (pricing engine, availability, lifecycle, no-show automation)
operations/        HousekeepingTask, MaintenanceRequest + automation services
finance/           Invoice (folio), Payment (charges & refunds), reporting
analytics/         KPI + chart endpoints (occupancy, ADR, RevPAR, channel mix)
core/              public site, guest dashboard, emails, nightly command wiring
```

### Domain rules implemented in `bookings/services.py`
- **Pricing engine** — rack rate × highest-priority seasonal/promo rule × weekend
  premium per night; the current Cambodia demo uses tax-only pricing (5% tax, no
  separate service charge); snapshot persisted on the booking (contracts never mutate).
- **Availability** — per-night peak-occupancy math over overlapping active
  bookings; validated inside `select_for_update()` on the inventory row → no
  double bookings even under concurrent requests.
- **Lifecycle** — confirmed → checked-in (assigns only vacant-clean rooms, flips
  them occupied) → checked-out (releases rooms, marks dirty, auto-creates urgent
  housekeeping tasks, settles the folio).
- **Cancellation policy** — free until N days before arrival (per room type),
  afterwards first night is retained; refunds are automatic ledger entries.
- **Automation** — `python manage.py nightly_ops` (cron 02:00): flags no-shows,
  queues daily housekeeping for occupied rooms, prints occupancy snapshot.
- **Maintenance** — high/critical requests block the room from selling until resolved.

### Security & scalability
- Custom user model + RBAC decorators; CSRF on every mutation; XSS-safe templates;
  clickjacking `DENY`; HTTPS/HSTS flags when `DEBUG=0`.
- Money handled with `Decimal` everywhere; DB constraints on date ranges and
  unique-active room assignments.
- Views are thin: all business logic lives in services → trivially testable
  (15 tests in `bookings/tests.py` cover pricing, availability, lifecycle,
  refunds and no-show automation).
- Scale path: Postgres + row locks (already used), Redis cache, Celery for
  `nightly_ops` + transactional email, gunicorn workers.

## API surface (staff)
- `GET /pms/api/price/?room_type=&check_in=&check_out=&rooms=` → JSON price preview
  used live by the new-reservation form.
- `GET /operations/rooms/stream/` → Server-Sent Events feed of live room-status
  changes; the Room Board patches tiles in place (soft real-time, zero JS deps).
- `GET /healthz/` → liveness/readiness probe for load balancers.

## v1.1 hardening (this revision)
- **Idempotent submissions** — booking wizard & staff form carry a session-bound
  idempotency token; a double-clicked "Confirm" can never create two reservations.
- **Proven concurrency safety** — `ConcurrencyTests` hammers `create_booking`
  from 8 threads against 2 rooms; exactly 2 sell. Postgres uses row locks
  (`SELECT … FOR UPDATE`); SQLite falls back to a process inventory lock.
- **Pagination** on reservations / payments / invoices with filter-preserving links.
- **Real-time room board** via SSE (swap the 2s poll for Channels/Redis pub-sub at scale).
- **Ops-ready**: `/healthz/`, structured `hotelops` logging, env-driven Postgres
  (`POSTGRES_DB` switches the DB automatically), `Dockerfile` + `docker-compose.yml`
  (Postgres + gunicorn + auto-migrate/seed entrypoint), GitHub Actions CI.

## Roadmap (recommended next steps, by impact/effort)
| Item | Why | Effort |
|---|---|---|
| Postgres `daterange` + GiST EXCLUDE constraint on inventory | double-booking impossible *at the DB level*, even outside the app | M |
| Nightly-inventory table or cached availability (Redis, invalidate on write) | search page stops recomputing per-night maths per request | M |
| DRF channel-manager API (public availability/rates, booking push webhooks, OTA sync) | real hotels live on Booking.com/Expedia connectivity | L |
| Rate plans (BAR/member/corporate per channel) instead of single rack rate | revenue-management parity | M |
| Folio line items (minibar, spa, restaurant postings) + night audit close | accurate accounting, locked business days | M |
| Celery beat for `nightly_ops` + async email; Sentry + request-id middleware | ops maturity | S |
| django-axes / rate limiting on login & booking endpoints | brute-force & abuse protection | S |
| Room moves/upgrades, group blocks, waitlist, overbooking buffer | commercial features | M–L |
| i18n (EN/KM) + WCAG accessibility pass + E2E suite (Playwright) | reach & quality | M |
| Locust load test of `/rooms/` search + booking POST | capacity proof before scaling | S |
