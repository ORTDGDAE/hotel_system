"""Add the ten hotel-scoped Reception accounts to all bundled data exports.

The live SQLite databases and seed command are updated separately. This keeps
Navicat's MySQL/PostgreSQL SQL exports and the Django JSON fixture aligned with
that live demo data without requiring a database server connection.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_DB = ROOT / "aurelia_collection.db"
MYSQL = ROOT / "navicat" / "aurelia_collection.mysql.sql"
POSTGRES = ROOT / "navicat" / "aurelia_collection.postgres.sql"
FIXTURE = ROOT / "navicat" / "fixtures" / "aurelia_collection.json"


def live_reception_rows():
    con = sqlite3.connect(LIVE_DB)
    rows = con.execute(
        """select username, password, first_name, last_name, email, role,
                  home_property_id, phone, avatar_initials
           from accounts_user
           where role='receptionist' and username like 'reception.%'
           order by username"""
    ).fetchall()
    props = dict(con.execute("select id, slug from hotel_property"))
    return [(*row, props[row[6]]) for row in rows]


def property_ids(path: Path, quote: str):
    text = path.read_text(encoding="utf-8")
    if quote == "`":
        pattern = re.compile(r"INSERT INTO `hotel_property` .*?VALUES \((\d+), '[^']*', '([^']+)'", re.S)
    else:
        pattern = re.compile(r'INSERT INTO "hotel_property" .*?VALUES \((\d+), \'[^\']*\', \'([^\']+)\'', re.S)
    return {slug: int(pid) for pid, slug in pattern.findall(text)}


def max_user_id(text: str, quote: str):
    token = "`accounts_user`" if quote == "`" else '"accounts_user"'
    values = re.findall(rf"INSERT INTO {re.escape(token)} .*?VALUES \((\d+),", text)
    return max(map(int, values), default=0)


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


def mysql_lines(rows, pids, start_id):
    out = []
    for offset, (username, password, first, last, email, role, _root_pid, phone, initials, slug) in enumerate(rows):
        uid = start_id + offset
        out.append(
            "INSERT INTO `accounts_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, "
            "`first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `role`, "
            "`home_property_id`, `phone`, `avatar_initials`, `welcome_offer_used`) VALUES "
            f"({uid}, '{sql_escape(password)}', NULL, 0, '{sql_escape(username)}', "
            f"'{sql_escape(first)}', '{sql_escape(last)}', '{sql_escape(email)}', 0, 1, "
            f"'2026-10-05 00:00:00', '{role}', {pids[slug]}, '{sql_escape(phone)}', '{initials}', 0);"
        )
    return out


def postgres_lines(rows, pids, start_id):
    out = []
    for offset, (username, password, first, last, email, role, _root_pid, phone, initials, slug) in enumerate(rows):
        uid = start_id + offset
        out.append(
            'INSERT INTO "accounts_user" ("id", "password", "last_login", "is_superuser", '
            '"username", "first_name", "last_name", "email", "is_staff", "is_active", '
            '"date_joined", "role", "home_property_id", "phone", "avatar_initials") VALUES '
            f"({uid}, '{sql_escape(password)}', NULL, FALSE, '{sql_escape(username)}', "
            f"'{sql_escape(first)}', '{sql_escape(last)}', '{sql_escape(email)}', FALSE, TRUE, "
            f"'2026-10-05 00:00:00+00', '{role}', {pids[slug]}, '{sql_escape(phone)}', '{initials}');"
        )
    return out


def insert_once(text: str, marker: str, lines: list[str], marker_name: str) -> str:
    # Use the stable account-name prefix rather than numeric IDs: other SQL
    # rows can legitimately contain the same ID values.
    if "reception.aurelia-" in text:
        return text
    if marker not in text:
        raise RuntimeError(f"Could not find {marker_name} insertion marker")
    return text.replace(marker, "\n".join(lines) + "\n" + marker, 1)


def update_sql(path: Path, quote: str, marker: str, marker_name: str):
    text = path.read_text(encoding="utf-8")
    rows = live_reception_rows()
    pids = property_ids(path, quote)
    missing = [slug for *_, slug in rows if slug not in pids]
    if missing:
        raise RuntimeError(f"Missing property IDs in {path.name}: {missing}")
    start = max_user_id(text, quote) + 1
    lines = mysql_lines(rows, pids, start) if quote == "`" else postgres_lines(rows, pids, start)
    path.write_text(insert_once(text, marker, lines, marker_name), encoding="utf-8")
    print(path, "updated with", len(lines), "Reception rows")


def update_fixture():
    rows = live_reception_rows()
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    existing = {obj.get("fields", {}).get("username") for obj in data if obj.get("model") == "accounts.user"}
    max_pk = max((obj.get("pk", 0) for obj in data if obj.get("model") == "accounts.user"), default=0)
    prop_ids = {obj["fields"]["slug"]: obj["pk"] for obj in data if obj.get("model") == "hotel.property"}
    added = 0
    for offset, (username, password, first, last, email, role, _root_pid, phone, initials, slug) in enumerate(rows, 1):
        if username in existing:
            continue
        data.append({
            "model": "accounts.user",
            "pk": max_pk + offset,
            "fields": {
                "password": password,
                "last_login": None,
                "is_superuser": False,
                "username": username,
                "first_name": first,
                "last_name": last,
                "email": email,
                "is_staff": False,
                "is_active": True,
                "date_joined": "2026-10-05T00:00:00Z",
                "role": role,
                "home_property": prop_ids[slug],
                "phone": phone,
                "avatar_initials": initials,
                "welcome_offer_used": False,
                "groups": [],
                "user_permissions": [],
            },
        })
        added += 1
    FIXTURE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(FIXTURE, "updated with", added, "Reception rows")


if __name__ == "__main__":
    update_sql(
        MYSQL,
        "`",
        "ALTER TABLE `accounts_user` AUTO_INCREMENT = 1;",
        "MySQL accounts_user marker",
    )
    update_sql(
        POSTGRES,
        '"',
        "SELECT setval(pg_get_serial_sequence('accounts_user', 'id'), COALESCE(MAX(\"id\"), 1)) FROM \"accounts_user\";",
        "PostgreSQL accounts_user marker",
    )
    update_fixture()
