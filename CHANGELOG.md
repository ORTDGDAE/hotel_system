# Aurelia Collection — Update Notes

Latest build: **27 September 2026** · Django 5.2 · SQLite demo DB (`aurelia_collection.db`)
Run it: `install.bat` (database setup + verify) then `start.bat` (server + public homepage, signed out).

---

## 2026-09-28 (#36) — PMS scroll-lock fix for all staff roles

- Fixed the staff/PMS document-scroll lock persisting after the mobile sidebar was opened and the viewport was resized or rotated to desktop.
- Added a desktop media override and resize/pageshow cleanup for the PMS drawer across administrator, manager, housekeeping and reception views.
- Added cache-busted `app.js` and `app.css` assets so the fix reaches the preview without stale browser files.

## 2026-09-28 (#35) — Cambodia-friendly catalog and tax-only pricing

- Lowered the live tiered catalog from **$30.00 to $460.00 per night** for a more accessible Cambodia demo price ladder.
- Changed the active demo properties to **5% tax only** with no separate service charge.
- Preserved all historical booking, folio and payment snapshots; the ledger audit now accepts valid historical snapshots when current property rates change.
- Updated booking, confirmation, invoice, email and finance copy to show tax-only pricing.
- Updated SQLite/Navicat data exports, seed defaults, tests, QA notes and presentation decks.

## 2026-09-27 (#34) — Default SQLite launch without authentication

- Changed the Windows one-click default back to local SQLite so no MySQL
  password or Navicat credential is required for a clean demo launch.
- `start.bat` now opens the public homepage signed out; the PMS dashboard stays
  protected behind the normal login route.
- MySQL/MariaDB remains available explicitly with `AURELIA_DB=mysql` and the
  private `mysql.local.bat` configuration.

## 2026-09-27 (#33) — Persistent MySQL connection defaults

- `start.bat` and `install.bat` now use MySQL defaults automatically:
  `127.0.0.1`, port `3306`, database `aurelia`, and user `root`.
- They no longer ask for the port/host/database/user on every launch; only a
  missing password is requested.
- Added `mysql.local.bat.example` for Navicat-specific host, port, database,
  user, and password values. Copy it to `mysql.local.bat` locally for a fully
  automatic launch; the real file should remain private.
- Clarified that Navicat is the GUI client: the app connects to the same
  MySQL database, while Navicat uses the same connection values to browse it.

## 2026-09-27 (#32) — Tiered room catalog pricing

- Restored differentiated nightly catalog prices across all 24 room types while
  keeping the pricing engine and rate-rule records intact.
- Entry pricing remains accessible at **$75/night**, with suites, villas,
  landmark hotels, and private-island stays increasing by room/property tier;
  the highest current catalog rate is **$1,150/night** for the Le Royal Suite.
- Updated the live catalog and future `seed_demo` runs; historical booking,
  invoice, payment, and folio snapshots were not rewritten.
- Refreshed the Navicat SQLite/MySQL exports with the tiered catalog.

## 2026-09-27 (#31) — Simple monogram logo replacement

- Replaced the previous architectural emblem with a minimal gold-on-navy
  Aurelia A monogram, without Angkor Wat, temple, skyline, or landscape imagery.
- Updated the guest and PMS brand marks, transition boot mark, favicons, and
  Apple touch icon; versioned CSS links ensure the new asset bypasses browser
  cache.
- Kept the original generated option as `static/img/logo-simple.png` and made
  it the active site logo at `static/img/logo.png`.

## 2026-09-27 (#30) — Welcome offer modal with blurred background

- Converted the 10% registration banner into a centered premium pop-up that
  appears shortly after the guest page loads.
- Added a dimmed, blurred background layer so the offer has clear focus without
  losing the Aurelia page context.
- Added a large animated 10% badge, orbit lines, coupon tile, sparkle accents,
  clear Unlock my offer CTA, private-offer copy, and a first-web-booking note.
- Preserved one-session dismissal, Escape/backdrop closing, focus restoration,
  keyboard focus trapping, responsive sizing, and reduced-motion behavior.
