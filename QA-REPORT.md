# QA Audit Report — Aurelia Collection (Hotel Booking & PMS)

**Date:** 2026-09-29 · **Auditor:** automated deep-dive + latest-version follow-up (static checks, per-role live crawl, SSE validation, data-integrity audit, asset verification)
**Verdict:** ✅ QA clean for the demo release — 1 audit/model consistency defect was fixed, the regression suite is green, and the live route/SSE crawl passed with expected auth and role gates.

---

## 0.1 Latest-version QA closure — 2026-09-29

The latest role, task-board, route-authorization, and end-to-end business-flow
changes were re-verified. The implementation is functionally healthy and the
persistent demo database was restored after the intentionally mutating pipeline
proof.

- Full Django suite: **41/41 passed**; `manage.py check`: passed with no issues.
- `manage.py audit_ledger`: **2,160 invariant checks passed** on the restored demo dataset: 170 bookings, 170 folios, 103 payments, and 369 rooms.
- `scripts/pipeline_proof.py`: all booking, pricing, payment, refund, room-state, housekeeping, no-show, and audit assertions passed; the proof audit reached **2,219 checks**.
- The proof's five temporary bookings and related rows were explicitly removed afterward. Final counts match the pre-proof dataset, and a post-cleanup ledger audit passed.
- Schema and dependencies: `makemigrations --check --dry-run` reported no changes, all migrations are applied, `pip check` passed, Python compilation passed, and JavaScript syntax checks passed for `app.js` and `ios-nav.js`.
- Route and role smoke coverage passed for guest, reception, manager, housekeeping, and admin. Housekeeping is restricted to its assigned task board, while manager/admin retain complete task visibility and assignment controls.
- Production-mode `check --deploy` passed with only the optional HSTS preload warning; the expected development-mode warnings remain only when `DEBUG=True`.
- Invoice regression fixed: per-night amount now multiplies quantity correctly (`$75 × 2 = $150`), and the tax label is derived from the invoice snapshot rather than hard-coded. Existing historical folios are intentionally preserved; new bookings remain 5% tax-only with no service charge.
- Guest booking contact validation now requires a phone number, uses a telephone-optimized input, shows a required-field hint/error, and rejects non-phone text.
- Dirty-room workflow strengthened: check-out and manual dirty-status changes create or reuse one cleaning task; the management Room Board shows task status, room type, assignee, and assignment-needed state; completion returns vacant-dirty rooms to vacant-clean.
- Departure payment workflow clarified: paid folios show `Paid in full`; outstanding folios expose `Record deposit`, with partial deposits allowed up to the balance due and a clear payment/deposit form on the booking detail.
- Multi-property management upgraded: `Group Manager` retains chain-wide control, while `Property Manager` accounts are fixed to one assigned hotel; direct booking, invoice, room, finance, staff, pricing, analytics, and task access is property-scoped and cross-hotel URLs are denied.
- The current demo has one group manager plus one property-manager account for each active hotel; all property-manager demo accounts use the existing demo password.
- Housekeeping teams are now grouped by hotel: **three cleaners per hotel** (30 cleaners across 10 hotels), and Property Manager assignment lists are limited to the active hotel’s team.
- The preview server remains live on `0.0.0.0:8000`.

Role acceptance is satisfied: Housekeeping sees only its own pending, in-progress,
and completed tasks; cannot access unassigned or other staff work; can start and
complete only its own assigned tasks; and is redirected away from management,
reservations, room-board, maintenance, finance, analytics, staff-directory,
property-management, and property-switching routes. Automatic checkout/nightly
task creation and existing room-status, inventory, pricing, payment,
cancellation, folio, and ledger rules remain covered and green.

---

## 0. Latest-version follow-up — 2026-09-27

The latest project version was tested after the zero-balance folio audit mismatch was
reproduced. The defect was in the audit command's expected-status calculation: it
classified zero-total, unpaid folios as `open` even though
`Invoice.recalc_status()` correctly classifies them as `paid`. The audit rule now
matches the model rule, and a finance regression test protects the behavior.

