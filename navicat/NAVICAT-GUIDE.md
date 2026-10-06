# Navicat Guide — Aurelia Collection Database Kit

Everything in this folder is a ready-to-use export of the live Aurelia
Collection database (10 Cambodia-only hotels — Aurelia sanctuaries in Phnom Penh,
Siem Reap, Kep, Koh Rong, Sihanoukville and Battambang, plus three real landmark
addresses: Raffles Hotel Le Royal, Rosewood Phnom Penh and Sala Lodges Siem Reap,
and Song Saa Private Island — 24 room types, 369 rooms, 170 bookings, 100 payments,
7 staff/guest users, real location photography and Google-Maps coordinates for
every property and attraction — all demo data).

| File | Use it for |
|---|---|
| `aurelia_collection.db` | Open directly in **Navicat Premium / Navicat for SQLite** — zero setup |
| `aurelia_collection.postgres.sql` | Full structure + data import into **PostgreSQL 12+** |
| `aurelia_collection.mysql.sql` | Full structure + data import into **MySQL 8+ / MariaDB 10.4+** |
| `fixtures/aurelia_collection.json` | Backend-agnostic Django fixture (`loaddata`) |

> The MySQL kit is regenerated from the current Django migration state and
> current SQLite snapshot. It includes the latest `welcome_offer_used` and
> `discount_total` fields. Import it into your MySQL/MariaDB server with
> Navicat, then run the sanity queries below; the project cannot connect to a
> user-owned MySQL server until its host and credentials are supplied.

---

## Option A — SQLite (fastest, no server needed)

1. Open Navicat → **Connection → SQLite**.
2. **Connection Name:** `Aurelia Collection`.
3. **Database file:** browse to `navicat/aurelia_collection.db`.
4. Click **Test Connection** → you should get *“Connection successful”*
   (green status). Click **OK**.
5. Double-click the connection, then double-click `aurelia_collection`
   (it turns green/bold = opened). Browse tables: `hotel_property`,
   `bookings_booking`, `finance_invoice`, `finance_payment`, `accounts_user`…

**Run the Django app on this file** — it already does; this is the live
database (`config/settings.py` → `SQLITE_PATH`, default
`aurelia_collection.db` at the project root).

---

## Option B — PostgreSQL

1. Start a PostgreSQL server (local install, Docker, or cloud).
2. In Navicat: **Connection → PostgreSQL**. Fill in Host / Port (5432) /
   user / password → **Test Connection** → green → OK.
3. Right-click the connection → **New Database…**
   - Name: `aurelia`
   - Encoding: `UTF8`
   - (Collation/Ctype: default is fine)
4. Double-click `aurelia` to open it, then right-click it →
   **Run SQL File…**
5. Pick `aurelia_collection.postgres.sql`, Encoding **65001 (UTF-8)**,
   click **Start**. Expect `Finished … Error: 0`.
6. Right-click `aurelia` → **Refresh**. You should see 23 tables
   (`accounts_user`, `hotel_property`, `bookings_booking`, …) with data.

**Sanity query** (Navicat query editor):

```sql
SELECT count(*) AS properties FROM hotel_property;   -- 7
SELECT count(*) AS bookings   FROM bookings_booking; -- 170
SELECT round(sum(total), 2)   FROM finance_invoice;  -- 198475.74
```

**Point Django at PostgreSQL** — replace the `DATABASES["default"]` entry
in `config/settings.py` (or better, gate it on an env var):

```python
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "aurelia",
    "USER": "your_pg_user",
    "PASSWORD": "your_pg_password",
    "HOST": "localhost",
    "PORT": "5432",
}}
```

Then `python3 manage.py migrate` (no-op) and `python3 manage.py runserver`.

---

## Option C — MySQL / MariaDB

1. Start a MySQL 8+ (or MariaDB 10.4+) server.
2. In Navicat: **Connection → MySQL**. Host / Port (3306) / user /
   password → **Test Connection** → green → OK.