- Versioned the premium stylesheet so the new modal is not hidden by browser
  cache.

## 2026-09-27 (#29) — Balanced guest navigation and page background

- Added a dedicated `guest-shell` body theme so the ivory page background,
  navy navigation glass, and gold accents transition as one balanced palette.
- Stabilized the guest nav gradient, border, shadow, brand contrast, and active
  link treatment instead of allowing the translucent header to clash with the
  light body surface.
- Added versioned premium CSS loading so the visual correction is picked up
  immediately by browsers.

## 2026-09-27 (#28) — Fixed persistent navigation loading veil

- Fixed a back/forward-cache issue where the iOS-style `Loading…` layer stayed
  in the restored page DOM after navigating back to the Hotels collection.
- `pageshow` now removes stale transition layers and clears both entering and
  leaving states on every restored page.
- Added a cache-busting version to the navigation script so browsers receive
  the fix immediately; `/hotels/` returned `200` after the update.

## 2026-09-27 (#27) — MySQL/MariaDB backend and Navicat installer

- Added first-class MySQL/MariaDB settings through `AURELIA_DB=mysql` and
  `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and
  `MYSQL_PASSWORD` / `MYSQL_PWD` environment variables.
- Added PyMySQL to the project dependencies; SQLite remains an explicit
  fallback through `AURELIA_DB=sqlite`.
- Updated `start.bat` and `install.bat` to prompt for the MySQL connection,
  migrate the schema, safely copy the current SQLite snapshot into an empty
  MySQL database, run the financial audit, and keep existing MySQL data on
  later runs.
- Added `scripts/migrate_sqlite_to_mysql.py` for a repeat-safe, Django-native
  data transfer that preserves users, bookings, folios, payments, pricing,
  imagery metadata, and the latest welcome-offer snapshot fields.
- Regenerated `navicat/aurelia_collection.mysql.sql` with the current schema
  and data, including `welcome_offer_used` and `discount_total`, plus an
  offline exporter for machines without MySQL installed.
- Updated the README and Navicat guide with connection and import steps.

## 2026-09-27 (#26) — Welcome offer animation polish

- Redesigned the 10% registration banner with a premium 10% OFF badge,
  animated sheen, soft gold glow, orbit ring, sparkle accents, animated CTA,
  and a more obvious Unlock offer action.
- Kept the banner small, dismissible, responsive, and reduced-motion safe.
- The real one-time discount and signup flow remain unchanged.

## 2026-09-27 (#25) — 10% welcome offer for new registrations

- Added a small, dismissible guest-site advertisement: **10% welcome offer · Register now**.
- Signup remains the entry point; the offer is opt-in through a registered guest
  account and does not request location or external payment details.
- Added a real one-time 10% room-subtotal discount for eligible new guest
  accounts booking through the website.
- Discounted nightly rates are snapshotted into the booking, service and tax
  are calculated on the discounted subtotal, and the offer is visible on the
  booking summary, confirmation, and PMS booking detail.
- Added account and booking fields, migrations, concurrency-safe eligibility,
  and a regression test. Latest suite: **23/23 tests passed**.

## 2026-09-27 (#24) — Hotel selection confirmation feedback

- Added an animated confirmation banner after a hotel change: “Now showing
  rooms at …” with city, room-type count, and a View all hotels action.
- The status uses `role=status` / `aria-live` and respects reduced motion.
- All-hotels mode stays clean; the feedback appears only after a specific hotel
  has been selected.

## 2026-09-27 (#23) — Curated hotel recommendations

- Added a **Recommended stays / Curated for you** row to the Hotel picker with
  three collection highlights: Phnom Penh, Angkor, and Song Saa Private Island.
- Recommendation cards use the same iPhone touch treatment as the picker list,
  with a subtle lift, selection pulse, green confirmation feedback, and delayed
  navigation so the choice is perceptible.
- Recommendations are curated from real stored property records; no location
  permission or external API is requested.

## 2026-09-27 (#22) — iPhone-premium hotel picker consistency

- Replaced the native grey Hotel select on Rooms & Suites with the same
  white grouped-field treatment as the date and guests controls.
- Added a body-portalled, blurred iOS sheet with hotel icons, city labels,
  active selection checkmark, Done/Escape/outside-tap closing, and responsive
  mobile sizing.
- Kept the existing GET parameters, property filtering, and auto-submit
  behavior intact.

## 2026-09-27 (#21) — Payment total clarity

- Renamed the Payments table amount column to **Payment total**.
- Added stay context to every transaction: nights and room count.
- Added a clear pricing note explaining that payment values are complete-stay
  totals, with the $75 nightly base, 5% service, and 10% tax.
- Kept the financial ledger values intact; multi-night and multi-room totals
  are now understandable instead of appearing to contradict the low base rate.

## 2026-09-27 (#20) — Affordable demo pricing reset

- Reset all 24 active room types to the lowest existing catalog base price:
  **$75.00 per night**.
- Normalized every property to **5% service charge + 10% tax**.
- Kept the pricing engine and seasonal, promo, and weekend rate-rule records
  intact; affordable demo mode disables those rules so dated searches remain
  flat, and the $75 base is now also used by future `seed_demo --flush` runs.
- Rebuilt the demo dataset with coherent low-price booking snapshots and
  folios, then re-ran QA: **22/22 tests passed** and **2,160 invariant checks
  passed** across 170 bookings, 170 folios, 103 payments, and 369 rooms.

## 2026-09-27 (#19) — Latest-version QA hardening

- Fixed the ledger audit command so zero-total folios with no payments are
  expected to be `paid`, matching `Invoice.recalc_status()` and the repaired
  demo data.
- Added a finance regression test for the zero-balance folio rule.
- Re-ran Django checks and the full suite: **22/22 tests passed**.
- Re-ran the invariant audit: **2,166 checks passed** across 170 bookings,
  170 folios, 100 payments, and 369 rooms.
- Completed a live anonymous and per-role route crawl plus the authenticated
  Room Board SSE check with no 500 responses or tracebacks.
- Refined the hero layering so the parallax image owns the scrim once instead
  of being double-darkened by the base hero background; the hero now reads
  brighter while retaining text contrast and the approved composition.

## 2026-09-24 (#18) — Simplified primary navigation

- Removed the Map entry from both the desktop navbar and mobile menu to keep
  the primary navigation focused and easier to scan.
- The `/map/` page remains available directly, and property/location cards keep
  their dedicated “Open in Google Maps” links.

## 2026-09-24 (#17) — Key-free Google Maps browser links

- Removed the Google Maps JavaScript API integration and its key loader from
  the live application. No API key is required, stored, or sent to Google by
  the website.
- Every property, room property header, nearby attraction, map result, map
  pin, and map popup now exposes a real Google Maps URL using the public
  `maps/search/?api=1&query=latitude,longitude` browser/app link format.
- The embedded collection preview remains key-free with Leaflet/CARTO/Esri
  tiles and an offline SVG fallback; choosing “Open in Google Maps” opens the
  real Google location in a new browser tab or the Google Maps mobile app.

## 2026-09-24 (#16) — PRO MAX motion stability and mobile UX polish

- Removed the duplicate global body fade so the branded page transition no
  longer double-fades or briefly flashes during navigation.
- Made scroll reveals fail-safe: content remains visible without JavaScript,
  while the animated reveal only activates when the JS shell is present.
- Fixed same-page hash navigation so `#amenities` links scroll correctly and
  receive the expected native smooth-scroll behavior.
