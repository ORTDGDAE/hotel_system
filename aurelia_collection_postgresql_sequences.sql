-- Aurelia Collection — PostgreSQL identity-sequence repair
--
-- COMPANION to aurelia_collection_postgresql_latest.sql. That dump is left
-- byte-for-byte untouched; this is a separate, optional second step.
--
-- WHY THIS IS NEEDED
--   The data dump opens with TRUNCATE ... RESTART IDENTITY CASCADE, which
--   resets every identity sequence to 1, then inserts rows with EXPLICIT
--   primary keys. It contains no setval() calls. So after the import every
--   sequence sits at 1 while the tables hold ids far above it:
--
--       hotel_room        369 rows   max id 1851
--       bookings_booking  170 rows   max id 1069
--       finance_invoice   170 rows   max id 1069
--       finance_payment   103 rows   max id  666
--       accounts_user      55 rows   max id   56
--       hotel_property     10 rows   max id   61
--
--   The first row the application creates is then offered id = 1 and
--   PostgreSQL rejects it:
--       duplicate key value violates unique constraint "accounts_user_pkey"
--   A new guest signup or a new booking fails immediately. hotel_room is
--   worse: ids 1-1500 are free, so new rooms insert happily for weeks and
--   only then begin colliding.
--
-- HOW TO RUN IT (after the data dump, in the same session or a new one)
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f aurelia_collection_postgresql_latest.sql
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f aurelia_collection_postgresql_sequences.sql
--
-- SAFE TO RE-RUN: each statement only ever moves a sequence forward to
-- MAX(id). pg_get_serial_sequence() resolves the owning sequence by name,
-- so this stays correct if the data export is regenerated with new ids.

BEGIN;

SELECT setval(pg_get_serial_sequence('"accounts_user"', 'id'), COALESCE((SELECT MAX("id") FROM "accounts_user"), 1), true);
SELECT setval(pg_get_serial_sequence('"bookings_booking"', 'id'), COALESCE((SELECT MAX("id") FROM "bookings_booking"), 1), true);
SELECT setval(pg_get_serial_sequence('"bookings_raterule"', 'id'), COALESCE((SELECT MAX("id") FROM "bookings_raterule"), 1), true);
SELECT setval(pg_get_serial_sequence('"bookings_roomassignment"', 'id'), COALESCE((SELECT MAX("id") FROM "bookings_roomassignment"), 1), true);
SELECT setval(pg_get_serial_sequence('"finance_invoice"', 'id'), COALESCE((SELECT MAX("id") FROM "finance_invoice"), 1), true);
SELECT setval(pg_get_serial_sequence('"finance_payment"', 'id'), COALESCE((SELECT MAX("id") FROM "finance_payment"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_amenity"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_amenity"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_attraction"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_attraction"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_property"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_property"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_room"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_room"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_roomtype"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_roomtype"), 1), true);
SELECT setval(pg_get_serial_sequence('"hotel_roomtype_amenities"', 'id'), COALESCE((SELECT MAX("id") FROM "hotel_roomtype_amenities"), 1), true);   -- ids auto-assigned by the dump; included for completeness
SELECT setval(pg_get_serial_sequence('"operations_housekeepingtask"', 'id'), COALESCE((SELECT MAX("id") FROM "operations_housekeepingtask"), 1), true);
SELECT setval(pg_get_serial_sequence('"operations_maintenancerequest"', 'id'), COALESCE((SELECT MAX("id") FROM "operations_maintenancerequest"), 1), true);

COMMIT;

-- VERIFY: each last_value must equal the max id in its table.
--   psql "$DATABASE_URL" -c "SELECT last_value FROM accounts_user_id_seq;"  -- expect 56
--   psql "$DATABASE_URL" -c "SELECT last_value FROM hotel_room_id_seq;"      -- expect 1851