- `python3 manage.py check`: passed with no issues.
- `python3 manage.py test`: **23/23 passed** (including the zero-balance folio and one-time welcome-offer regression tests).
- `python3 manage.py audit_ledger`: **passed — 2,160 invariant checks** across 170 bookings, 170 folios, 103 payments, and 369 rooms.
- Catalog pricing is now Cambodia-friendly and tiered across the 24 active room types, from **$30.00/night** for the entry-level Colonial Room to **$460.00/night** for the Le Royal Suite; the current demo uses **5% tax only** with no separate service charge. Rate-rule records remain available in the PMS, but are disabled so dated searches stay flat at each room type's rack rate. Historical booking and financial snapshots were not rewritten.
- JavaScript syntax checks (`app.js`, `ios-nav.js`): passed.
- Local CSS asset audit: passed.
- Anonymous public crawl: home, health, collection, rooms, map, auth pages, designed 404 all returned expected 200/404 responses.
- Auth/role crawl: guest, reception, manager, housekeeping, and admin demo sessions returned expected 200s or login/permission 302 gates across dashboard, PMS, operations, finance, and analytics.
- Room Board SSE: **200 `text/event-stream`**, first event parsed as JSON for all 369 rooms; active-property scoping remained intact.
- No 500 response or traceback was observed during the live crawl.
- Finance UI clarification: Payments now labels the amount as a full payment total, shows nights/rooms for each booking, and explains the $30 lowest nightly base plus 5% tax only. The underlying historical totals remain correct rather than being flattened.
- Rooms & Suites UI consistency: the Hotel selector now uses the same iPhone-premium grouped field and body-portalled selection sheet as dates and guests; public room routes returned 200 before and after the change.
- The Hotel sheet now includes three curated recommendation cards with touch lift, selection pulse, and visible selection feedback; no geolocation permission or external API is requested.
- Choosing a specific hotel now produces an animated accessible confirmation banner with the selected hotel, city, room-type count, and a return-to-all-hotels action; all-hotels mode remains clean.
- Anonymous guests now see a dismissible 10% welcome-offer ad linking to signup. Eligible newly registered guests receive the one-time discount in the booking, folio, confirmation, cancellation-fee basis, and payment flow; eligibility and one-time consumption are regression-tested.
- The welcome ad received a visual polish pass with an animated 10% badge, sheen, gold glow, sparkle accents, CTA motion, responsive behavior, and reduced-motion fallback; guest home returned `200` after the update.
- Fixed the iOS navigation loading veil persisting after back/forward-cache restoration; `ios-nav.js` now clears stale layers on `pageshow`, and `/hotels/` returned `200` with the versioned fix.
- Added the `guest-shell` palette correction for the navigation/body transition: stable navy glass navigation, gold hairline, and ivory gradient body; `/hotels/` returned `200` with versioned premium CSS.
- Converted the welcome advertisement into a delayed centered modal with a blurred/dimmed background, responsive animation, Escape/backdrop closing, focus restoration/trapping, and reduced-motion support; anonymous `/hotels/` returned `200` with the versioned popup CSS.
- Replaced the active architectural brand artwork with the approved simple gold A monogram; guest home returned `200`, Django checks passed, and the active logo matches `logo-simple.png`.
- Windows one-click launch now defaults to SQLite with no MySQL password prompt and opens the public homepage signed out; the PMS dashboard remains login-protected. MySQL/Navicat remains an explicit opt-in.
- Fixed the PMS scroll-lock edge case after opening the mobile staff sidebar and resizing/rotating to desktop; the cleanup now applies to administrator, manager, housekeeping and reception shells, with cache-busted staff assets.

The 302 responses are intentional authentication/permission boundaries. The
404 is the designed error page, and the POST-only cancellation behavior remains
covered by the test suite.

## 0a. Follow-up regression — 2026-09-24

A second live regression pass was run after the motion, navigation, live Room
Board, and key-free Google Maps changes:

- **21/21 Django tests passed** and `manage.py check` reported no issues.
- Guest shell, authentication pages, hotel collection, map, health probe,
  all **24 room detail URLs**, and designed 404 were checked.
- Guest dashboard and staff/PMS, operations, finance, analytics, reservation,
  and invoice routes all returned their expected 200/302/405 responses.
- Room Board SSE returned **200** with valid JSON for all **369 rooms**;
  malformed-event handling and active-property scoping are regression-tested.
- Map page returned **200** without any Google Maps API loader or API-key
  reference. Real property and attraction links use Google’s public
  `maps/search/?api=1&query=latitude,longitude` browser/app URL format.
- Desktop and mobile primary navigation no longer contains the Map item;
  direct map/location links remain available from relevant content.
- JavaScript syntax, inline map JavaScript, local CSS assets, and self-hosted
  Remix Icon WOFF2 loading all passed. No 500 response or traceback appeared
  in the live server log during the crawl.

The 405 observed on `GET /bookings/cancel/<id>/` is intentional because
cancellation is a POST-only operation; the 404 observed for the synthetic QA
URL is the designed error page, not an application failure.

## 1. Scope & method