- Added touch-safe hover rules, mobile CTA wrapping, lighter mobile hero
  effects, scroll locking shared by all sheets, and accessible toast/status
  semantics.
- Added a proper mobile PMS drawer scrim with Escape/outside-tap closing,
  focus state attributes, and no background scrolling while open.
- Added POST double-submit protection with a clear `Working…` state, plus
  resilient live Room Board reconnection feedback and malformed-event guards.
- Cleaned the self-hosted Remix Icon font declaration to reference only the
  shipped WOFF2 asset, eliminating avoidable missing legacy-font requests.

## 2026-09-22 (#15) — QA sweep: live room stream and collection copy

- Fixed a production-visible 500 on the Room Board live SSE endpoint: the
  serializer was receiving the `Room.status_tone` method itself instead of its
  returned string. Added a regression test for the first JSON event and kept
  the stream scoped to the active PMS property.
- Corrected stale collection copy that said "Eleven hotels · Southeast Asia"
  and updated it to the current **10 sanctuaries · Cambodia** collection.
- Updated the setup scripts and seed-command help text so they no longer list
  the removed `reception.bkk` demo user or the old 11-hotel count.

## 2026-09-22 (#14) — Generated brand icon set and avatar correction

- Replaced the remaining text-based SVG `A` favicon with the generated Aurelia
  emblem across the browser favicon, iPhone home-screen icon, installable-app
  manifest, and boot splash. Added optimized 16px, 32px and 180px icon sizes.
