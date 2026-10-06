from __future__ import annotations

from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Aurelia_Collection_Hotel_Management_Project_Short_Deck.pptx"

# Aurelia Collection palette
NAVY = RGBColor(11, 20, 39)
NAVY2 = RGBColor(25, 52, 92)
NAVY3 = RGBColor(43, 77, 119)
GOLD = RGBColor(195, 161, 90)
PALE_GOLD = RGBColor(243, 227, 184)
IVORY = RGBColor(250, 248, 244)
BG = RGBColor(247, 248, 250)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(15, 23, 42)
MUTED = RGBColor(100, 116, 139)
GREEN = RGBColor(6, 118, 71)
BLUE = RGBColor(37, 99, 235)
RED = RGBColor(180, 35, 24)
LINE = RGBColor(226, 232, 240)
LIGHT_GREEN = RGBColor(236, 253, 243)
LIGHT_BLUE = RGBColor(239, 246, 255)
LIGHT_GOLD = RGBColor(246, 239, 223)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def shape(slide, kind, x, y, w, h, fill=None, line=None, transparency=0):
    shp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
        shp.fill.transparency = transparency
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.8)
    return shp


def rounded(slide, x, y, w, h, fill=WHITE, line=None):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, w, h, fill, line)


def rect(slide, x, y, w, h, fill, line=None):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, y, w, h, fill, line)


def circle(slide, x, y, d, fill, line=None):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x, y, d, d, fill, line)


