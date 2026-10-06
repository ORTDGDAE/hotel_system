"""Export the current SQLite demo data as PostgreSQL data-only SQL.

The target PostgreSQL database must already have the Django schema. Run
`python manage.py migrate` first, then execute the generated file with psql.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.apps import apps
from django.db import models

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "navicat" / "fixtures" / "aurelia_collection_render_latest.json"
OUT = ROOT / "Aurelia_Collection_PostgreSQL_Latest_Data.sql"

ORDER = [
    "hotel.amenity",
    "hotel.property",
    "hotel.roomtype",
    "hotel.room",
    "hotel.attraction",
    "accounts.user",
    "bookings.raterule",
    "bookings.booking",
    "finance.invoice",
    "finance.payment",
    "bookings.roomassignment",
    "operations.housekeepingtask",
    "operations.maintenancerequest",
]


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def qstr(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_value(field, value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(field, models.JSONField):
        return qstr(json.dumps(value, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"
    if isinstance(field, (models.IntegerField, models.FloatField)) and not isinstance(value, str):
        return str(value)
    # Django fixtures serialize dates, datetimes, decimals and text as strings;
    # PostgreSQL casts quoted literals to the target column type.
    return qstr(str(value))


def model_for(label):
    app, name = label.split(".", 1)
    return apps.get_model(app, name)


def concrete_fields(model):
    # Include the auto-created primary-key field so all foreign-key IDs from
    # the fixture continue to point at the same rows after import.
    return [f for f in model._meta.concrete_fields if not f.auto_created or f.primary_key]


def insert_line(model, obj):
    fields = concrete_fields(model)
    columns = []
    values = []
    data = obj["fields"]
    for field in fields:
        columns.append(field.column)
        if field.primary_key:
            value = obj["pk"]
        else:
            value = data.get(field.name)
        values.append(sql_value(field, value))
    return (
        f"INSERT INTO {qident(model._meta.db_table)} ("
        + ", ".join(qident(c) for c in columns)
        + ") VALUES ("
        + ", ".join(values)
        + ");"
    )


def through_lines(model, obj):
    field = next((f for f in model._meta.many_to_many if f.name == "amenities"), None)
    if field is None:
        return []
    through = field.remote_field.through
    # The auto-created through model has two foreign keys: roomtype and amenity.
    source_field = field.m2m_field_name()
    target_field = field.m2m_reverse_field_name()
    source_id = obj["pk"]
    values = obj["fields"].get(field.name) or []
    lines = []
    for target_id in values:
        lines.append(
            f"INSERT INTO {qident(through._meta.db_table)} "
            f"({qident(source_field + '_id')}, {qident(target_field + '_id')}) "
            f"VALUES ({source_id}, {target_id});"
        )
    return lines


def main():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    by_label = {label: [] for label in ORDER}
    for obj in fixture:
        if obj.get("model") in by_label:
            by_label[obj["model"]].append(obj)

    models_by_label = {label: model_for(label) for label in ORDER}
    tables = [model._meta.db_table for model in models_by_label.values()]
    roomtype_model = models_by_label["hotel.roomtype"]
    amenities_field = roomtype_model._meta.get_field("amenities")
    tables.append(amenities_field.remote_field.through._meta.db_table)

    lines = [
        "-- Aurelia Collection — latest PostgreSQL data export",
        "-- Generated from the validated current SQLite dataset.",
        "-- Requires the current Django schema: run `python manage.py migrate` first.",
        "-- Current snapshot: 10 hotels, 369 rooms, 170 bookings, 170 invoices,",
        "-- 103 payments, 55 users, and 10 hotel-specific Reception accounts.",
        "",
        "BEGIN;",
        "TRUNCATE " + ", ".join(qident(t) for t in tables) + " RESTART IDENTITY CASCADE;",
        "",
    ]

    for label in ORDER:
        model = models_by_label[label]
        for obj in by_label[label]:
            lines.append(insert_line(model, obj))
            if label == "hotel.roomtype":
                lines.extend(through_lines(model, obj))
        lines.append("")

    lines += ["COMMIT;", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print("objects", sum(len(v) for v in by_label.values()))


if __name__ == "__main__":
    main()