- Restored signed-in user and staff avatars to functional username initials;
  the generated profile portrait is not used as an account avatar.
- Removed the duplicate legacy favicon link and the unused profile asset so the
  brand icon is now consistent wherever the app presents its identity.

---

## 2026-09-22 (#13) — Loading layer, designed error pages, mobile sheet menu, CSRF proxy fix

- **Loading page:** branded boot splash (gold mark pulse, 600ms fade) on every
  load + navigation loading layer (gold indeterminate top bar, glass
  "Loading…" chip with spinner after 420ms) wired into ios-nav.js transitions.
  Reduced-motion users get none of it.
- **Error pages:** designed `404.html` / `500.html` / `403.html` (glass icon
  tile, gradient display numerals, on-brand copy, gold CTAs) replace Django's
  raw technical pages.
- **Responsive fix:** ≤980px the nav collapses to a burger opening an iOS
  bottom-sheet menu (scrim, spring slide-up, safe-area padding, hairline link
  list, action buttons) — no more overflowing/wrapping nav row.
- **Real prod bug fixed:** CSRF origin check rejected every POST coming
  through the TLS preview proxy (scheme seen as http). `SECURE_PROXY_SSL_HEADER`
  is now set unconditionally; login POST through proxy verified 302.
- **Env gates:** `DJANGO_SSL_REDIRECT` (default on when DEBUG=False),
  `DJANGO_DEMO_LOGIN=1` keeps one-click demo login available in prod mode;
  blank `CSRF_TRUSTED_ORIGINS` entries filtered (Django 4+ system check).
- Preview now runs **DEBUG=False** (`--insecure` for statics) so error pages
  and prod behaviours are visible live.

## 2026-09-22 (#12) — Fix: template comment leak + centered footer

- **Bug:** the two-line `{# … #}` doc comments atop `partials/ios_dates.html`
  and `ios_guests.html` rendered as visible raw text under the hero CTA.
  Root cause: Django's tag regex has no DOTALL — inline `{# #}` comments must
  be SINGLE-LINE (multi-line needs `{% comment %}`). Collapsed both to one
  line; scanned all templates — no other multi-line inline comments exist.
- Footer recomposed center-axis: brand emblem, tagline (520px measure),
  contact line, link groups and legal bar all centered; staff column joins
  the centered family for staff roles only.

## 2026-09-21 (late #11) — Theme back to normal light (user preference)

- Removed the automatic `prefers-color-scheme: dark` layer from ios.css —
  the site now always renders the light Aurelia theme regardless of OS setting.
- `color-scheme` meta back to `light` (native controls/scrollbars light),
  single light `theme-color` for browser chrome.
- iOS materials, motion, pickers and page transitions all retained.

## 2026-09-21 (late #10) — Glitch-free picker layout: iOS modal sheets

Screenshots showed the date popover clipped by the booking card's
`overflow:hidden` (second month sliced, presets cut) and nav labels wrapping.
- Date & guests popovers now **portal to <body>** as centered iOS sheets:
  dimmed blurred scrim, spring scale-in, scroll-locked page, 2-up months on
  desktop / single month ≤640px, never clipped by any ancestor card/transform.
- Esc / scrim tap / Done close it and restore scroll.
- Nav links `white-space:nowrap` + tighter gaps at 1250/1080px breakpoints —
  no more two-line labels.

