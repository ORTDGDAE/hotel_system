"""Load the Navicat MySQL kit into a MySQL/MariaDB server using pure PyMySQL.

This is install.bat's automatic fallback when no mysql.exe client is on PATH
and none is found in the common install folders (MySQL Server, MariaDB,
XAMPP, Wamp64) - it needs no client binary at all, only a reachable server.

    python scripts/load_kit_mysql.py --host 127.0.0.1 --port 3306 --user root \
        [--password SECRET]  (or set MYSQL_PWD)  \
        [--database aurelia] --file navicat/aurelia_collection.mysql.sql [--keep]

By default the target database is dropped and recreated (full rebuild);
pass --keep to load into an existing database as-is.
Exits 0 on success (and prints verification counts), 1 on any failure.
"""
import argparse
import os
import sys

import pymysql
from pymysql.constants import CLIENT

TABLES = [
    "hotel_property", "hotel_roomtype", "hotel_room", "hotel_amenity",
    "hotel_attraction", "bookings_booking", "finance_payment",
    "finance_invoice", "accounts_user", "django_migrations",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Load the Aurelia Navicat kit into MySQL/MariaDB via PyMySQL.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default=os.environ.get("MYSQL_PWD", ""))
    ap.add_argument("--database", default="aurelia")
    ap.add_argument("--file", required=True, help="path to navicat/aurelia_collection.mysql.sql")
    ap.add_argument("--keep", action="store_true", help="do not drop the database first")
    a = ap.parse_args()

    try:
        with open(a.file, encoding="utf-8") as fh:
            sql = fh.read()
    except OSError as exc:
        print(f"[ERROR] cannot read {a.file}: {exc}")
        return 1

    try:
        conn = pymysql.connect(
            host=a.host, port=a.port, user=a.user, password=a.password,
            charset="utf8mb4", autocommit=True, connect_timeout=10,
            client_flag=CLIENT.MULTI_STATEMENTS,
        )
    except pymysql.MySQLError as exc:
        print(f"[ERROR] cannot connect to {a.host}:{a.port} as {a.user}: {exc}")
        return 1

    try:
        with conn.cursor() as cur:
            if not a.keep:
                cur.execute(f"DROP DATABASE IF EXISTS `{a.database}`")
                while cur.nextset():
                    pass
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{a.database}` "
                        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{a.database}`")
            while cur.nextset():
                pass
        print(f"  Loading {os.path.basename(a.file)} into {a.host}:{a.port}/{a.database} ...")
        with conn.cursor() as cur:
            cur.execute(sql)  # whole dump in one multi-statement round trip
            while cur.nextset():
                pass
        with conn.cursor() as cur:
            union = " union all ".join(
                f"select '{t}', count(*) from `{t}`" for t in TABLES)
            cur.execute(union)
            rows = cur.fetchall()
            cur.execute("select count(*) from hotel_amenity where icon like 'ri-%%'")
            amenity_ri = cur.fetchone()[0]
            cur.execute("select count(*) from hotel_attraction where icon like 'ri-%%'")
            attraction_ri = cur.fetchone()[0]
        print("  MySQL OK - verification counts:")
        for name, count in rows:
            print(f"    {name:<20}: {count}")
        print(f"    {'icon classes (ri-)':<20}: {amenity_ri} amenities + {attraction_ri} attractions")
        return 0
    except pymysql.MySQLError as exc:
        print(f"[ERROR] load failed: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