3. Right-click the connection → **New Database…**
   - Name: `aurelia`
   - Character Set: `utf8mb4`
   - Collation: `utf8mb4_general_ci` (or server default)
4. Double-click `aurelia`, right-click → **Run SQL File…** →
   pick `aurelia_collection.mysql.sql` → Encoding **65001 (UTF-8)** →
   **Start**. Expect `Error: 0`.
5. Refresh → 23 tables with data. The same sanity queries from Option B
   work here.

**Point Django at MySQL** — the project already includes PyMySQL in
`requirements.txt` and registers it as Django's MySQL driver. Use environment
variables rather than editing source code:

```bat
set AURELIA_DB=mysql
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_DATABASE=aurelia
set MYSQL_USER=root
set MYSQL_PASSWORD=your_mysql_password
python manage.py migrate
```

Then run `start.bat`; it will preserve/import the current SQLite snapshot when
the target database is empty. The app and Navicat can use the same `aurelia`
database, so there is no second copy to keep synchronized.

---

## Option D — Django fixtures (any backend)

Works with any database Django supports (including a brand-new empty one):

```bash
python3 manage.py migrate
python3 manage.py loaddata navicat/fixtures/aurelia_collection.json
```

The fixture is ordered FK-safe, so a single `loaddata` restores everything.

---

## Automatic loading — `install.bat` and `start.bat`

On Windows, both scripts default to **SQLite** so they run automatically
without a database password or Navicat connection. `start.bat` opens the public
homepage signed out; `/pms/` remains protected and requires login.

To opt into MySQL/MariaDB, set `AURELIA_DB=mysql` and copy
`mysql.local.bat.example` to `mysql.local.bat` with the same values used by
Navicat. The MySQL defaults are host `127.0.0.1`, port `3306`, database
`aurelia`, user `root`; the password is kept in the private local file.

`install.bat` then creates the virtual environment, installs Django and PyMySQL,
runs migrations, imports the current `aurelia_collection.db` snapshot into an
empty MySQL target, runs `audit_ledger`, and refreshes the current
`navicat/aurelia_collection.mysql.sql` export.

`start.bat` performs the same safe setup and then starts Django on the public
homepage. On later MySQL runs, the `--if-empty` guard leaves existing MySQL
data untouched.

The one-time copy helper can also be run directly:

```bat
set AURELIA_DB=mysql
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_DATABASE=aurelia
set MYSQL_USER=root
set MYSQL_PASSWORD=SECRET
.venv\Scripts\python scripts\migrate_sqlite_to_mysql.py --if-empty
```

If you prefer the Navicat GUI, connect to the same MySQL database and use
**Tools → Run SQL File** with `aurelia_collection.mysql.sql`. The SQL file is a
portable full snapshot and includes the current schema/data; the app scripts
are usually easier because they preserve the existing SQLite data without a
separate manual import.

---

## "Is my connection healthy?" checklist

- **Test Connection** returns *Connection successful* before you import.
- After import, the connection icon is green and the `aurelia` database
  opens (name turns bold/green) without a lock icon.
- Table count = **23** (plus nothing else — `sqlite_sequence` is
  SQLite-only and absent in PG/MySQL by design).
- `django_migrations` has **34** rows → `manage.py migrate` says
  *“No migrations to apply.”* (the DB is marked fully migrated, including the
  welcome-offer account and booking snapshot migrations).
- Login still works with the demo accounts (password hashes were
  exported verbatim): `manager` / `Aurelia2026!`.

## Demo accounts (all passwords: `Aurelia2026!`)

`manager` (chain-wide), `reception` (Phnom Penh),
`manager.sr` (Siem Reap), `housekeeping`, `housekeeping2`, `guest`, `admin`.

---

## Regenerating the kit

After any schema or data change:

```bash
python3 scripts/export_mysql_kit_offline.py
```

This refreshes the MySQL/Navicat SQL file from the current Django migration
state and live SQLite data without requiring a MySQL server. The original
`export_navicat_kit.py` remains available when local PostgreSQL and
MySQL/MariaDB servers are running and you want vendor-native dumps for both
backends.