## 2026-09-21 (late #9) — Professional QA audit: 5 N+1 fixes, 1 data bug, hardening

Full audit report in **QA-REPORT.md**. Highlights:
- Query counts slashed (value-identical, parity-proven): invoices 197→7,
  analytics 133→13, PMS dashboard 78→20, rooms 54→7, hotels 34→4.
- New service helpers: `bulk_rate_rules`, `bulk_overlaps`, `occupancy_series`;
  annotation/prefetch-aware `Invoice.paid_amount`, `Booking.assigned_rooms`,
  `Property.from_price`/`sellable_rooms`; 2-query `outstanding_balance`.
- Fixed non-deterministic invoice pagination (stable `-issued_at,-id` order).
- Hardened `Invoice.recalc_status` for zero-balance folios; repaired 11 rows.
- Replaced dead `ri-satellite-line` icon with `ri-earth-line` (68/68 valid).
- Verified: 20/20 tests (warnings-as-errors), 35-URL per-role crawl all-green,
  data integrity ALL CLEAN, all static refs/images present, dev-login DEBUG-gated.

## 2026-09-21 (late #8) — iOS page transitions + site-wide dark mode

- **Page transitions** (`static/js/ios-nav.js`, both shells): every same-origin
  link and GET form animates like an iOS view change — page fades/slides up-out
  (130ms), new page springs in (340ms, Apple easing). bfcache-aware (back/
  forward restores instantly, never faded), respects prefers-reduced-motion,
  skips modified clicks, external links, downloads, POST forms and any submit
  already handled by other scripts.