def text(slide, value, x, y, w, h, size=14, color=INK, bold=False,
         font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = value
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return box


def bullets(slide, items, x, y, w, h, size=11, color=INK, gap=5, bullet_color=GOLD):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.text = ""
        r = p.add_run()
        r.text = "•  "
        r.font.name = "Aptos"
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = bullet_color
        r2 = p.add_run()
        r2.text = item
        r2.font.name = "Aptos"
        r2.font.size = Pt(size)
        r2.font.color.rgb = color
    return box


def background(slide, color=BG):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def footer(slide, number, dark=False):
    line_color = RGBColor(70, 92, 125) if dark else LINE
    text_color = RGBColor(185, 198, 218) if dark else RGBColor(148, 163, 184)
    rect(slide, 0.62, 7.10, 12.08, 0.008, line_color)
    text(slide, "Aurelia Collection · Hotel management project · 29 September 2026",
         0.64, 7.16, 9.5, 0.18, 8.2, text_color, margin=0)
    text(slide, f"{number:02d}", 12.15, 7.13, 0.55, 0.22, 8.5, text_color, True,
         align=PP_ALIGN.RIGHT, margin=0)


def header(slide, kicker, title, subtitle, number, dark=False):
    text(slide, kicker.upper(), 0.62, 0.38, 5.5, 0.22, 9.5, GOLD, True, margin=0)
    text(slide, title, 0.62, 0.67, 11.7, 0.55, 27,
         WHITE if dark else INK, True, "Georgia", margin=0)
    text(slide, subtitle, 0.64, 1.29, 11.35, 0.36, 11.5,
         RGBColor(205, 216, 232) if dark else MUTED, margin=0)
    text(slide, f"{number:02d}", 12.35, 0.40, 0.40, 0.22, 9,
         RGBColor(205, 216, 232) if dark else MUTED, True, align=PP_ALIGN.RIGHT, margin=0)


def card(slide, x, y, w, h, title, desc, fill=WHITE, accent=GOLD,
         title_color=INK, desc_color=MUTED, title_size=13, desc_size=10.2):
    rounded(slide, x, y, w, h, fill, LINE if fill != NAVY else None)
    rect(slide, x, y, 0.055, h, accent)
    text(slide, title, x + 0.22, y + 0.19, w - 0.35, 0.25,
         title_size, title_color, True, "Georgia", margin=0)
    text(slide, desc, x + 0.22, y + 0.61, w - 0.35, h - 0.70,
         desc_size, desc_color, margin=0)


def metric(slide, x, y, w, value, label, accent=GOLD, dark=False):
    fill = RGBColor(23, 40, 68) if dark else WHITE
    line = RGBColor(69, 92, 125) if dark else LINE
    value_color = PALE_GOLD if dark else NAVY
    label_color = RGBColor(205, 216, 232) if dark else MUTED
    rounded(slide, x, y, w, 1.05, fill, line)
    rect(slide, x, y, 0.055, 1.05, accent)
    text(slide, value, x + 0.22, y + 0.17, w - 0.30, 0.38, 24,
         value_color, True, "Georgia", margin=0)
    text(slide, label, x + 0.22, y + 0.68, w - 0.30, 0.18, 9.2,
         label_color, margin=0)


def flow_step(slide, x, y, n, title, desc, accent=GOLD):
    rounded(slide, x, y, 2.72, 1.45, WHITE, LINE)
    circle(slide, x + 0.20, y + 0.20, 0.38, accent)
    text(slide, str(n), x + 0.20, y + 0.30, 0.38, 0.10, 8.5,
         NAVY if accent == GOLD else WHITE, True, align=PP_ALIGN.CENTER, margin=0)
    text(slide, title, x + 0.72, y + 0.20, 1.78, 0.20, 11.2, INK, True, margin=0)
    text(slide, desc, x + 0.20, y + 0.76, 2.28, 0.42, 9.2, MUTED, margin=0)


# 1 — cover
s = prs.slides.add_slide(blank)
background(s, NAVY)
rect(s, 0, 0, 13.333, 0.12, GOLD)
circle(s, 10.75, -0.55, 3.0, NAVY3)
circle(s, 11.75, 5.80, 2.3, NAVY2)
text(s, "A", 0.78, 0.78, 0.72, 0.72, 28, NAVY, True, "Georgia", PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, 0)
rounded(s, 0.78, 0.78, 0.72, 0.72, GOLD, None)
text(s, "AURELIA COLLECTION", 1.72, 0.86, 5.2, 0.20, 10, PALE_GOLD, True, margin=0)
text(s, "Hotel Management\nProject", 0.78, 1.85, 8.2, 1.36, 38, WHITE, True, "Georgia", margin=0)
text(s, "A short, meaningful view of the complete guest journey,\nPMS operations, role access, pricing and deployment path.",
     0.82, 3.48, 6.5, 0.66, 15, RGBColor(205, 216, 232), margin=0)
metric(s, 0.82, 5.10, 2.02, "10", "properties", GOLD, True)
metric(s, 3.03, 5.10, 2.02, "24", "room types", BLUE, True)
metric(s, 5.24, 5.10, 2.02, "$30", "lowest rate", GREEN, True)
text(s, "Direct booking · front desk · housekeeping · finance · analytics", 8.05, 5.45, 4.15, 0.35, 12, PALE_GOLD, True, align=PP_ALIGN.RIGHT, margin=0)
text(s, "LATEST PROJECT SUMMARY · 29 SEP 2026", 8.05, 6.48, 4.15, 0.18, 9, RGBColor(185, 198, 218), True, align=PP_ALIGN.RIGHT, margin=0)
footer(s, 1, True)

# 2 — executive snapshot
s = prs.slides.add_slide(blank)
background(s, IVORY)
header(s, "Executive view", "What the project delivers", "One operating system connects guest demand to room readiness, financial control and management insight.", 2)
card(s, 0.78, 1.92, 3.78, 2.02, "The problem", "Hotel teams work across disconnected channels, spreadsheets and manual handoffs. That creates slow response, unclear ownership and risk of inventory or billing errors.", WHITE, RED)
card(s, 4.78, 1.92, 3.78, 2.02, "The answer", "Aurelia Collection combines a guest website and a role-based PMS with one reservation record, one room state and one financial snapshot.", WHITE, GOLD)
card(s, 8.78, 1.92, 3.78, 2.02, "The result", "A clear operating rhythm: discover, book, prepare, arrive, stay, check out, reconcile and improve.", WHITE, GREEN)
text(s, "The project is deliberately simple for users and disciplined underneath.", 0.82, 4.55, 11.5, 0.28, 19, NAVY, True, "Georgia", PP_ALIGN.CENTER, margin=0)
metric(s, 1.18, 5.25, 2.55, "$30", "minimum catalog rate", GOLD)
metric(s, 4.03, 5.25, 2.55, "5%", "tax only", BLUE)
metric(s, 6.88, 5.25, 2.55, "0%", "service charge", GREEN)
metric(s, 9.73, 5.25, 2.55, "1", "operating source of truth", NAVY3)
footer(s, 2)

# 3 — guest journey and channels
s = prs.slides.add_slide(blank)
background(s, BG)
header(s, "Demand to stay", "One journey, three booking channels", "Every channel ends in the same controlled reservation, inventory check and folio workflow.", 3)
flow_step(s, 0.78, 1.95, 1, "Website", "Guest searches dates, rooms and live totals, then confirms online.", GOLD)
flow_step(s, 3.68, 1.95, 2, "Walk-in / phone", "Reception creates the stay for the guest using the same rules.", NAVY3)
flow_step(s, 6.58, 1.95, 3, "OTA / agency", "Source is recorded manually today; external reference stays visible.", GREEN)
flow_step(s, 9.48, 1.95, 4, "One reservation", "Availability, price, folio, status and history remain consistent.", BLUE)
rect(s, 2.13, 3.57, 0.90, 0.035, GOLD)
rect(s, 5.03, 3.57, 0.90, 0.035, GOLD)
rect(s, 7.93, 3.57, 0.90, 0.035, GOLD)
card(s, 0.78, 4.32, 5.70, 1.54, "Guest service", "Property discovery, room details, live availability, registered-user welcome offer, confirmation and My Stays self-service.", WHITE, GOLD)
card(s, 6.84, 4.32, 5.78, 1.54, "Future channel layer", "A channel-manager integration can later add automatic OTA availability, rate, booking-import and overbooking protection.", WHITE, BLUE)
rounded(s, 0.78, 6.22, 11.84, 0.48, LIGHT_BLUE, RGBColor(191, 219, 254))
text(s, "Current boundary: OTA / agency handling is manual but controlled; automatic synchronization is future scope.", 1.04, 6.37, 11.32, 0.15, 9.7, NAVY3, True, align=PP_ALIGN.CENTER, margin=0)
footer(s, 3)

# 4 — roles
s = prs.slides.add_slide(blank)
background(s, IVORY)
header(s, "People and access", "Five roles keep the hotel moving", "Each role sees the work it owns while the platform protects shared inventory and financial records.", 4)
roles = [
    ("Guest", "Search, book, manage a personal stay", GOLD),
    ("Reception", "Reservations, arrivals, departures and payments", NAVY3),
    ("Housekeeping", "Room status, tasks and maintenance handoff", GREEN),
    ("Manager", "Rates, finance, analytics and property scope", BLUE),
    ("Administrator", "Users, configuration and full system control", NAVY),
]
for i, (title, desc, accent) in enumerate(roles):
    x = 0.78 + (i % 3) * 4.13
    y = 1.94 + (i // 3) * 1.64
    card(s, x, y, 3.63, 1.20, title, desc, WHITE, accent, title_size=13, desc_size=10.0)
rounded(s, 0.78, 5.58, 11.84, 0.76, NAVY, None)
text(s, "Access principle", 1.05, 5.78, 1.55, 0.18, 10, PALE_GOLD, True, margin=0)
text(s, "Guests see their own journey · staff operate the hotel · managers control the business · administrators control the system.", 2.66, 5.77, 9.40, 0.20, 11, WHITE, True, align=PP_ALIGN.CENTER, margin=0)
footer(s, 4)

# 5 — operations
s = prs.slides.add_slide(blank)
background(s, BG)
header(s, "Operations", "From booking to checkout", "The PMS turns a reservation into a visible operational handoff instead of a hidden manual task.", 5)
ops = [
    ("Reservation", "Dates, guests, source and total are captured."),
    ("Validation", "Availability and pricing are checked atomically."),
    ("Prepare", "Housekeeping and room status make the room sellable."),
    ("Arrive", "Reception checks in only to a ready room."),
    ("Stay", "Tasks, service issues and room condition remain visible."),
    ("Checkout", "Folio, payment, status and audit trail are closed."),
]
for i, (title, desc) in enumerate(ops):
    x = 0.78 + (i % 3) * 4.13
    y = 1.95 + (i // 3) * 1.92
    flow_step(s, x, y, i + 1, title, desc, GOLD if i in (0, 5) else NAVY3)
rounded(s, 0.78, 6.10, 11.84, 0.58, LIGHT_GREEN, RGBColor(167, 243, 208))
text(s, "Operational value: reception, housekeeping and management see the same truth at the same time.", 1.03, 6.30, 11.34, 0.18, 10.5, GREEN, True, align=PP_ALIGN.CENTER, margin=0)
footer(s, 5)

# 6 — pricing
s = prs.slides.add_slide(blank)
background(s, NAVY)
header(s, "Commercial model", "Simple pricing that is easy to trust", "The current Cambodia pricing revision starts at $30/night and applies 5% tax only.", 6, True)
rounded(s, 0.78, 1.95, 5.10, 4.62, RGBColor(23, 40, 68), RGBColor(69, 92, 125))
text(s, "Example stay", 1.12, 2.28, 2.0, 0.22, 14, PALE_GOLD, True, "Georgia", margin=0)
text(s, "$30", 1.12, 2.78, 2.1, 0.56, 38, WHITE, True, "Georgia", margin=0)
text(s, "per night", 3.16, 3.04, 1.3, 0.18, 11, RGBColor(200, 214, 233), margin=0)
calc = [("2 nights", "$60.00"), ("Welcome offer 10%", "−$6.00"), ("Taxable subtotal", "$54.00"), ("Tax 5%", "+$2.70"), ("Guest total", "$56.70")]
for i, (label, amount) in enumerate(calc):
    y = 3.75 + i * 0.43
    color = PALE_GOLD if i == 4 else RGBColor(205, 216, 232)
    text(s, label, 1.12, y, 2.55, 0.18, 10.5, color, i == 4, margin=0)
    text(s, amount, 4.10, y, 1.15, 0.18, 10.5, color, i == 4, align=PP_ALIGN.RIGHT, margin=0)
rounded(s, 6.25, 1.95, 6.37, 4.62, PALE_GOLD, None)
text(s, "Current catalog", 6.62, 2.30, 2.2, 0.22, 14, NAVY, True, "Georgia", margin=0)
text(s, "$30 → $460", 6.62, 2.76, 3.0, 0.42, 28, NAVY, True, "Georgia", margin=0)
bullets(s, ["Entry rooms: $30–$58", "Suites and city rooms: $64–$172", "Villas and premium stays: $216–$356", "Highest current catalog rate: $460", "Historical bookings keep original snapshots"], 6.62, 3.55, 5.25, 1.68, 11, NAVY, 8, GREEN)
text(s, "Service charge: 0% · Tax: 5%", 6.62, 5.84, 4.8, 0.20, 10.5, RGBColor(85, 67, 27), True, margin=0)
footer(s, 6, True)

# 7 — platform and deployment
s = prs.slides.add_slide(blank)
background(s, IVORY)
header(s, "Platform", "The PMS is modular and deployment-ready", "Start simply for a demo or small property, then connect a larger database when operational scale requires it.", 7)
modules = [
    ("Guest site", "Properties, rooms, search, booking and My Stays", GOLD),
    ("Front office", "Dashboard, reservations, calendar and folios", NAVY3),
    ("Operations", "Room Board, housekeeping and maintenance", GREEN),
    ("Business", "Rates, payments, invoices, reports and analytics", BLUE),
]
for i, (title, desc, accent) in enumerate(modules):
    x = 0.78 + (i % 2) * 3.98
    y = 1.93 + (i // 2) * 1.54
    card(s, x, y, 3.54, 1.15, title, desc, WHITE, accent, title_size=12.5, desc_size=9.6)
rounded(s, 8.95, 1.93, 3.67, 3.73, NAVY, None)
text(s, "DEPLOYMENT PATH", 9.30, 2.28, 2.55, 0.20, 9.5, PALE_GOLD, True, margin=0)
bullets(s, ["SQLite-first startup", "Windows install and start scripts", "Optional MySQL / MariaDB", "Navicat-ready database path", "Static assets and role-aware routes"], 9.30, 2.78, 2.95, 1.72, 10.5, WHITE, 8, PALE_GOLD)
text(s, "The default path is fast; the upgrade path is clear.", 9.30, 5.02, 2.92, 0.32, 10, RGBColor(205, 216, 232), True, margin=0)
rounded(s, 0.78, 5.35, 7.68, 0.60, LIGHT_BLUE, RGBColor(191, 219, 254))
text(s, "Technical handoff: preserve the same models and workflows when moving from SQLite to MySQL/MariaDB.", 1.03, 5.57, 7.18, 0.16, 9.8, NAVY3, True, align=PP_ALIGN.CENTER, margin=0)
footer(s, 7)

# 8 — safeguards
s = prs.slides.add_slide(blank)
background(s, BG)
header(s, "Trust layer", "Simple screens, disciplined controls", "The system is designed to make the safe path the easiest path for hotel teams.", 8)
controls = [
    ("Inventory", "Every night is checked before a booking is created.", NAVY3),
    ("Pricing", "Rate, discount, tax and total are stored with the stay.", GOLD),
    ("Room readiness", "Only vacant-clean rooms can be assigned at arrival.", GREEN),
    ("Cancellation", "Policy and refund records are applied consistently.", RED),
    ("Access", "Role scope separates guest, operations, manager and admin work.", BLUE),
    ("Audit", "Ledger, inventory and financial invariants are checked.", NAVY),
]
for i, (title, desc, accent) in enumerate(controls):
    x = 0.78 + (i % 3) * 4.13
    y = 1.95 + (i // 3) * 1.68
    card(s, x, y, 3.63, 1.25, title, desc, WHITE, accent, title_size=12.5, desc_size=9.8)
rounded(s, 0.78, 5.70, 11.84, 0.66, NAVY, None)
text(s, "Release confidence", 1.05, 5.93, 1.65, 0.17, 10, PALE_GOLD, True, margin=0)
text(s, "23/23 tests passed · 2,160 ledger invariants passed · 10 properties and 24 room types updated", 2.86, 5.91, 9.25, 0.20, 10.7, WHITE, True, align=PP_ALIGN.CENTER, margin=0)
footer(s, 8)

# 9 — owner outcomes
s = prs.slides.add_slide(blank)
background(s, IVORY)
header(s, "Owner outcomes", "What the hotel team gains", "The project is measured by operational clarity, not by the number of screens it contains.", 9)
card(s, 0.78, 1.95, 3.78, 2.12, "For the owner", "A chain-level view of demand, occupancy, ADR, revenue, payments and open folio balances.", WHITE, GOLD)
card(s, 4.78, 1.95, 3.78, 2.12, "For the guest", "Clear room choices, transparent total pricing, direct booking convenience and self-service stay management.", WHITE, BLUE)
card(s, 8.78, 1.95, 3.78, 2.12, "For the front desk", "One reservation workflow for web, walk-in, phone and agency demand with fewer handoff errors.", WHITE, GREEN)
text(s, "The meaningful change", 0.82, 4.70, 3.0, 0.25, 17, NAVY, True, "Georgia", margin=0)
bullets(s, ["The hotel can see what is happening now.", "The team knows who owns the next action.", "The owner can trust how totals were calculated.", "The technology can grow without changing the hotel’s operating language."], 0.82, 5.18, 11.0, 1.18, 12, INK, 8, GOLD)
footer(s, 9)

# 10 — demonstration sequence
s = prs.slides.add_slide(blank)
background(s, NAVY)
header(s, "Demonstration", "The shortest meaningful walkthrough", "Use this sequence to show the project end to end in a few minutes.", 10, True)
sequence = [
    ("1", "Open the website", "Show the public guest experience."),
    ("2", "Search a $30 room", "Show dates, inventory and tax-only total."),
    ("3", "Confirm a stay", "Show offer, confirmation and My Stays."),
    ("4", "Open the PMS", "Show dashboard and reservation record."),
    ("5", "Create a walk-in", "Show controlled manual booking."),
    ("6", "Operate the room", "Show check-in, Room Board and tasks."),
    ("7", "Close the stay", "Show checkout, folio and payment."),
    ("8", "Show the next step", "Explain MySQL and future OTA connection."),
]
for i, (n, title, desc) in enumerate(sequence):
    x = 0.78 + (i % 4) * 3.08
    y = 1.95 + (i // 4) * 1.65
    rounded(s, x, y, 2.67, 1.24, RGBColor(23, 40, 68), RGBColor(69, 92, 125))
    circle(s, x + 0.20, y + 0.20, 0.34, GOLD if i < 4 else NAVY3)
    text(s, n, x + 0.20, y + 0.29, 0.34, 0.10, 8.5, NAVY if i < 4 else WHITE, True, align=PP_ALIGN.CENTER, margin=0)
    text(s, title, x + 0.68, y + 0.20, 1.72, 0.18, 10.4, WHITE, True, margin=0)
    text(s, desc, x + 0.20, y + 0.69, 2.18, 0.30, 9.0, RGBColor(205, 216, 232), margin=0)
rounded(s, 0.78, 5.72, 11.84, 0.76, PALE_GOLD, None)
text(s, "Next handoff: verify the owner’s MySQL/Navicat connection, then add live OTA synchronization when ready.", 1.04, 5.99, 11.34, 0.20, 11, NAVY, True, align=PP_ALIGN.CENTER, margin=0)
text(s, "Aurelia Collection · short project deck", 0.80, 6.68, 3.8, 0.16, 9, RGBColor(185, 198, 218), margin=0)
footer(s, 10, True)

prs.core_properties.title = "Aurelia Collection — Hotel Management Project · Short Deck"
prs.core_properties.subject = "Concise end-to-end hotel management project overview"
prs.core_properties.author = "Aurelia Collection"
prs.core_properties.keywords = "hotel management, PMS, guest website, roles, pricing, operations, deployment"
prs.save(OUT)
print(OUT)
