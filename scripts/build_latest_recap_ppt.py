from __future__ import annotations

from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Aurelia_Collection_Latest_Release_Recap.pptx"
IMG = ROOT / "static" / "img"

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
BLUE = RGBColor(0, 122, 255)
LINE = RGBColor(226, 232, 240)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def rgb(hex_value: str) -> RGBColor:
    hex_value = hex_value.lstrip("#")
    return RGBColor(int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16))


def shape(slide, kind, x, y, w, h, fill=None, line=None, radius=False, transparency=0):
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


def rounded(slide, x, y, w, h, fill=WHITE, line=None, transparency=0):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, w, h, fill, line, transparency=transparency)


def rect(slide, x, y, w, h, fill, line=None, transparency=0):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, y, w, h, fill, line, transparency=transparency)


def circle(slide, x, y, d, fill, line=None, transparency=0):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x, y, d, d, fill, line, transparency=transparency)


def text(slide, value, x, y, w, h, size=14, color=INK, bold=False, font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, italic=False, margin=0.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return box


def rich_text(slide, runs, x, y, w, h, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    for item in runs:
        run = p.add_run()
        run.text = item.get("text", "")
        run.font.name = item.get("font", "Aptos")
        run.font.size = Pt(item.get("size", 14))
        run.font.bold = item.get("bold", False)
        run.font.color.rgb = item.get("color", INK)
    return box


def bullets(slide, items, x, y, w, h, size=14, color=INK, gap=6, bullet_color=GOLD):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.level = 0
        p.alignment = PP_ALIGN.LEFT
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


def add_image(slide, path, x, y, w, h, transparency=0):
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    if transparency:
        # python-pptx does not expose picture transparency reliably; overlay handles this.
        rect(slide, x, y, w, h, NAVY, transparency=transparency)
    return pic


def header(slide, kicker, title, subtitle=None, dark=False, number=None):
    color = WHITE if dark else INK
    muted = RGBColor(205, 216, 232) if dark else MUTED
    text(slide, kicker.upper(), 0.62, 0.43, 4.8, 0.22, size=9.5, color=GOLD, bold=True, font="Aptos", margin=0)
    text(slide, title, 0.62, 0.70, 11.7, 0.58, size=27, color=color, bold=True, font="Georgia", margin=0)
    if subtitle:
        text(slide, subtitle, 0.64, 1.32, 11.3, 0.34, size=11.5, color=muted, margin=0)
    if number is not None:
        text(slide, f"{number:02d}", 12.35, 0.45, 0.4, 0.22, size=9, color=muted, bold=True, align=PP_ALIGN.RIGHT, margin=0)


def footer(slide, number, dark=False):
    color = RGBColor(185, 198, 218) if dark else RGBColor(148, 163, 184)
    rect(slide, 0.62, 7.13, 12.08, 0.008, GOLD if dark else LINE)
    text(slide, "Aurelia Collection · Latest release recap · 27 September 2026", 0.64, 7.19, 7.4, 0.18, size=8.2, color=color, margin=0)
    text(slide, f"{number:02d}", 12.15, 7.16, 0.55, 0.22, size=8.5, color=color, bold=True, align=PP_ALIGN.RIGHT, margin=0)


def stat_card(slide, x, y, w, h, value, label, accent=GOLD, dark=False):
    fill = RGBColor(23, 40, 68) if dark else WHITE
    line = RGBColor(69, 92, 125) if dark else LINE
    rounded(slide, x, y, w, h, fill, line)
    rect(slide, x, y, 0.055, h, accent)
    text(slide, value, x + 0.2, y + 0.2, w - 0.35, 0.43, size=23, color=PALE_GOLD if dark else NAVY, bold=True, font="Georgia", margin=0)
    text(slide, label, x + 0.2, y + 0.72, w - 0.35, h - 0.78, size=10.5, color=RGBColor(201, 211, 227) if dark else MUTED, bold=True, margin=0)


def icon_badge(slide, x, y, label, fill=GOLD, color=NAVY, d=0.36):
    circle(slide, x, y, d, fill)
    text(slide, label, x, y + 0.01, d, d - 0.02, size=12, color=color, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)


def photo_card(slide, path, x, y, w, h, title, subtitle):
    rounded(slide, x, y, w, h, WHITE, LINE)
    add_image(slide, path, x, y, w, 1.35)
    rect(slide, x, y + 1.13, w, 0.22, NAVY, transparency=12)
    text(slide, title, x + 0.16, y + 1.50, w - 0.3, 0.28, size=14, color=INK, bold=True, font="Georgia", margin=0)
    text(slide, subtitle, x + 0.16, y + 1.84, w - 0.3, h - 1.94, size=10.5, color=MUTED, margin=0)


def add_slide_bg(slide, color=BG):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


# 1. Cover
slide = prs.slides.add_slide(blank)
add_image(slide, IMG / "hero.jpg", 0, 0, 13.333, 7.5)
rect(slide, 0, 0, 13.333, 7.5, NAVY, transparency=22)
rect(slide, 0, 0, 13.333, 7.5, NAVY, transparency=46)
add_image(slide, IMG / "logo-simple.png", 0.72, 0.66, 0.78, 0.78)
text(slide, "AURELIA COLLECTION", 1.72, 0.78, 5.4, 0.3, size=16, color=PALE_GOLD, bold=True, margin=0)
text(slide, "Hotel Booking & Property Management System", 0.76, 2.05, 11.3, 0.52, size=31, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "Latest release recap", 0.78, 2.72, 6.5, 0.42, size=22, color=PALE_GOLD, font="Georgia", margin=0)
text(slide, "A polished guest experience, operational PMS, financially consistent booking flow, and MySQL/Navicat-ready deployment path.", 0.8, 3.45, 7.2, 0.7, size=14, color=RGBColor(225, 232, 242), margin=0)
rounded(slide, 0.8, 5.65, 3.5, 0.6, RGBColor(255,255,255), None, transparency=86)
text(slide, "BUILD 27 SEPTEMBER 2026", 1.02, 5.84, 3.05, 0.18, size=9.5, color=PALE_GOLD, bold=True, margin=0)
text(slide, "Cambodia · 10 sanctuaries · One standard of grace", 0.82, 6.65, 7.5, 0.22, size=10, color=RGBColor(215, 225, 238), margin=0)

# 2. Executive snapshot
slide = prs.slides.add_slide(blank)
add_slide_bg(slide)
header(slide, "Release snapshot", "What shipped in the latest version", "The product is now a coherent end-to-end hotel platform, not just a booking front end.", number=2)
stat_card(slide, 0.72, 1.92, 2.78, 1.2, "10", "Cambodia properties", GOLD)
stat_card(slide, 3.68, 1.92, 2.78, 1.2, "24", "Room types", NAVY3)
stat_card(slide, 6.64, 1.92, 2.78, 1.2, "369", "Physical rooms", GREEN)
stat_card(slide, 9.60, 1.92, 2.78, 1.2, "23/23", "Django tests passing", BLUE)
rounded(slide, 0.72, 3.55, 5.85, 2.65, WHITE, LINE)
text(slide, "The release pillars", 1.0, 3.83, 4.7, 0.25, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
items = [
    ("01", "Guest journey", "Collection discovery, room search, mobile navigation and signup conversion."),
    ("02", "PMS operations", "Reservations, room board, housekeeping, folios, payments and reporting."),
    ("03", "Commercial logic", "Tiered rack rates, rate-rule records, snapshots and one-time welcome offer."),
    ("04", "Deployment path", "MySQL/MariaDB configuration, SQLite transfer, Navicat SQL export and one-click scripts."),
]
for i, (num, title, desc) in enumerate(items):
    yy = 4.23 + i * 0.45
    icon_badge(slide, 1.0, yy + 0.01, num, fill=PALE_GOLD, d=0.27)
    text(slide, title, 1.38, yy, 1.45, 0.19, size=10.5, color=INK, bold=True, margin=0)
    text(slide, desc, 2.75, yy, 3.35, 0.3, size=9.3, color=MUTED, margin=0)
rounded(slide, 6.86, 3.55, 5.52, 2.65, NAVY, None)
text(slide, "Release signal", 7.18, 3.83, 3.6, 0.25, size=14, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "A premium guest shell backed by operationally credible hotel data and a verified financial ledger.", 7.18, 4.22, 4.7, 0.75, size=18, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "Current preview remains available on port 8000 while the user-owned MySQL connection is configured.", 7.18, 5.35, 4.55, 0.42, size=10.5, color=RGBColor(199, 212, 231), margin=0)
footer(slide, 2)

# 3. Guest experience
slide = prs.slides.add_slide(blank)
add_slide_bg(slide)
header(slide, "Guest experience", "A calmer, more premium path to booking", "The public site now balances editorial hospitality, responsive interaction, and clear conversion moments.", number=3)
photo_card(slide, IMG / "props" / "rosewood.jpg", 0.72, 1.86, 3.78, 3.22, "Discover the collection", "Real Cambodia properties, city context, vibe tags, pricing and map links in one glance.")
photo_card(slide, IMG / "props" / "sala-lodges.jpg", 4.78, 1.86, 3.78, 3.22, "Choose with confidence", "Curated hotel recommendations, animated selection feedback and accessible picker sheets.")
photo_card(slide, IMG / "props" / "song-saa.jpg", 8.84, 1.86, 3.78, 3.22, "Book the right stay", "Rooms, suites and island villas lead into a consistent, responsive booking flow.")
rounded(slide, 0.72, 5.45, 11.9, 0.92, WHITE, LINE)
icon_badge(slide, 1.0, 5.72, "✓", fill=GREEN, color=WHITE, d=0.33)
text(slide, "Guest-facing details", 1.48, 5.63, 1.8, 0.19, size=10.5, color=INK, bold=True, margin=0)
text(slide, "Responsive navigation · curated hotel picker · Google Maps public links · bfcache-safe page transitions · designed 404 and auth boundaries", 3.23, 5.63, 8.95, 0.3, size=10.5, color=MUTED, margin=0)
footer(slide, 3)

# 4. Pricing and offer
slide = prs.slides.add_slide(blank)
add_slide_bg(slide, IVORY)
header(slide, "Commercial logic", "Tiered pricing with a real welcome conversion offer", "Rack rates vary by room and property tier; booking snapshots remain financially authoritative.", number=4)
rounded(slide, 0.72, 1.82, 5.1, 4.82, NAVY, None)
text(slide, "Current catalog ladder", 1.03, 2.15, 3.3, 0.25, size=14, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "$30", 1.03, 2.62, 2.15, 0.55, size=34, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "entry rate", 3.12, 2.82, 1.3, 0.2, size=11, color=RGBColor(200, 214, 233), margin=0)
levels = [("Entry", "$30", 0.24), ("Suites", "$86–$172", 0.42), ("Landmark", "$128–$460", 0.75), ("Private island", "$216–$356", 0.61)]
for i, (lab, val, width) in enumerate(levels):
    yy = 3.45 + i * 0.56
    text(slide, lab, 1.03, yy, 1.1, 0.18, size=10, color=RGBColor(198, 210, 229), margin=0)
    rect(slide, 2.2, yy + 0.03, 2.95 * width, 0.12, GOLD if i < 2 else PALE_GOLD)
    text(slide, val, 4.24, yy - 0.04, 1.18, 0.22, size=10, color=WHITE, bold=True, align=PP_ALIGN.RIGHT, margin=0)
text(slide, "24 room types · rules remain in the PMS but are disabled for flat dated demo searches.", 1.03, 5.86, 4.25, 0.45, size=10.5, color=RGBColor(197, 210, 229), margin=0)
rounded(slide, 6.2, 1.82, 6.42, 4.82, WHITE, LINE)
text(slide, "10% welcome offer", 6.55, 2.12, 3.1, 0.28, size=15, color=NAVY, bold=True, font="Georgia", margin=0)
text(slide, "Newly registered guests see a delayed modal with a blurred background and unlock the real first-stay discount.", 6.55, 2.55, 5.4, 0.44, size=11.5, color=MUTED, margin=0)
# modal mockup
rounded(slide, 6.62, 3.22, 5.55, 2.68, NAVY, None)
circle(slide, 7.05, 3.63, 1.12, GOLD)
text(slide, "10", 7.05, 3.82, 1.12, 0.34, size=28, color=NAVY, bold=True, font="Georgia", align=PP_ALIGN.CENTER, margin=0)
text(slide, "% OFF", 7.17, 4.25, 0.88, 0.16, size=8, color=NAVY, bold=True, align=PP_ALIGN.CENTER, margin=0)
text(slide, "Welcome to Aurelia", 8.48, 3.62, 2.9, 0.28, size=16, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "Register now and save 10% on your first web booking.", 8.48, 4.02, 2.95, 0.48, size=10.5, color=RGBColor(211, 223, 239), margin=0)
rounded(slide, 8.48, 4.78, 1.85, 0.37, PALE_GOLD, None)
text(slide, "Unlock offer  ↗", 8.58, 4.87, 1.65, 0.16, size=9, color=NAVY, bold=True, align=PP_ALIGN.CENTER, margin=0)
text(slide, "Nightly rates → 10% discount → 5% tax only → full-stay total", 6.62, 6.13, 5.2, 0.2, size=10, color=GREEN, bold=True, margin=0)
footer(slide, 4)

# 5. PMS
slide = prs.slides.add_slide(blank)
add_slide_bg(slide)
header(slide, "Property operations", "The guest promise is connected to the PMS", "Front desk, operations and finance share the same booking lifecycle and room inventory.", number=5)
# workflow ribbon
steps = [("01", "Reserve", "Booking + snapshot"), ("02", "Assign", "Room inventory"), ("03", "Operate", "Housekeeping + room board"), ("04", "Settle", "Folio + payment"), ("05", "Report", "Analytics + audit")]
for i, (num, title, desc) in enumerate(steps):
    x = 0.78 + i * 2.48
    rounded(slide, x, 1.92, 2.12, 1.05, NAVY if i in [0,4] else WHITE, LINE if i not in [0,4] else None)
    text(slide, num, x + 0.16, 2.12, 0.34, 0.2, size=10, color=GOLD if i in [0,4] else NAVY3, bold=True, margin=0)
    text(slide, title, x + 0.62, 2.06, 1.3, 0.22, size=13, color=WHITE if i in [0,4] else INK, bold=True, font="Georgia", margin=0)
    text(slide, desc, x + 0.62, 2.38, 1.3, 0.2, size=9, color=RGBColor(196, 210, 230) if i in [0,4] else MUTED, margin=0)
    if i < 4:
        text(slide, "→", x + 2.18, 2.29, 0.27, 0.2, size=16, color=GOLD, bold=True, align=PP_ALIGN.CENTER, margin=0)
rounded(slide, 0.78, 3.55, 5.75, 2.6, WHITE, LINE)
text(slide, "PMS surfaces", 1.08, 3.86, 2.2, 0.22, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
bullets(slide, [
    "Reservations, calendar and new booking workflow",
    "Room Board with SSE live updates across 369 rooms",
    "Housekeeping tasks, maintenance requests and role gates",
    "Manager, reception, housekeeping, guest and admin shells",
], 1.08, 4.28, 4.95, 1.45, size=11, gap=9)
rounded(slide, 6.82, 3.55, 5.8, 2.6, NAVY2, None)
text(slide, "Operational confidence", 7.15, 3.86, 3.2, 0.22, size=14, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "Every booking carries its own commercial snapshot — rates, discount, service, tax and total — so the PMS never needs to rewrite history.", 7.15, 4.28, 4.75, 0.82, size=17, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "Full-stay payment totals remain full-stay totals.", 7.15, 5.55, 4.2, 0.2, size=10.5, color=RGBColor(211, 223, 239), margin=0)
footer(slide, 5)

# 6. Financial integrity
slide = prs.slides.add_slide(blank)
add_slide_bg(slide, NAVY)
header(slide, "Financial integrity", "The numbers are treated as contracts", "Historical reservations, folios, payments and cancellation bases remain stable after catalog changes.", dark=True, number=6)
stat_card(slide, 0.72, 1.95, 2.85, 1.28, "170", "Bookings", GOLD, dark=True)
stat_card(slide, 3.78, 1.95, 2.85, 1.28, "170", "Folios", PALE_GOLD, dark=True)
stat_card(slide, 6.84, 1.95, 2.85, 1.28, "103", "Payments", GREEN, dark=True)
stat_card(slide, 9.90, 1.95, 2.7, 1.28, "2,160", "Invariant checks", BLUE, dark=True)
rounded(slide, 0.72, 3.68, 7.15, 2.42, RGBColor(23, 40, 68), RGBColor(69, 92, 125))
text(slide, "Snapshot principle", 1.05, 3.98, 2.5, 0.22, size=14, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "A booking stores the rate details and totals that were actually sold. Later price-catalog changes do not mutate historical revenue.", 1.05, 4.42, 5.95, 0.74, size=20, color=WHITE, bold=True, font="Georgia", margin=0)
text(slide, "The 10% offer is applied before the 5% tax, then stored in the booking snapshot.", 1.05, 5.48, 5.95, 0.24, size=10.5, color=RGBColor(198, 212, 231), margin=0)
rounded(slide, 8.25, 3.68, 4.35, 2.42, PALE_GOLD, None)
text(slide, "Audit result", 8.58, 3.98, 2.1, 0.22, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
text(slide, "PASSED", 8.58, 4.35, 3.2, 0.46, size=30, color=GREEN, bold=True, font="Georgia", margin=0)
text(slide, "2,160 / 2,160 invariants", 8.58, 4.98, 3.2, 0.2, size=11.5, color=NAVY, bold=True, margin=0)
text(slide, "369 rooms · 170 bookings · 170 folios · 103 payments", 8.58, 5.36, 3.2, 0.34, size=9.5, color=RGBColor(55, 75, 70), margin=0)
footer(slide, 6, dark=True)

# 7. Brand & accessibility
slide = prs.slides.add_slide(blank)
add_slide_bg(slide, IVORY)
header(slide, "Brand system", "A simpler mark and a more considered interface", "The visual language is now more coherent: navy, ivory, brushed gold and calm motion.", number=7)
rounded(slide, 0.78, 1.82, 3.38, 4.75, NAVY, None)
add_image(slide, IMG / "logo-simple.png", 1.52, 2.24, 1.9, 1.9)
text(slide, "A", 1.52, 4.33, 1.9, 0.26, size=11, color=PALE_GOLD, bold=True, align=PP_ALIGN.CENTER, margin=0)
text(slide, "Simple gold A monogram", 1.05, 4.87, 2.85, 0.3, size=16, color=WHITE, bold=True, font="Georgia", align=PP_ALIGN.CENTER, margin=0)
text(slide, "No temple, skyline or landscape symbol. Just a clear, scalable hospitality mark.", 1.12, 5.38, 2.7, 0.55, size=10.5, color=RGBColor(205, 216, 232), align=PP_ALIGN.CENTER, margin=0)
rounded(slide, 4.62, 1.82, 7.98, 4.75, WHITE, LINE)
text(slide, "Interaction decisions", 4.98, 2.15, 3.1, 0.23, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
features = [
    ("NAV", "Balanced guest shell", "Ivory body, stable navy glass navigation and gold hairline."),
    ("POP", "Welcome modal", "Blurred backdrop, centered offer card and one-session dismissal."),
    ("MOT", "Motion with control", "Page transitions, press feedback and reduced-motion fallbacks."),
    ("A11", "Accessible behavior", "Escape close, focus restore/trap, live status and responsive controls."),
]
for i, (tag, title, desc) in enumerate(features):
    yy = 2.7 + i * 0.78
    rounded(slide, 4.98, yy, 0.58, 0.36, PALE_GOLD, None)
    text(slide, tag, 4.98, yy + 0.085, 0.58, 0.14, size=8.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER, margin=0)
    text(slide, title, 5.82, yy - 0.02, 2.4, 0.19, size=11.5, color=INK, bold=True, margin=0)
    text(slide, desc, 8.28, yy - 0.02, 3.75, 0.3, size=10.2, color=MUTED, margin=0)
footer(slide, 7)

# 8. Database/deployment
slide = prs.slides.add_slide(blank)
add_slide_bg(slide)
header(slide, "Deployment path", "SQLite fallback, MySQL target, Navicat visibility", "Windows setup scripts now carry the project from a local snapshot to a user-owned MySQL database.", number=8)
# flow
flow_y = 2.35
nodes = [
    ("01", "Current SQLite", "aurelia_collection.db", BG),
    ("02", "Transfer helper", "migrate_sqlite_to_mysql.py", IVORY),
    ("03", "MySQL / MariaDB", "aurelia · utf8mb4", RGBColor(231, 242, 255)),
    ("04", "Navicat", "same connection", PALE_GOLD),
]
for i, (num, title, desc, fill) in enumerate(nodes):
    x = 0.78 + i * 3.12
    rounded(slide, x, flow_y, 2.52, 1.38, fill, LINE)
    text(slide, num, x + 0.2, flow_y + 0.2, 0.35, 0.2, size=10, color=GOLD if i != 2 else BLUE, bold=True, margin=0)
    text(slide, title, x + 0.2, flow_y + 0.52, 2.1, 0.22, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
    text(slide, desc, x + 0.2, flow_y + 0.92, 2.1, 0.18, size=9.5, color=MUTED, margin=0)
    if i < 3:
        text(slide, "→", x + 2.64, flow_y + 0.54, 0.42, 0.25, size=21, color=GOLD, bold=True, align=PP_ALIGN.CENTER, margin=0)
rounded(slide, 0.78, 4.25, 5.55, 1.85, NAVY, None)
text(slide, "One-click Windows path", 1.08, 4.57, 2.9, 0.22, size=14, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "install.bat  →  migrate  →  import if empty  →  audit\nstart.bat    →  connect  →  open admin preview", 1.08, 5.03, 4.65, 0.62, size=14, color=WHITE, bold=True, margin=0)
rounded(slide, 6.68, 4.25, 5.92, 1.85, WHITE, LINE)
text(slide, "Automatic defaults", 7.0, 4.57, 2.5, 0.22, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
text(slide, "127.0.0.1  ·  3306  ·  aurelia  ·  root", 7.0, 5.04, 4.95, 0.25, size=16, color=INK, bold=True, margin=0)
text(slide, "Use mysql.local.bat for a private password and Navicat-specific values.", 7.0, 5.47, 4.8, 0.25, size=10.2, color=MUTED, margin=0)
footer(slide, 8)

# 9. QA
slide = prs.slides.add_slide(blank)
add_slide_bg(slide, BG)
header(slide, "Quality status", "Release checks are green", "Automated validation and live route checks cover the latest design, booking and deployment changes.", number=9)
rounded(slide, 0.78, 1.92, 4.1, 4.7, NAVY, None)
text(slide, "QA CLEAN", 1.12, 2.32, 2.6, 0.34, size=27, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
text(slide, "Latest automated run", 1.12, 2.88, 2.5, 0.2, size=11, color=RGBColor(197, 211, 231), margin=0)
for i, (val, lab) in enumerate([("23/23", "Django tests"), ("2,160", "ledger invariants"), ("0", "pending migrations"), ("200", "Hotels route")]):
    yy = 3.45 + i * 0.62
    icon_badge(slide, 1.12, yy, "✓", fill=GREEN, color=WHITE, d=0.28)
    text(slide, val, 1.57, yy - 0.01, 1.0, 0.22, size=14, color=WHITE, bold=True, margin=0)
    text(slide, lab, 2.76, yy + 0.01, 1.55, 0.18, size=10.2, color=RGBColor(199, 212, 231), margin=0)
text(slide, "No 500 response or traceback observed during the latest live crawl.", 1.12, 5.92, 3.2, 0.34, size=10.2, color=RGBColor(199, 212, 231), margin=0)
rounded(slide, 5.28, 1.92, 7.32, 4.7, WHITE, LINE)
text(slide, "Verified coverage", 5.65, 2.32, 2.7, 0.22, size=14, color=NAVY, bold=True, font="Georgia", margin=0)
bullets(slide, [
    "Anonymous guest shell, hotel collection, rooms, map, auth pages and designed 404",
    "Guest, reception, manager, housekeeping and admin route/role gates",
    "Room Board SSE stream with valid JSON for all 369 rooms",
    "Welcome offer eligibility, one-time consumption and financial snapshot regression",
    "JavaScript syntax, local CSS assets, logo assets and versioned cache paths",
], 5.65, 2.82, 6.35, 2.1, size=12, gap=13, bullet_color=GREEN)
rounded(slide, 5.65, 5.43, 6.35, 0.67, RGBColor(236, 253, 243), RGBColor(167, 243, 208))
text(slide, "Ready for the next user-owned MySQL/Navicat connection step.", 5.95, 5.65, 5.75, 0.2, size=11, color=GREEN, bold=True, margin=0)
footer(slide, 9)

# 10. Next steps
slide = prs.slides.add_slide(blank)
add_slide_bg(slide, NAVY)
header(slide, "Release handoff", "Current version: ready for configuration", "The product build is complete; the remaining environment step is connecting the owner’s MySQL/MariaDB server.", dark=True, number=10)
rounded(slide, 0.78, 1.95, 7.0, 4.5, RGBColor(23, 40, 68), RGBColor(69, 92, 125))
text(slide, "Recommended handoff", 1.15, 2.3, 3.0, 0.23, size=15, color=PALE_GOLD, bold=True, font="Georgia", margin=0)
steps = [
    ("1", "Start MySQL/MariaDB", "Use the same server details configured in Navicat."),
    ("2", "Copy mysql.local.bat.example", "Enter the private password and any custom host/port."),
    ("3", "Run install.bat once", "Migrate schema, preserve the SQLite snapshot and audit."),
    ("4", "Run start.bat", "Launch the app and open the admin preview automatically."),
]
for i, (num, title, desc) in enumerate(steps):
    yy = 2.92 + i * 0.72
    circle(slide, 1.15, yy, 0.33, GOLD)
    text(slide, num, 1.15, yy + 0.07, 0.33, 0.15, size=9, color=NAVY, bold=True, align=PP_ALIGN.CENTER, margin=0)
    text(slide, title, 1.68, yy - 0.01, 2.5, 0.2, size=11.5, color=WHITE, bold=True, margin=0)
    text(slide, desc, 4.15, yy - 0.01, 3.05, 0.28, size=10, color=RGBColor(198, 212, 231), margin=0)
rounded(slide, 8.2, 1.95, 4.35, 4.5, PALE_GOLD, None)
add_image(slide, IMG / "logo-simple.png", 9.65, 2.28, 1.45, 1.45)
text(slide, "Aurelia Collection", 8.63, 4.05, 3.5, 0.34, size=20, color=NAVY, bold=True, font="Georgia", align=PP_ALIGN.CENTER, margin=0)
text(slide, "10 sanctuaries · Cambodia", 8.85, 4.55, 3.05, 0.2, size=10, color=RGBColor(91, 75, 35), bold=True, align=PP_ALIGN.CENTER, margin=0)
text(slide, "Latest build\n27 September 2026", 9.1, 5.16, 2.55, 0.5, size=13, color=NAVY, bold=True, align=PP_ALIGN.CENTER, margin=0)
footer(slide, 10, dark=True)

# Give slides a consistent title property where possible.
prs.core_properties.title = "Aurelia Collection — Latest Release Recap"
prs.core_properties.subject = "Hotel booking and property management system release summary"
prs.core_properties.author = "Aurelia Collection"
prs.core_properties.keywords = "hotel, PMS, booking, Cambodia, MySQL, Navicat, release"
prs.core_properties.comments = "Generated from the latest validated project state on 27 September 2026."
prs.save(OUT)
print(OUT)