| Layer | Technique | Result |
|---|---|---|
| Static | `manage.py check` / `check --deploy` | 0 issues; 6 deploy warnings — all dev-mode-only (hardening block activates when `DEBUG=False`) ✓ |
| Tests | Full suite, warnings-as-errors | **21/21 OK**, no `UnorderedObjectListWarning` after fix |
| Routes | Crawl of 35 URLs as anon / admin / reception / housekeeping / guest | All expected codes: 200s, correct 302 login/role gates, clean 404, 405 on POST-only create ✓ |
| Performance | Per-page SQL query counting (`CaptureQueriesContext`) | 5 N+1 hotspots found → fixed (table below) |
| Data integrity | Double-assignment, oversell, ledger-vs-status, orphans, overcapacity, stale stays | **ALL CLEAN** (after 1 repair, §4) |
| Assets | Every `{% static %}` ref, every `ri-*` icon class, every `image_url` | 0 missing statics; 1 missing icon fixed; 34/34 images present |
| Security | dev-login gating, auth decorators, settings | `dev_login` DEBUG-gated (404 in prod) ✓; staff/manager decorators on all back-office routes ✓ |

## 2. Performance defects found & fixed

| Page | Before | After | Root cause → fix |
|---|---:|---:|---|
| `/finance/invoices/` | **197 q** | **7 q** | `Invoice.paid_amount` ran a payments query per row (×2 via `balance`), and `outstanding_balance()` looped all open folios with per-row queries → annotated `paid_total` (Coalesce+Sum), made property annotation/prefetch-aware, rewrote `outstanding_balance()` to 2 queries |
| `/analytics/` | **133 q** | **13 q** | `occupancy_for_date()` called **61×** (two overlapping 30-day loops) → new `occupancy_series()` computes the whole span in 2 queries; one series now feeds KPI + average + chart |
| `/pms/` dashboard | **78 q** | **20 q** | `assigned_rooms` property queried per booking row (44 q) + per-row `invoice`/`payments` (23 q) → prefetch-aware property + `Prefetch("room_assignments")` + `select_related("invoice")` + `prefetch_related("invoice__payments")` |
| `/rooms/` | **54 q** | **7 q** | Per-type `price_stay`/`available_rooms` each ran queries → new `bulk_rate_rules()` + `bulk_overlaps()` fetched once and threaded through (also speeds up dated search: **11 q** total) |
| `/hotels/` | **34 q** | **4 q** | Per-property `from_price` aggregate, `sellable_rooms` count, `room_types.count` → single annotated queryset (`from_price_ann`, `sellable_ann`, `rt_count`), properties made annotation-aware |

All optimizations verified **value-identical** to the old code paths (parity harness: 30-day occupancy × per-day recompute, 24 room types priced both ways, 10 properties sellable-count both ways — zero mismatches). All new parameters are optional → every existing caller unaffected.

## 3. Correctness bug found & fixed

- **Non-deterministic invoice pagination** — `Paginator` over an unordered (annotate/grouped) queryset could duplicate/skip rows across pages. Fixed with explicit `.order_by("-issued_at", "-id")` (stable tie-break). Surfaced by running the suite with warnings-as-errors.
- **Dead icon** — `ri-satellite-line` (map Satellite toggle) doesn't exist in the self-hosted Remix Icon build → rendered as an empty box. Replaced with `ri-earth-line`. 67/68 icons were valid; now 68/68.

## 4. Data hygiene

- **11 zero-balance folios** of cancelled bookings were stuck `open` forever (`recalc_status` had no total=0 branch) — polluting "open invoices" filters/KPIs. Hardened `recalc_status()` (zero-balance + no payments ⇒ `paid`; refund branch still wins) and repaired the 11 rows. Re-audit: **ALL CLEAN** across 170 bookings / 170 invoices / 100 payments / 41 room assignments.

## 5. Confirmed-healthy (no action needed)

- Booking engine: half-open interval overlap math, peak-night room counting, capacity & stay-length validation, cancellation fee flow — all covered by tests and the integrity probe.
- Role model: anon → login redirects; guest → PMS/finance blocked; reception → analytics blocked (manager+); housekeeping → ops-only. `staff_directory` already staff-gated.
- Security posture: secret key via env, HSTS/SSL-redirect/secure-cookie block auto-activates when `DEBUG=False`, `X_FRAME_OPTIONS=DENY`, CSRF middleware on, dev-login 404s in prod.

## 6. Recommended next steps (not blockers)

1. **Tests for the new batch paths** — parity was proven by harness; fold a few assertions into `bookings/tests.py`.
2. **DB indexes** — `Booking(status, check_in, check_out)` composite index would keep `bulk_overlaps` fast at 100k+ rows.
3. **Sentry/structured logging** in production (LOGGING block already prepared).
4. **Select-or-async for reports** — `/finance/reports/` (12 q) is fine now; if ledger volume grows, aggregate in SQL rather than Python loops.