- **Dark mode, automatic** (`prefers-color-scheme: dark` in ios.css): full iOS
  dark palette — #0c0c0e background, #1c1c1e raised surfaces, hairlines
  rgba(84,84,88), system dark-mode accents (blue #64b0ff, green #30d158,
  red #ff6960, amber #ff9f0a, violet #bf5af2) retokenized so every component
  (cards, tables, badges, forms, toasts, segmented tabs, date/guests popovers,
  map panel, search dock, auth glass) switches with zero template changes.
- `color-scheme` + dual `theme-color` metas in both base templates (native
  dark scrollbars/form controls, matching browser chrome).

## 2026-09-21 (late #7) — Global iOS design-system skin (`static/css/ios.css`)

Everything re-materialed in Apple's visual language, guest site **and** PMS:
- SF-style system typography stack, tight heading tracking, antialiasing.
- Buttons → iOS rounded-rects with **press-scale (0.96) feedback**; blue system
  primary, gold house gradient kept for CTAs, pill nav CTA.
- Cards → floating sheets (20px radius, hairline border, soft iOS shadow);
  property/room cards lift on hover and **press like app icons**, images zoom.
- Inputs/selects → grouped-field grey fill, 12px radius, blue focus ring,
  custom SVG chevron on selects; checkboxes → **iOS green switch toggles**.
- Tabs → **segmented controls**; tables → hairline lists with uppercase
  micro-headers; chips/badges → system capsules.
- Nav & toasts & search dock → frosted glass (blur + saturate); auth cards →
  26px glass sheets; footer hairlines; thin scrollbars; blue selection.

## 2026-09-21 (late #6) — iOS guests & rooms stepper sheet

- The three native selects (Rooms / Adults / Children) on **home + rooms list**
  collapse into one premium "Rooms & guests" field (`partials/ios_guests.html`)
  showing a live summary ("3 guests · 2 rooms (1 child)").
- Tapping opens the same frosted-glass sheet with three iOS stepper rows
  (− / value / +, circular grey buttons, blue glyphs, tap-scale, bump animation
  on the number, hairline dividers, helper captions Age 13+ / Ages 0–12).
- Limits derived from the real option ranges (rooms 1–5 or 1–8, adults 1–6,
  children 0–4); hidden selects keep the same GET params for search & pricing.

## 2026-09-21 (late #5) — iOS-style premium date-range picker

- Native browser calendars replaced on **home search dock, rooms list and room
  detail** with an iPhone-grade picker (`partials/ios_dates.html`): frosted-glass
  popover (blur + saturate), Apple spring animation, two-month spread, pill
  range highlight with rounded ends, today ring, past dates disabled.
- **Presets**: Tonight · Weekend · 3 nights · 1 week; live hover range preview;
  nights counter chip on the check-out field ("3 nights"); Clear / Done actions;
  Esc + outside-click dismiss; tap-scale micro-animation on days.
- Hidden native inputs keep the exact same GET params (`check_in`, `check_out`),
  so search, availability and pricing are untouched; room detail auto-submits
  after a completed range (as before). Staff PMS filters keep plain inputs.

## 2026-09-21 (late #4, retired 2026-09-24) — Optional FREE Google Maps key support

- `/map/` now auto-upgrades to the **official Google Maps engine** (roadmap /
  satellite / hybrid / terrain, Google's own controls, red teardrop markers,
  cluster badges, photo InfoWindows) when a key is present — otherwise it stays
  on the **key-free** CARTO/Esri/OSM tiles. No key = still fully working.
- Key sources, in order: env var `GOOGLE_MAPS_API_KEY`, or a plain text file
  **`google.key`** in the project root (one line, the key). Invalid/blocked key
  degrades gracefully back to the key-free map after a 6s watchdog.
- Get a free key (Google's $200/month free credit): console.cloud.google.com →
  new project → enable **Maps JavaScript API** → Credentials → Create
  credentials → API key → paste into `google.key`. See CHANGELOG footer recipe.

## 2026-09-21 (late #3) — `/map/` now a REAL slippy map of Cambodia

- Rebuilt on **Leaflet 1.9.4 with live raster tiles**: CARTO Voyager basemap
  (Google-Maps-look), **Satellite** (Esri World Imagery) and **Dark** styles —
  one-tap style cycler top-right, real zoom controls, real scale bar, real
  attribution strip.
- Genuine pan/zoom/inertia, **city clusters → red teardrop pins** declustering at
  zoom 9, Google-style photo popups with Rooms & Google-Maps buttons.
- Left panel (search / city chips / hotel cards) flies the real map and opens pins.
- **Offline fallback**: where tiles/CDN can't load (air-gapped preview), the page
  automatically swaps to the self-contained stylised SVG engine with a notice pill.

## 2026-09-21 (late #2) — Auth UX fix: no more mystery login failures

- **Signup** now shows a **live password checklist** (8+ chars · not only numbers ·
  not common · not your name/username · both match) that ticks green as you type,
  plus **show/hide eye toggles** on both password fields, and blocks submit until
  the basics pass — so an account can never silently fail to be created again.
- **Login** demo-accounts box is now **click-to-fill chips** (admin / manager /
  reception / housekeeping / guest) — one tap fills username + password.
- Guest account `kemkhx` (kemkhx@gmail.com) pre-created with password `Aurelia2026!`.

## 2026-09-21 (late) — `/map/` rebuilt as a Google-Maps-style interactive map

- Full-bleed map shell under the nav: **drag to pan, scroll / double-click to zoom**,
  animated fly-to, zoom +/− / reset / **dark-map theme** / fullscreen controls.
- **Google-style red teardrop pins** that keep constant screen size at every zoom;
  cities **cluster into red count badges** when zoomed out and decluster on zoom/click.
- **Info windows** (photo, stars, tagline, from-price, "Rooms & rates" + "Google Maps"
  buttons) with pointer arrow, anchored to the pin while panning.
- **Left results panel** like Google Maps: search box, city filter chips, scrollable
  hotel cards (photo · stars · city · price) — click flies to the pin and opens it.
- Stylised basemap: country outline with dashed admin border, **Tonlé Sap lake,
  Mekong + Tonlé Sap rivers, Cardamom & Bokor park shading**, neighbour-country
  labels (THAILAND / LAOS / VIETNAM / GULF OF THAILAND).
- Live **scale bar** (km, recomputed per zoom) and Google-style attribution strip.
- Zero external tiles or libraries — works offline and in the sandboxed preview.

## 2026-09-21 — Ten sanctuaries, live map & auto distances

**Collection grew from 7 to 10 properties** (all real Cambodian landmarks,
Google-Maps coordinates, real photography, original OTA-style copy):

| New sanctuary | Coordinates | Rooms & my price calls |
|---|---|---|
| Rosewood Phnom Penh (Vattanac Capital Tower) | 11.5687, 104.9309 | Premier River King $340 ×26 · Executive Sky Suite $660 ×12 |
| Sala Lodges, Siem Reap (11 heritage houses) | 13.3454, 103.8605 | Garden Sala Villa $215 ×6 · Heritage Sala House $365 ×5 |
| Song Saa Private Island (Koh Rong archipelago) | 10.7555, 103.2621 | Ocean View Villa $540 ×10 · Overwater Reserve Villa $890 ×14 |

- **Coordinates everywhere**: `Property.latitude/longitude` and
  `Attraction.latitude/longitude` (migration `hotel/0008`); all 10 properties
  and all 47 attractions geo-coded (0 missing).
- **Haversine auto-distance**: the Nearby strip now shows computed chips —
  `690 m from hotel`, `7.0 km from hotel` (metres under 1 km) — via
  `Attraction.distance_km()` / `distance_label()`; OTA text kept as fallback.
  Each property also exposes a Google-Maps deep link (`Property.maps_url`).
- **New public page `/map/`** (nav link "Map"): self-contained SVG of Cambodia
  with pulsing **city cluster pins** (Phnom Penh ×3, Siem Reap ×2, Koh Rong ×2,
  Kep, Sihanoukville, Battambang) + cluster cards with photo, stars,
  from-price, coordinates, Rooms button and Google-Maps link per property.
- **Branding**: "Ten sanctuaries. One kingdom of grace." / "10 sanctuaries · Cambodia".
- 12 new attractions for the new hotels (house-reef dive, plankton glow night
  swim, Koh Rong Sanloem day sail, Wat Phom, Russian Market, Pub Street &
  Psar Chaa, Kampong Phluk, …) — all with coordinates.
- Navicat kit regenerated **with the new schema** and re-verified:
  PostgreSQL load exit 0, MySQL load exit 0 — both `props=10 rooms=369
  coords=47 mig=32`.

**Counts now**: 10 properties · 24 room types · 369 rooms · 47 attractions ·
170 bookings · 100 payments · invoice Σ **$198,475.74** · 7 users · 32 migrations.
**Checks**: 20/20 tests · 2,166 ledger/inventory invariants PASSED.

---

## 2026-09-20/21 — Premium icon system, DB installer, sidebar fix

- **Remix Icon 4.5.0 self-hosted** (`static/css/fonts/`): every emoji/glyph in
  all 22 templates replaced with `ri-*` vector icons; amenity & attraction
  icons stored as class strings (fields widened to 40 chars, migrations
  0006/0007). Flaticon fonts need a per-account licence key, so the
  open-licence Remix family is the drop-in substitute.
- **`install.bat`** — automatic database installer: venv → deps → migrate →
  smart seed/reseed → verification table + full ledger audit → optional
  PostgreSQL/MySQL kit loads with 4-tier client resolution (PATH → common
  install folders → built-in pure-PyMySQL loader `scripts/load_kit_mysql.py`
  → Navicat GUI recipe). `start.bat` remains the one-click run+auto-login.
- **Sidebar overflow fix**: nav taller than the viewport used to spill below
  the navy panel; sidebar now scrolls internally with a thin on-theme
  scrollbar. Leftover glyphs (◧ ⏻ ＋ ℹ️) converted to `ri-*` icons.

---

## Quick verification (any time)

```bash
python manage.py test bookings          # 20/20
python manage.py audit_ledger           # every invariant PASSED
python manage.py seed_demo --flush      # rebuild demo data (10 properties)
python scripts/export_navicat_kit.py    # rebuild Navicat kit (needs PG+MySQL)
```

Demo logins (password `Aurelia2026!`): admin · manager · reception ·
manager.sr · housekeeping · housekeeping2 · guest — or open
`http://127.0.0.1:8000/auth/dev-login/admin/?next=/pms/` (DEBUG only).
