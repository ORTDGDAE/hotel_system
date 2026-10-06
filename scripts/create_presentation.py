from pathlib import Path
from math import cos, sin, pi

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Aurelia_Collection_Class_Presentation.pptx"

# --- Palette -----------------------------------------------------------------
NAVY = RGBColor(14, 26, 47)
NAVY_2 = RGBColor(22, 39, 66)
INK = RGBColor(29, 42, 61)
MUTED = RGBColor(92, 108, 128)
PALE = RGBColor(247, 244, 238)
WHITE = RGBColor(255, 255, 255)
GOLD = RGBColor(202, 157, 70)
GOLD_PALE = RGBColor(247, 234, 199)
BLUE = RGBColor(52, 113, 181)
BLUE_PALE = RGBColor(225, 237, 250)
GREEN = RGBColor(44, 137, 97)
GREEN_PALE = RGBColor(225, 243, 234)
RED = RGBColor(179, 70, 65)
RED_PALE = RGBColor(250, 229, 226)
LINE = RGBColor(220, 225, 231)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def rgb(hexv):
    hexv = hexv.lstrip('#')
    return RGBColor(int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16))


def shape(slide, kind, x, y, w, h, fill=None, line=None, radius=True, transparency=0):
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
        shp.line.width = Pt(0.75)
    return shp


def text(slide, value, x, y, w, h, size=16, color=INK, bold=False, font="Aptos", align=PP_ALIGN.LEFT,
         valign=MSO_ANCHOR.TOP, italic=False, margin=0.04, fit=False, char_spacing=None):
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
    f = run.font
    f.name = font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    if char_spacing is not None:
        f.spacing = Pt(char_spacing)
    if fit:
        tf.fit_text(font_family=font, max_size=Pt(size))
    return box


def rich_text(slide, runs, x, y, w, h, size=16, color=INK, font="Aptos", margin=0.04, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    for item in runs:
        run = p.add_run()
        run.text = item.get("text", "")
        run.font.name = item.get("font", font)
        run.font.size = Pt(item.get("size", size))
        run.font.bold = item.get("bold", False)
        run.font.italic = item.get("italic", False)
        run.font.color.rgb = item.get("color", color)
    return box


def bullet_list(slide, items, x, y, w, h, size=15, color=INK, bullet_color=GOLD, gap=0.08, line_h=0.36):
    cur = y
    for item in items:
        shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x, cur + 0.10, 0.10, 0.10, fill=bullet_color)
        text(slide, item, x + 0.20, cur, w - 0.20, line_h + 0.08, size=size, color=color)
        cur += line_h + gap


def image_cover(slide, path, x, y, w, h, overlay=None, transparency=35):
    path = str(path)
    with Image.open(path) as im:
        iw, ih = im.size
    target = w / h
    source = iw / ih
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    if source > target:
        # crop left/right
        visible = target / source
        crop = (1 - visible) / 2
        pic.crop_left = crop
        pic.crop_right = crop
    else:
        visible = source / target
        crop = (1 - visible) / 2
        pic.crop_top = crop
        pic.crop_bottom = crop
    if overlay is not None:
        shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, y, w, h, fill=overlay, line=None, transparency=transparency)
    return pic


def line(slide, x1, y1, x2, y2, color=LINE, width=1.2, dash=None):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = color
    ln.line.width = Pt(width)
    if dash:
        ln.line.dash_style = dash
    return ln


def pill(slide, label, x, y, w, fill=GOLD_PALE, color=INK, icon=None):
    shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, w, 0.30, fill=fill, line=None)
    if icon:
        text(slide, icon, x + 0.10, y + 0.01, 0.20, 0.24, size=10, color=color, bold=True, valign=MSO_ANCHOR.MIDDLE)
        text(slide, label, x + 0.30, y + 0.01, w - 0.36, 0.24, size=9.5, color=color, bold=True, valign=MSO_ANCHOR.MIDDLE)
    else:
        text(slide, label, x + 0.12, y + 0.01, w - 0.24, 0.24, size=9.5, color=color, bold=True, valign=MSO_ANCHOR.MIDDLE)


def card(slide, x, y, w, h, fill=WHITE, border=LINE, radius=True):
    return shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, w, h, fill=fill, line=border)


def section_header(slide, kicker, title, subtitle=None, page=None, dark=False):
    color = WHITE if dark else INK
    muted = RGBColor(202, 211, 224) if dark else MUTED
    text(slide, kicker.upper(), 0.62, 0.43, 3.8, 0.25, size=10, color=GOLD, bold=True, char_spacing=1.2)
    text(slide, title, 0.62, 0.70, 11.5, 0.52, size=28, color=color, bold=True, font="Aptos Display")
    if subtitle:
        text(slide, subtitle, 0.64, 1.28, 11.1, 0.42, size=12.5, color=muted)
    if page is not None:
        text(slide, f"{page:02d}", 12.18, 0.43, 0.52, 0.25, size=10, color=muted, bold=True, align=PP_ALIGN.RIGHT)


def footer(slide, page, dark=False):
    color = RGBColor(185, 195, 210) if dark else RGBColor(145, 154, 166)
    line(slide, 0.62, 7.11, 12.70, 7.11, color=color, width=0.6)
    text(slide, "AURELIA COLLECTION  ·  CLASS PRESENTATION", 0.65, 7.17, 4.0, 0.18, size=7.5, color=color, bold=True, char_spacing=0.5)
    text(slide, "Django 5.2  ·  27 September 2026", 8.85, 7.17, 3.8, 0.18, size=7.5, color=color, align=PP_ALIGN.RIGHT)


def add_slide(dark=False, bg=PALE):
    slide = prs.slides.add_slide(blank)
    bg_fill = slide.background.fill
    bg_fill.solid(); bg_fill.fore_color.rgb = bg
    return slide


def stat_card(slide, x, y, w, number, label, fill=WHITE, accent=GOLD):
    card(slide, x, y, w, 1.05, fill=fill, border=LINE)
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, y, 0.06, 1.05, fill=accent, line=None)
    text(slide, number, x + 0.22, y + 0.16, w - 0.34, 0.40, size=23, color=INK, bold=True, font="Aptos Display")
    text(slide, label, x + 0.22, y + 0.64, w - 0.34, 0.22, size=9.5, color=MUTED, bold=True)


def link_text(slide, label, url, x, y, w, h, size=11, color=BLUE):
    box = text(slide, label, x, y, w, h, size=size, color=color, bold=True)
    box.text_frame.paragraphs[0].runs[0].hyperlink.address = url
    return box

# --- Slide 1: Cover ----------------------------------------------------------
slide = add_slide(bg=NAVY)
image_cover(slide, ROOT / "static/img/hero.jpg", 7.10, 0, 6.23, 7.5, overlay=NAVY, transparency=48)
shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, 8.4, 7.5, fill=NAVY, line=None)
# warm rule and mark
shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0.72, 0.78, 0.72, 0.05, fill=GOLD, line=None)
shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, 0.72, 1.18, 0.75, 0.75, fill=GOLD, line=None)
text(slide, "A", 0.72, 1.18, 0.75, 0.75, size=26, color=NAVY, bold=True, font="Aptos Display", align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
text(slide, "AURELIA COLLECTION", 1.67, 1.29, 3.9, 0.24, size=11, color=GOLD, bold=True, char_spacing=1.4)
text(slide, "Hotel booking\n& property management\nsystem", 0.72, 2.20, 6.35, 2.05, size=35, color=WHITE, bold=True, font="Aptos Display")
text(slide, "A class-ready walkthrough of the guest experience, PMS workflows, business logic, architecture, and QA evidence behind a Cambodia-only hotel collection.", 0.77, 4.72, 5.55, 0.86, size=16, color=RGBColor(215, 224, 236))
pill(slide, "PROJECT PRESENTATION", 0.77, 6.25, 1.92, fill=RGBColor(45, 61, 86), color=WHITE)
text(slide, "Django 5.2  ·  27 September 2026", 0.78, 6.78, 3.55, 0.22, size=10.5, color=RGBColor(181, 193, 210))
text(slide, "Aurelia Grand / Aurelia Collection", 10.00, 6.88, 2.55, 0.25, size=9.5, color=WHITE, bold=True, align=PP_ALIGN.RIGHT)

# --- Slide 2: Problem and objectives ----------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "01 · Why this project", "One system for the whole stay", "Aurelia turns a fragmented hotel operation into one shared source of truth.", 2)
# left problem
card(slide, 0.62, 1.95, 5.65, 4.55, fill=NAVY, border=NAVY)
text(slide, "THE OPERATING PROBLEM", 0.95, 2.28, 3.2, 0.25, size=10, color=GOLD, bold=True, char_spacing=1.2)
text(slide, "Bookings, rooms,\npeople and money\nare connected.", 0.95, 2.73, 4.6, 1.25, size=27, color=WHITE, bold=True, font="Aptos Display")
bullet_list(slide, [
    "Manual handoffs create avoidable guest friction.",
    "Inventory mistakes create oversell risk and room moves.",
    "Finance needs a traceable folio, not a spreadsheet snapshot.",
    "Staff need different tools — without seeing what they should not.",
], 0.98, 4.32, 4.8, 1.55, size=13, color=RGBColor(221, 228, 238), bullet_color=GOLD, line_h=0.30)
# right objectives
text(slide, "PROJECT OBJECTIVES", 6.78, 2.12, 3.2, 0.25, size=10, color=GOLD, bold=True, char_spacing=1.2)
obj = [
    ("01", "Make booking feel premium", "Clear search, live prices, forgiving mobile flows."),
    ("02", "Protect inventory", "Atomic booking checks and peak-night availability math."),
    ("03", "Connect the hotel team", "PMS, room board, housekeeping and maintenance in one shell."),
    ("04", "Keep money explainable", "Invoice / payment ledger with cancellation and refund rules."),
]
for i, (num, head, desc) in enumerate(obj):
    y = 2.58 + i * 0.91
    text(slide, num, 6.82, y, 0.45, 0.36, size=16, color=GOLD, bold=True, font="Aptos Display")
    line(slide, 7.35, y + 0.18, 7.68, y + 0.18, color=GOLD, width=1.5)
    text(slide, head, 7.82, y - 0.02, 4.55, 0.26, size=15, color=INK, bold=True)
    text(slide, desc, 7.82, y + 0.30, 4.55, 0.32, size=11.5, color=MUTED)
footer(slide, 2)

# --- Slide 3: Product snapshot / personas -----------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "02 · Product snapshot", "Two experiences, one operating model", "The same booking record moves from discovery to departure — while each role sees a focused workspace.", 3)
# guest lane
card(slide, 0.62, 1.98, 6.08, 4.62, fill=PALE, border=LINE)
image_cover(slide, ROOT / "static/img/rooms/deluxe.jpg", 0.62, 1.98, 6.08, 1.46, overlay=NAVY, transparency=52)
text(slide, "GUEST EXPERIENCE", 0.96, 2.34, 2.4, 0.24, size=10, color=GOLD, bold=True, char_spacing=1.1)
text(slide, "Discover → book → stay", 0.96, 2.68, 4.8, 0.42, size=22, color=WHITE, bold=True, font="Aptos Display")
steps = [("1", "Explore", "Cambodia collection, rooms, real photos"), ("2", "Search", "Dates, guests, rooms and availability"), ("3", "Confirm", "Snapshot price, folio and confirmation"), ("4", "Self-serve", "My Stays, cancellation and map links")]
for i, (n, h, d) in enumerate(steps):
    x = 0.95 + (i % 2) * 2.82
    y = 3.75 + (i // 2) * 1.10
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x, y, 0.37, 0.37, fill=GOLD, line=None)
    text(slide, n, x, y + 0.01, 0.37, 0.29, size=11, color=NAVY, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    text(slide, h, x + 0.51, y - 0.02, 1.95, 0.24, size=13, color=INK, bold=True)
    text(slide, d, x + 0.51, y + 0.29, 1.95, 0.42, size=9.7, color=MUTED)
# staff lane
card(slide, 6.98, 1.98, 5.73, 4.62, fill=NAVY, border=NAVY)
text(slide, "STAFF WORKSPACE", 7.34, 2.28, 2.4, 0.24, size=10, color=GOLD, bold=True, char_spacing=1.1)
text(slide, "See the operation\nat a glance", 7.34, 2.67, 4.5, 0.83, size=23, color=WHITE, bold=True, font="Aptos Display")
# mini dashboard cards
for i, (label, value, accent) in enumerate([("Arrivals", "24", BLUE), ("In-house", "86", GREEN), ("Open tasks", "12", GOLD)]):
    x = 7.34 + i * 1.68
    card(slide, x, 3.82, 1.45, 0.90, fill=RGBColor(31, 50, 80), border=RGBColor(58, 77, 105))
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, 3.82, 1.45, 0.05, fill=accent, line=None)
    text(slide, value, x + 0.15, 4.05, 1.14, 0.30, size=21, color=WHITE, bold=True)
    text(slide, label, x + 0.15, 4.42, 1.15, 0.16, size=8.5, color=RGBColor(190, 202, 220))
# staff functions
for i, label in enumerate(["Reservations", "Room board", "Housekeeping", "Finance", "Analytics"]):
    x = 7.34 + (i % 3) * 1.70
    y = 5.02 + (i // 3) * 0.60
    pill(slide, label, x, y, 1.48, fill=RGBColor(43, 63, 94), color=WHITE)
text(slide, "Property-aware: one hotel or the full collection.", 7.36, 6.23, 4.7, 0.22, size=10.5, color=RGBColor(190, 202, 220), italic=True)
footer(slide, 3)

# --- Slide 4: guest experience ------------------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "03 · Guest journey", "A premium booking flow without the friction", "The public site is intentionally simple: discover a room, get a trustworthy price, complete the stay.", 4)
# image / callout
image_cover(slide, ROOT / "static/img/props/phnom-penh.jpg", 0.62, 1.98, 4.35, 4.72, overlay=NAVY, transparency=42)
text(slide, "01", 0.98, 2.35, 0.52, 0.30, size=15, color=GOLD, bold=True)
text(slide, "Discover the\ncollection", 0.98, 2.80, 3.0, 0.78, size=26, color=WHITE, bold=True, font="Aptos Display")
text(slide, "Ten Cambodian sanctuaries with property stories, real photography, room types and direct location links.", 1.00, 4.06, 3.15, 0.85, size=13, color=RGBColor(226, 232, 241))
pill(slide, "10 properties · Cambodia", 0.99, 5.33, 1.90, fill=RGBColor(45, 61, 86), color=WHITE)
pill(slide, "Real room imagery", 0.99, 5.76, 1.74, fill=RGBColor(45, 61, 86), color=WHITE)
# flow
flow = [
    ("02", "Search", "Date range + rooms + adults + children", BLUE_PALE, BLUE),
    ("03", "Price", "Nightly rules → service → tax → total", GOLD_PALE, GOLD),
    ("04", "Book", "Atomic availability check + invoice", GREEN_PALE, GREEN),
    ("05", "Manage", "Confirmation, My Stays, cancel", RED_PALE, RED),
]
for i, (n, head, desc, fill, accent) in enumerate(flow):
    x = 5.38 + (i % 2) * 3.64
    y = 2.16 + (i // 2) * 1.93
    card(slide, x, y, 3.31, 1.49, fill=WHITE, border=LINE)
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x + 0.24, y + 0.22, 0.43, 0.43, fill=accent, line=None)
    text(slide, n, x + 0.24, y + 0.23, 0.43, 0.30, size=10, color=WHITE if accent != GOLD else NAVY, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    text(slide, head, x + 0.86, y + 0.22, 2.15, 0.28, size=15, color=INK, bold=True)
    text(slide, desc, x + 0.24, y + 0.80, 2.70, 0.44, size=10.5, color=MUTED)
text(slide, "iPhone-premium interaction details", 5.42, 6.18, 2.9, 0.23, size=10, color=GOLD, bold=True, char_spacing=0.6)
pill(slide, "body-portalled date sheet", 8.10, 6.12, 1.87, fill=GOLD_PALE, color=INK)
pill(slide, "guest stepper sheet", 10.18, 6.12, 1.60, fill=GOLD_PALE, color=INK)
footer(slide, 4)

# --- Slide 5: PMS workflow ---------------------------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "04 · PMS / front desk", "From reservation to room key", "Staff workflows reuse the same domain services as the guest booking flow — not a second set of rules.", 5)
# pipeline
nodes = [
    ("RESERVATION", "Confirmed", BLUE, BLUE_PALE),
    ("ARRIVAL", "Check-in", GREEN, GREEN_PALE),
    ("IN-HOUSE", "Occupied", GOLD, GOLD_PALE),
    ("DEPARTURE", "Check-out", RED, RED_PALE),
]
for i, (head, sub, accent, fill) in enumerate(nodes):
    x = 0.78 + i * 3.10
    if i < 3:
        line(slide, x + 2.22, 3.17, x + 3.00, 3.17, color=LINE, width=2.0)
        shape(slide, MSO_AUTO_SHAPE_TYPE.CHEVRON, x + 2.78, 3.07, 0.28, 0.20, fill=LINE, line=None)
    card(slide, x, 2.20, 2.42, 1.88, fill=fill, border=LINE)
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x + 0.22, 2.45, 0.48, 0.48, fill=accent, line=None)
    text(slide, str(i + 1), x + 0.22, 2.49, 0.48, 0.30, size=12, color=NAVY if accent == GOLD else WHITE, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    text(slide, head, x + 0.84, 2.47, 1.32, 0.22, size=10, color=accent, bold=True, char_spacing=0.6)
    text(slide, sub, x + 0.22, 3.15, 1.82, 0.34, size=19, color=INK, bold=True, font="Aptos Display")
    text(slide, ["Search, assign, edit", "Validate clean room", "Live room status", "Release + settle"][i], x + 0.22, 3.59, 1.86, 0.26, size=9.8, color=MUTED)
# lower modules
text(slide, "STAFF MODULES", 0.78, 4.68, 2.3, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
modules = [
    ("Reservations", "New booking, filters, detail, payment"),
    ("Calendar", "Visual occupancy across the stay dates"),
    ("Rates", "Seasonal, weekend and promo rules"),
    ("Property switch", "Active hotel scope for multi-property staff"),
]
for i, (h, d) in enumerate(modules):
    x = 0.78 + (i % 2) * 6.05
    y = 5.04 + (i // 2) * 0.72
    line(slide, x, y + 0.14, x + 0.18, y + 0.14, color=GOLD, width=2.0)
    text(slide, h, x + 0.28, y, 1.95, 0.22, size=13, color=INK, bold=True)
    text(slide, d, x + 2.35, y, 3.35, 0.24, size=10.5, color=MUTED)
footer(slide, 5)

# --- Slide 6: operations -----------------------------------------------------
slide = add_slide(bg=NAVY)
section_header(slide, "05 · Operations", "The room is a state machine", "Front desk, housekeeping and maintenance work against one physical-room status — so stock stays honest.", 6, dark=True)
# state machine
states = [
    ("Vacant\nclean", GREEN, 1.02, 2.40),
    ("Occupied\nclean", BLUE, 3.28, 2.40),
    ("Vacant\ndirty", GOLD, 5.54, 2.40),
    ("Maintenance", RED, 7.80, 2.40),
    ("Out of\norder", RGBColor(122, 132, 148), 10.06, 2.40),
]
for label, accent, x, y in states:
    shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, 1.68, 0.93, fill=RGBColor(31, 50, 80), line=accent)
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x + 0.16, y + 0.25, 0.14, 0.14, fill=accent, line=None)
    text(slide, label, x + 0.40, y + 0.18, 1.06, 0.49, size=12, color=WHITE, bold=True, valign=MSO_ANCHOR.MIDDLE)
for x1, x2 in [(2.70, 3.28), (4.96, 5.54)]:
    line(slide, x1, 2.86, x2, 2.86, color=RGBColor(100, 120, 151), width=1.4)
    shape(slide, MSO_AUTO_SHAPE_TYPE.CHEVRON, x2 - 0.08, 2.77, 0.18, 0.18, fill=RGBColor(100, 120, 151), line=None)
line(slide, 6.40, 3.45, 7.88, 3.45, color=RGBColor(100, 120, 151), width=1.4, dash=MSO_LINE_DASH_STYLE.DASH)
shape(slide, MSO_AUTO_SHAPE_TYPE.CHEVRON, 7.80, 3.36, 0.18, 0.18, fill=RGBColor(100, 120, 151), line=None)
line(slide, 9.48, 2.86, 10.06, 2.86, color=RGBColor(100, 120, 151), width=1.4)
shape(slide, MSO_AUTO_SHAPE_TYPE.CHEVRON, 9.98, 2.77, 0.18, 0.18, fill=RGBColor(100, 120, 151), line=None)
text(slide, "check-in", 2.80, 3.08, 0.82, 0.20, size=8.5, color=RGBColor(190, 202, 220), align=PP_ALIGN.CENTER)
text(slide, "check-out", 4.86, 3.08, 0.82, 0.20, size=8.5, color=RGBColor(190, 202, 220), align=PP_ALIGN.CENTER)
text(slide, "high / critical request", 6.37, 3.67, 1.52, 0.20, size=8.5, color=RGBColor(190, 202, 220), align=PP_ALIGN.CENTER)
text(slide, "blocked from sale", 9.42, 3.08, 1.02, 0.20, size=8.5, color=RGBColor(190, 202, 220), align=PP_ALIGN.CENTER)
# three columns
ops = [
    ("LIVE ROOM BOARD", "SSE endpoint sends the current room state; the UI patches tiles in place without a heavy client dependency.", "200 · text/event-stream", BLUE),
    ("HOUSEKEEPING", "Check-out marks rooms dirty and auto-creates urgent clean tasks. Completing the task returns vacant rooms to clean stock.", "Pending → In progress → Completed", GREEN),
    ("NIGHTLY OPERATIONS", "No-shows, daily service tasks and occupancy snapshots are ready for the 02:00 nightly job.", "manage.py nightly_ops", GOLD),
]
for i, (head, desc, tag, accent) in enumerate(ops):
    x = 0.80 + i * 4.16
    card(slide, x, 4.65, 3.76, 1.45, fill=RGBColor(25, 43, 72), border=RGBColor(56, 75, 105))
    text(slide, head, x + 0.22, 4.90, 3.1, 0.22, size=10, color=accent, bold=True, char_spacing=0.7)
    text(slide, desc, x + 0.22, 5.25, 3.25, 0.48, size=10.4, color=RGBColor(212, 221, 233))
    pill(slide, tag, x + 0.22, 5.87, 2.36 if i != 1 else 2.52, fill=RGBColor(46, 65, 96), color=WHITE)
footer(slide, 6, dark=True)

# --- Slide 7: architecture --------------------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "06 · Architecture", "Thin views, explicit domain services", "Django apps keep responsibilities separated while sharing one relational data model.", 7)
# layers left
layers = [
    ("Experience", "Templates · CSS · JS · mobile sheets", GOLD, GOLD_PALE),
    ("Web / access", "URLs · views · forms · RBAC decorators", BLUE, BLUE_PALE),
    ("Domain", "booking services · finance services · ops services", GREEN, GREEN_PALE),
    ("Persistence", "Django ORM · SQLite demo / Postgres path", RED, RED_PALE),
]
for i, (head, desc, accent, fill) in enumerate(layers):
    y = 2.05 + i * 0.91
    card(slide, 0.75, y, 5.25, 0.68, fill=fill, border=LINE)
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0.75, y, 0.10, 0.68, fill=accent, line=None)
    text(slide, head, 1.03, y + 0.14, 1.35, 0.22, size=13, color=INK, bold=True)
    text(slide, desc, 2.50, y + 0.14, 3.16, 0.25, size=10.5, color=MUTED)
    if i < 3:
        line(slide, 3.28, y + 0.68, 3.28, y + 0.91, color=LINE, width=1.0)
# app map
text(slide, "DJANGO APPS", 6.62, 2.02, 2.3, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
apps = [
    ("accounts", "custom user + roles"), ("hotel", "properties + rooms"),
    ("bookings", "reservations + pricing"), ("operations", "tasks + maintenance"),
    ("finance", "folios + payments"), ("analytics", "KPIs + charts"),
    ("core", "guest shell + emails"), ("config", "settings + routing"),
]
for i, (app, desc) in enumerate(apps):
    x = 6.62 + (i % 2) * 2.85
    y = 2.42 + (i // 2) * 0.86
    card(slide, x, y, 2.54, 0.65, fill=WHITE, border=LINE)
    text(slide, app, x + 0.18, y + 0.12, 1.00, 0.20, size=11.5, color=INK, bold=True, font="Aptos Mono")
    text(slide, desc, x + 1.15, y + 0.12, 1.20, 0.22, size=9.2, color=MUTED)
# bottom principle
card(slide, 6.62, 5.95, 5.40, 0.68, fill=NAVY, border=NAVY)
text(slide, "Principle", 6.90, 6.12, 0.80, 0.19, size=10, color=GOLD, bold=True)
text(slide, "Views orchestrate. Services decide. Models persist.", 7.82, 6.10, 3.86, 0.22, size=12, color=WHITE, bold=True)
footer(slide, 7)

# --- Slide 8: data model -----------------------------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "07 · Data model", "The reservation is the spine", "Property and room inventory, the guest stay, and the folio connect through explicit foreign keys.", 8)
# ER diagram boxes
# property chain
card(slide, 0.75, 2.08, 2.28, 0.92, fill=GOLD_PALE, border=GOLD)
text(slide, "Property", 0.98, 2.28, 1.55, 0.24, size=16, color=INK, bold=True)
text(slide, "city · coords · tax · service", 0.98, 2.64, 1.78, 0.17, size=9.2, color=MUTED)
card(slide, 0.75, 3.65, 2.28, 0.92, fill=BLUE_PALE, border=BLUE)
text(slide, "RoomType", 0.98, 3.85, 1.55, 0.24, size=16, color=INK, bold=True)
text(slide, "base price · capacity · stock", 0.98, 4.21, 1.80, 0.17, size=9.2, color=MUTED)
card(slide, 0.75, 5.22, 2.28, 0.92, fill=GREEN_PALE, border=GREEN)
text(slide, "Room", 0.98, 5.42, 1.55, 0.24, size=16, color=INK, bold=True)
text(slide, "number · floor · status", 0.98, 5.78, 1.80, 0.17, size=9.2, color=MUTED)
line(slide, 1.90, 3.00, 1.90, 3.65, color=LINE, width=1.6)
line(slide, 1.90, 4.57, 1.90, 5.22, color=LINE, width=1.6)
text(slide, "1 → many", 2.02, 3.22, 0.70, 0.17, size=8.5, color=MUTED)
text(slide, "1 → many", 2.02, 4.78, 0.70, 0.17, size=8.5, color=MUTED)
# center booking
card(slide, 4.25, 2.90, 2.95, 1.36, fill=NAVY, border=NAVY)
text(slide, "Booking", 4.58, 3.16, 2.10, 0.28, size=20, color=WHITE, bold=True, font="Aptos Display")
text(slide, "dates · guests · source · status\nprice snapshot · rate details", 4.58, 3.62, 2.20, 0.42, size=10.5, color=RGBColor(214, 223, 235))
# right folio
card(slide, 8.15, 2.10, 2.10, 0.97, fill=RED_PALE, border=RED)
text(slide, "Invoice", 8.40, 2.32, 1.55, 0.25, size=16, color=INK, bold=True)
text(slide, "one folio per booking", 8.40, 2.69, 1.48, 0.17, size=9.2, color=MUTED)
card(slide, 10.74, 2.10, 1.75, 0.97, fill=GOLD_PALE, border=GOLD)
text(slide, "Payment", 10.97, 2.32, 1.35, 0.25, size=15, color=INK, bold=True)
text(slide, "charges / refunds", 10.97, 2.69, 1.20, 0.17, size=9.2, color=MUTED)
line(slide, 7.20, 3.58, 8.15, 2.60, color=LINE, width=1.4)
line(slide, 10.25, 2.58, 10.74, 2.58, color=LINE, width=1.4)
# lower links
card(slide, 4.25, 5.10, 2.95, 0.93, fill=PALE, border=LINE)
text(slide, "RoomAssignment", 4.57, 5.29, 2.25, 0.23, size=14, color=INK, bold=True)
text(slide, "physical room during stay", 4.57, 5.63, 2.18, 0.17, size=9.2, color=MUTED)
card(slide, 8.15, 4.10, 2.10, 0.93, fill=WHITE, border=LINE)
text(slide, "RateRule", 8.43, 4.30, 1.52, 0.23, size=14, color=INK, bold=True)
text(slide, "seasonal / promo / weekend", 8.43, 4.63, 1.52, 0.17, size=8.8, color=MUTED)
card(slide, 10.74, 4.10, 1.75, 0.93, fill=WHITE, border=LINE)
text(slide, "Ops", 11.00, 4.30, 1.20, 0.23, size=14, color=INK, bold=True)
text(slide, "tasks + maintenance", 11.00, 4.63, 1.20, 0.17, size=8.8, color=MUTED)
line(slide, 5.72, 4.26, 5.72, 5.10, color=LINE, width=1.4)
line(slide, 7.20, 5.57, 8.15, 4.57, color=LINE, width=1.4)
line(slide, 7.20, 5.57, 10.74, 4.57, color=LINE, width=1.1, dash=MSO_LINE_DASH_STYLE.DASH)
footer(slide, 8)

# --- Slide 9: booking/inventory logic ---------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "08 · Booking engine", "Availability is a business rule, not a guess", "The engine protects capacity at the same moment it prices and persists the reservation.", 9)
# formula panel
card(slide, 0.72, 2.00, 5.45, 4.55, fill=NAVY, border=NAVY)
text(slide, "PRICE PER STAY", 1.02, 2.30, 2.2, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
text(slide, "rack rate ×\napplicable rules", 1.02, 2.72, 2.15, 0.72, size=23, color=WHITE, bold=True, font="Aptos Display")
text(slide, "+ weekend premium\n× rooms\n+ 5% tax only", 3.48, 2.79, 2.12, 1.26, size=14, color=RGBColor(220, 229, 239), bold=True)
line(slide, 1.02, 4.03, 5.55, 4.03, color=RGBColor(74, 94, 125), width=0.8)
text(slide, "Contract protection", 1.02, 4.37, 1.6, 0.20, size=10, color=GOLD, bold=True)
text(slide, "The nightly breakdown and totals are snapshotted onto Booking. Later rate changes never mutate an existing reservation.", 1.02, 4.70, 4.55, 0.72, size=13, color=RGBColor(220, 229, 239))
pill(slide, "Decimal money", 1.02, 5.78, 1.28, fill=RGBColor(45, 61, 86), color=WHITE)
pill(slide, "max 30 nights", 2.52, 5.78, 1.35, fill=RGBColor(45, 61, 86), color=WHITE)
# guards right
text(slide, "INVENTORY GUARDS", 6.72, 2.12, 2.7, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
guards = [
    ("01", "Half-open overlap", "[check-in, check-out) means an adjacent stay does not conflict."),
    ("02", "Peak-night math", "Each overlapping active booking contributes rooms per night; the maximum is the committed count."),
    ("03", "Atomic write", "RoomType inventory row is locked inside a transaction before the final availability check."),
    ("04", "Lifecycle truth", "Confirmed and checked-in block stock; cancelled, checked-out and no-show do not."),
]
for i, (num, head, desc) in enumerate(guards):
    y = 2.55 + i * 0.89
    text(slide, num, 6.75, y, 0.43, 0.28, size=14, color=GOLD, bold=True, font="Aptos Display")
    text(slide, head, 7.40, y - 0.01, 2.25, 0.24, size=14, color=INK, bold=True)
    text(slide, desc, 7.40, y + 0.29, 4.62, 0.34, size=10.6, color=MUTED)
    if i < 3: line(slide, 7.40, y + 0.77, 12.02, y + 0.77, color=LINE, width=0.6)
footer(slide, 9)

# --- Slide 10: finance -------------------------------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "09 · Finance", "A folio that explains itself", "Every charge and refund is tied to the booking; status is derived from the completed-payment ledger.", 10)
# folio visual
card(slide, 0.72, 2.03, 5.18, 4.56, fill=PALE, border=LINE)
text(slide, "FOLIO FLOW", 1.02, 2.30, 1.5, 0.22, size=10, color=GOLD, bold=True, char_spacing=1.1)
rows = [("Room subtotal", "$1,200.00", INK), ("Service · 5%", "$60.00", INK), ("Tax · 10%", "$126.00", INK), ("Grand total", "$1,386.00", NAVY)]
for i, (label, val, col) in enumerate(rows):
    y = 2.86 + i * 0.55
    if i == 3: line(slide, 1.02, y - 0.08, 5.50, y - 0.08, color=GOLD, width=1.2)
    text(slide, label, 1.03, y, 2.3, 0.22, size=13 if i == 3 else 11.5, color=col, bold=i == 3)
    text(slide, val, 4.00, y, 1.42, 0.22, size=14 if i == 3 else 11.5, color=col, bold=i == 3, align=PP_ALIGN.RIGHT)
# states
text(slide, "STATUS DERIVATION", 1.03, 5.27, 2.2, 0.20, size=10, color=GOLD, bold=True, char_spacing=1.1)
for i, (label, fill, col) in enumerate([("open", BLUE_PALE, BLUE), ("partial", GOLD_PALE, GOLD), ("paid", GREEN_PALE, GREEN), ("refunded", RED_PALE, RED)]):
    x = 1.02 + (i % 2) * 2.03
    y = 5.66 + (i // 2) * 0.40
    pill(slide, label, x, y, 1.48, fill=fill, color=col)
# cancellation right
text(slide, "CANCELLATION RULE", 6.65, 2.12, 2.9, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
text(slide, "Free until the property’s deadline.\nAfter that, retain the first night.", 6.65, 2.58, 5.2, 0.76, size=24, color=INK, bold=True, font="Aptos Display")
# waterfall
steps = [("Paid", "−$1,386", BLUE), ("Fee", "+$120", GOLD), ("Refund", "−$1,266", RED), ("Final folio", "$120", GREEN)]
for i, (h, val, col) in enumerate(steps):
    y = 3.82 + i * 0.54
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 6.68, y + 0.03, 0.07, 0.28, fill=col, line=None)
    text(slide, h, 6.92, y, 1.62, 0.22, size=12, color=INK, bold=True)
    text(slide, val, 10.45, y, 1.18, 0.22, size=12, color=col, bold=True, align=PP_ALIGN.RIGHT)
    if i < 3: line(slide, 6.92, y + 0.38, 11.62, y + 0.38, color=LINE, width=0.6)
card(slide, 6.65, 6.06, 5.48, 0.45, fill=GREEN_PALE, border=GREEN)
text(slide, "QA hardening: zero-total folios now reconcile as paid, not open.", 6.93, 6.18, 4.95, 0.18, size=10.5, color=GREEN, bold=True)
footer(slide, 10)

# --- Slide 11: auth and roles ------------------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "10 · Authentication & permissions", "Least privilege, visible in the navigation", "A custom User model drives role gates across guest, operations, finance and analytics.", 11)
# role table
headers = [("Role", 0.80, 1.65), ("Guest site", 3.05, 1.55), ("PMS / Ops", 5.25, 1.55), ("Finance", 7.45, 1.55), ("Analytics", 9.65, 1.55)]
for h, x, w in headers:
    text(slide, h.upper(), x, 2.07, w, 0.24, size=9.5, color=GOLD, bold=True, char_spacing=0.7)
line(slide, 0.80, 2.42, 12.15, 2.42, color=LINE, width=1.0)
role_rows = [
    ("Guest", "Own stays", "—", "—", "—", BLUE),
    ("Receptionist", "Public + stays", "Reservations", "Payments", "—", GREEN),
    ("Housekeeping", "Public + stays", "Room board / tasks", "—", "—", GOLD),
    ("Manager", "All guest", "All staff ops", "Reports", "KPIs", NAVY),
    ("Administrator", "All", "All + admin", "All", "All", RED),
]
for i, row in enumerate(role_rows):
    y = 2.61 + i * 0.62
    fill = WHITE if i % 2 == 0 else RGBColor(250, 249, 246)
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0.80, y - 0.08, 11.36, 0.53, fill=fill, line=None)
    h, guest, ops, fin, ana, accent = row
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0.80, y - 0.08, 0.07, 0.53, fill=accent, line=None)
    text(slide, h, 1.02, y + 0.04, 1.62, 0.22, size=12.5, color=INK, bold=True)
    for val, x in [(guest, 3.05), (ops, 5.25), (fin, 7.45), (ana, 9.65)]:
        col = MUTED if val == "—" else INK
        text(slide, val, x, y + 0.04, 1.52, 0.22, size=10.5, color=col, bold=val != "—")
# security cards
card(slide, 0.80, 6.08, 3.58, 0.50, fill=NAVY, border=NAVY)
text(slide, "CSRF on mutations", 1.08, 6.23, 1.48, 0.18, size=10.5, color=WHITE, bold=True)
text(slide, "·", 2.64, 6.23, 0.20, 0.18, size=12, color=GOLD, bold=True)
text(slide, "dev-login gated", 2.90, 6.23, 1.22, 0.18, size=10.5, color=GOLD, bold=True)
card(slide, 4.67, 6.08, 3.58, 0.50, fill=WHITE, border=LINE)
text(slide, "X-Frame-Options DENY", 4.95, 6.23, 1.75, 0.18, size=10.5, color=INK, bold=True)
text(slide, "·", 6.78, 6.23, 0.20, 0.18, size=12, color=GOLD, bold=True)
text(slide, "HTTPS flags in prod", 7.02, 6.23, 1.10, 0.18, size=9.5, color=MUTED, bold=True)
card(slide, 8.53, 6.08, 3.63, 0.50, fill=WHITE, border=LINE)
text(slide, "Safe templates", 8.82, 6.23, 1.20, 0.18, size=10.5, color=INK, bold=True)
text(slide, "·", 10.10, 6.23, 0.20, 0.18, size=12, color=GOLD, bold=True)
text(slide, "Decimal money", 10.34, 6.23, 1.30, 0.18, size=10.5, color=MUTED, bold=True)
footer(slide, 11)

# --- Slide 12: maps ----------------------------------------------------------
slide = add_slide(bg=NAVY)
section_header(slide, "11 · Maps & the collection", "Cambodia-first, key-free by design", "The site keeps a real Cambodia map while Google Maps is used as a browser/app destination link — never as a required tile API.", 12, dark=True)
# stylized map panel
card(slide, 0.72, 1.93, 7.05, 4.80, fill=RGBColor(25, 43, 72), border=RGBColor(60, 80, 111))
# water/background
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.00, 2.25, 6.48, 4.18, fill=RGBColor(21, 57, 83), line=None)
# approximate Cambodia polygon in local panel coords
poly = [(2.26, 2.58), (3.36, 2.38), (4.68, 2.52), (5.82, 2.92), (6.70, 3.72), (6.28, 4.48), (5.70, 5.24), (4.74, 5.80), (3.56, 5.72), (2.72, 5.30), (2.10, 4.56), (1.88, 3.72)]
freeform = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.FREEFORM, Inches(0), Inches(0), Inches(0.01), Inches(0.01)) if False else None
# draw map via polygon in SVG-ish using a freeform-like line network (safe in pptx with closed line)
for i in range(len(poly)):
    p1 = poly[i]; p2 = poly[(i + 1) % len(poly)]
    line(slide, p1[0], p1[1], p2[0], p2[1], color=RGBColor(104, 166, 151), width=2.0)
# rivers
line(slide, 5.66, 2.68, 5.45, 3.40, color=RGBColor(92, 184, 214), width=1.6)
line(slide, 5.45, 3.40, 5.20, 4.18, color=RGBColor(92, 184, 214), width=1.6)
line(slide, 5.20, 4.18, 4.82, 4.86, color=RGBColor(92, 184, 214), width=1.6)
line(slide, 4.82, 4.86, 4.55, 5.56, color=RGBColor(92, 184, 214), width=1.6)
# pins
pins = [("Siem Reap", 4.12, 3.20), ("Battambang", 3.18, 3.54), ("Phnom Penh", 5.05, 4.42), ("Kep", 4.36, 5.55), ("Koh Rong", 2.68, 5.02)]
for label, x, y in pins:
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x - 0.08, y - 0.08, 0.16, 0.16, fill=GOLD, line=None)
    text(slide, label, x + 0.12, y - 0.09, 1.22, 0.20, size=8.5, color=WHITE, bold=True)
text(slide, "REAL CAMBODIA COLLECTION", 1.14, 2.47, 2.6, 0.20, size=9, color=GOLD, bold=True, char_spacing=0.7)
text(slide, "10 properties · WGS-84 coordinates", 1.14, 6.06, 2.8, 0.20, size=9.5, color=RGBColor(195, 208, 225))
# key-free explanation
text(slide, "HOW IT WORKS", 8.28, 2.08, 2.2, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
map_bullets = [
    "Leaflet/CARTO/Esri map preview stays key-free.",
    "Self-contained SVG fallback works when tiles cannot load.",
    "Every property and attraction stores real latitude / longitude.",
    "Google link format: maps/search/?api=1&query=lat,lon",
]
bullet_list(slide, map_bullets, 8.30, 2.55, 4.32, 1.95, size=12.4, color=RGBColor(221, 229, 239), bullet_color=GOLD, line_h=0.33, gap=0.10)
# map link samples
text(slide, "BROWSER / APP LINKS", 8.30, 4.92, 2.4, 0.20, size=10, color=GOLD, bold=True, char_spacing=0.8)
link_text(slide, "Phnom Penh · 11.56560, 104.93250", "https://www.google.com/maps/search/?api=1&query=11.56560,104.93250", 8.30, 5.28, 4.18, 0.20, size=10.5, color=WHITE)
link_text(slide, "Siem Reap · 13.35200, 103.85700", "https://www.google.com/maps/search/?api=1&query=13.35200,103.85700", 8.30, 5.66, 4.18, 0.20, size=10.5, color=WHITE)
text(slide, "No API key stored or required by the website.", 8.30, 6.18, 4.25, 0.22, size=10.5, color=RGBColor(193, 207, 225), italic=True)
footer(slide, 12, dark=True)

# --- Slide 13: UX/accessibility ----------------------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "12 · UX / UI", "Designed for clarity, touch and recovery", "A normal-light visual system, responsive navigation and reduced-motion behavior support real use — not just screenshots.", 13)
# left visual mock
card(slide, 0.72, 1.98, 4.12, 4.72, fill=NAVY, border=NAVY)
# mock mobile
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.12, 2.31, 1.85, 3.72, fill=WHITE, line=RGBColor(102, 119, 143))
shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, 1.12, 2.31, 1.85, 0.70, fill=NAVY_2, line=None)
text(slide, "Aurelia", 1.29, 2.52, 1.25, 0.18, size=9, color=WHITE, bold=True)
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.28, 3.32, 1.53, 0.48, fill=GOLD_PALE, line=None)
text(slide, "3 nights", 1.45, 3.47, 1.15, 0.18, size=10, color=INK, bold=True, align=PP_ALIGN.CENTER)
for j in range(3):
    shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.28, 4.13 + j * 0.36, 1.54, 0.18, fill=RGBColor(238, 241, 245), line=None)
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.28, 5.40, 1.54, 0.35, fill=GOLD, line=None)
text(slide, "Search rooms", 1.37, 5.49, 1.35, 0.15, size=8.8, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
# sheet overlay
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 2.30, 3.00, 2.10, 2.80, fill=RGBColor(249, 248, 245), line=LINE)
text(slide, "Dates & guests", 2.58, 3.25, 1.48, 0.22, size=12, color=INK, bold=True)
text(slide, "Body-portalled sheet", 2.58, 3.58, 1.52, 0.18, size=9, color=GOLD, bold=True)
for j, lab in enumerate(["Check-in", "Check-out", "Guests"]):
    text(slide, lab, 2.58, 4.06 + j * 0.40, 0.78, 0.16, size=8.5, color=MUTED)
    line(slide, 3.36, 4.22 + j * 0.40, 4.02, 4.22 + j * 0.40, color=LINE, width=0.7)
text(slide, "Done", 3.35, 5.40, 0.63, 0.18, size=10, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
# right checklist
text(slide, "PROFESSIONAL DETAILS", 5.42, 2.14, 2.7, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
check = [
    ("Responsive", "Mobile bottom-sheet menu; no overflowing nav labels."),
    ("Accessible", "Semantic status, focus states, labels, keyboard-friendly close paths."),
    ("Resilient", "Designed 403 / 404 / 500 pages, loading layer and submit protection."),
    ("Motion-aware", "Transitions and scroll reveals respect prefers-reduced-motion."),
    ("Light by default", "Normal light theme; self-hosted Remix Icons; no emoji glyphs."),
]
for i, (h, d) in enumerate(check):
    y = 2.58 + i * 0.72
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, 5.44, y + 0.03, 0.28, 0.28, fill=GREEN, line=None)
    text(slide, "✓", 5.44, y + 0.03, 0.28, 0.24, size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    text(slide, h, 5.90, y, 1.42, 0.20, size=13, color=INK, bold=True)
    text(slide, d, 7.47, y, 4.54, 0.31, size=10.6, color=MUTED)
footer(slide, 13)

# --- Slide 14: QA ------------------------------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "13 · QA / testing", "Evidence, not just confidence", "The latest-version pass combined automated tests, invariant checks, static audits and a live per-role crawl.", 14)
stat_card(slide, 0.72, 1.98, 2.72, "22 / 22", "Django tests passed", fill=WHITE, accent=GREEN)
stat_card(slide, 3.66, 1.98, 2.72, "2,166", "ledger + inventory invariants", fill=WHITE, accent=BLUE)
stat_card(slide, 6.60, 1.98, 2.72, "369", "rooms in live SSE payload", fill=WHITE, accent=GOLD)
stat_card(slide, 9.54, 1.98, 2.72, "0", "500s / tracebacks observed", fill=WHITE, accent=RED)
# matrix
text(slide, "LATEST CHECKS", 0.78, 3.42, 2.0, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
checks = [
    ("Django system check", "No issues", GREEN),
    ("Full unit / integration suite", "22 / 22 passed", GREEN),
    ("Ledger & inventory audit", "2,166 / 2,166 passed", GREEN),
    ("JavaScript syntax", "app.js + ios-nav.js passed", GREEN),
    ("CSS asset audit", "Local URLs resolved", GREEN),
    ("Live route crawl", "Public + 5 demo roles", GREEN),
    ("Room Board SSE", "200 · JSON event · 369 rooms", GREEN),
]
for i, (name, result, accent) in enumerate(checks):
    y = 3.82 + i * 0.38
    line(slide, 0.80, y + 0.21, 0.98, y + 0.21, color=accent, width=2.2)
    text(slide, name, 1.10, y, 3.35, 0.23, size=11.2, color=INK, bold=True)
    text(slide, result, 4.72, y, 3.18, 0.23, size=10.7, color=MUTED)
# audit fix box
card(slide, 8.34, 3.50, 4.08, 2.91, fill=NAVY, border=NAVY)
text(slide, "ONE DEFECT FOUND → FIXED", 8.68, 3.83, 2.92, 0.22, size=10, color=GOLD, bold=True, char_spacing=0.8)
text(slide, "Zero-total folios\nwere being expected\nas open by the audit.", 8.68, 4.25, 3.06, 0.84, size=20, color=WHITE, bold=True, font="Aptos Display")
text(slide, "The command now mirrors Invoice.recalc_status(): zero balance + no payments = paid. A finance regression test protects the rule.", 8.68, 5.28, 3.00, 0.60, size=10.7, color=RGBColor(214, 224, 237))
footer(slide, 14)

# --- Slide 15: limitations / roadmap ----------------------------------------
slide = add_slide(bg=WHITE)
section_header(slide, "14 · Limitations & next steps", "A strong v1 with a clear scale path", "The platform is demo-ready and operationally coherent; these are the deliberate next investments.", 15)
# limitations
card(slide, 0.72, 2.03, 5.70, 4.43, fill=PALE, border=LINE)
text(slide, "CURRENT LIMITATIONS", 1.04, 2.34, 2.5, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
bullet_list(slide, [
    "SQLite is the demo default; PostgreSQL is the production path.",
    "Room Board is soft real-time SSE polling; pub/sub is the scale upgrade.",
    "No payment gateway or channel-manager / OTA sync yet.",
    "No folio postings for minibar, spa or restaurant charges.",
    "Playwright, load testing and EN / KM localization remain future work.",
], 1.04, 2.80, 4.85, 2.24, size=12.5, color=INK, bullet_color=RED, line_h=0.32, gap=0.12)
pill(slide, "transparent about scope", 1.04, 5.73, 1.68, fill=RED_PALE, color=RED)
# roadmap
text(slide, "RECOMMENDED ROADMAP", 6.92, 2.34, 2.7, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
road = [
    ("01", "Production data layer", "Postgres daterange + exclusion constraint; Redis availability cache."),
    ("02", "Commercial connectivity", "DRF channel-manager API, OTA sync, rate plans and webhooks."),
    ("03", "Hotel accounting", "Folio line items, night audit close and business-day controls."),
    ("04", "Ops maturity", "Celery beat, transactional email, Sentry and request IDs."),
]
for i, (n, h, d) in enumerate(road):
    y = 2.78 + i * 0.77
    text(slide, n, 6.94, y, 0.40, 0.24, size=14, color=GOLD, bold=True, font="Aptos Display")
    text(slide, h, 7.58, y, 2.55, 0.23, size=13, color=INK, bold=True)
    text(slide, d, 7.58, y + 0.27, 4.55, 0.29, size=10.2, color=MUTED)
    if i < 3: line(slide, 7.58, y + 0.64, 12.02, y + 0.64, color=LINE, width=0.6)
footer(slide, 15)

# --- Slide 16: class demo / takeaway ----------------------------------------
slide = add_slide(bg=NAVY)
section_header(slide, "15 · Takeaway", "Aurelia is a connected hotel system", "The strongest part of the project is not one screen — it is the consistency of the rules underneath every screen.", 16, dark=True)
# three takeaways
cards = [
    ("For guests", "Premium discovery and booking with clear price, capacity and self-service.", GOLD),
    ("For staff", "Role-aware workflows that keep reservations, rooms, tasks and money aligned.", BLUE),
    ("For the system", "Tested domain services, explicit invariants and a roadmap to production scale.", GREEN),
]
for i, (h, d, accent) in enumerate(cards):
    x = 0.78 + i * 4.16
    card(slide, x, 2.18, 3.76, 1.95, fill=RGBColor(25, 43, 72), border=RGBColor(60, 80, 111))
    shape(slide, MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, 2.18, 3.76, 0.07, fill=accent, line=None)
    text(slide, h, x + 0.28, 2.56, 2.8, 0.28, size=18, color=WHITE, bold=True, font="Aptos Display")
    text(slide, d, x + 0.28, 3.05, 3.06, 0.60, size=12, color=RGBColor(214, 224, 237))
# class demo flow
text(slide, "SUGGESTED LIVE DEMO", 0.80, 4.72, 2.5, 0.23, size=10, color=GOLD, bold=True, char_spacing=1.1)
demo = ["Guest searches a room", "Staff sees the reservation", "Check-in / check-out changes inventory", "Folio and housekeeping reconcile"]
for i, item in enumerate(demo):
    x = 0.82 + i * 3.04
    if i < 3:
        line(slide, x + 2.38, 5.49, x + 2.90, 5.49, color=RGBColor(92, 116, 151), width=1.4)
        shape(slide, MSO_AUTO_SHAPE_TYPE.CHEVRON, x + 2.77, 5.40, 0.18, 0.18, fill=RGBColor(92, 116, 151), line=None)
    shape(slide, MSO_AUTO_SHAPE_TYPE.OVAL, x, 5.19, 0.60, 0.60, fill=GOLD, line=None)
    text(slide, str(i + 1), x, 5.33, 0.60, 0.25, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    text(slide, item, x + 0.78, 5.19, 1.88, 0.51, size=11, color=WHITE, bold=True)
card(slide, 0.80, 6.35, 11.73, 0.44, fill=RGBColor(25, 43, 72), border=RGBColor(60, 80, 111))
text(slide, "Project evidence: README.md  ·  QA-REPORT.md  ·  CHANGELOG.md  ·  live preview on port 8000", 1.06, 6.47, 11.2, 0.18, size=9.5, color=RGBColor(193, 207, 225), align=PP_ALIGN.CENTER)
footer(slide, 16, dark=True)

# --- Slide 17: latest UI refinement ------------------------------------------
slide = add_slide(bg=PALE)
section_header(slide, "16 · Latest build update", "The hero now has one visual story", "A final polish pass removed the duplicate image/scrim layer identified during preview review.", 17)
# Updated visual treatment
card(slide, 0.72, 1.98, 6.20, 4.72, fill=NAVY, border=NAVY)
image_cover(slide, ROOT / "static/img/hero.jpg", 0.72, 1.98, 6.20, 3.08, overlay=NAVY, transparency=42)
text(slide, "LATEST UI REFINEMENT", 1.08, 2.32, 2.7, 0.22, size=10, color=GOLD, bold=True, char_spacing=1.1)
text(slide, "Brighter image depth.\nSame premium hierarchy.", 1.08, 2.70, 4.80, 0.76, size=25, color=WHITE, bold=True, font="Aptos Display")
pill(slide, "single controlled scrim", 1.08, 4.24, 1.72, fill=RGBColor(45, 61, 86), color=WHITE)
pill(slide, "parallax retained", 2.98, 4.24, 1.42, fill=RGBColor(45, 61, 86), color=WHITE)
# mini CTA treatment
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 1.08, 4.86, 1.60, 0.42, fill=GOLD, line=None)
text(slide, "Explore rooms", 1.22, 4.98, 1.32, 0.16, size=10, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
shape(slide, MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, 2.88, 4.86, 1.68, 0.42, fill=RGBColor(255,255,255), line=RGBColor(255,255,255))
text(slide, "Discover the hotel", 3.00, 4.98, 1.44, 0.16, size=9.5, color=INK, bold=True, align=PP_ALIGN.CENTER)
text(slide, "The composition remains recognizably Aurelia: gold accent, dark navy framing, and a clear action path.", 1.08, 5.70, 5.15, 0.46, size=11.2, color=RGBColor(214, 224, 237))
# right evidence column
text(slide, "WHAT CHANGED", 7.48, 2.10, 2.3, 0.22, size=10, color=GOLD, bold=True, char_spacing=1.1)
latest = [
    ("01", "Removed duplicate background", "The parallax .hero-bg now owns the photograph and overlay."),
    ("02", "Reduced visual heaviness", "The remaining scrim protects text without burying the property image."),
    ("03", "Rechecked the build", "Home 200 · 22/22 tests · 2,160 ledger checks · CSS / JS passed."),
]
for i, (n, h, d) in enumerate(latest):
    y = 2.55 + i * 1.02
    text(slide, n, 7.50, y, 0.42, 0.26, size=14, color=GOLD, bold=True, font="Aptos Display")
    text(slide, h, 8.16, y, 3.80, 0.24, size=14, color=INK, bold=True)
    text(slide, d, 8.16, y + 0.31, 3.84, 0.38, size=10.7, color=MUTED)
    if i < 2: line(slide, 8.16, y + 0.78, 12.05, y + 0.78, color=LINE, width=0.6)
card(slide, 7.48, 5.78, 4.55, 0.57, fill=GREEN_PALE, border=GREEN)
text(slide, "Preview remains running on port 8000.", 7.80, 5.96, 3.93, 0.20, size=11, color=GREEN, bold=True)
footer(slide, 17)

# Core properties metadata for a consistent, portable deck.
for s in prs.slides:
    for shp in s.shapes:
        if not shp.has_text_frame:
            continue
        for p in shp.text_frame.paragraphs:
            for r in p.runs:
                # Use theme-safe fallbacks where available.
                if not r.font.name:
                    r.font.name = "Aptos"

prs.core_properties.title = "Aurelia Collection — Hotel Booking & Property Management System"
prs.core_properties.subject = "Class presentation of the complete Aurelia Collection project"
prs.core_properties.author = "Aurelia Collection project team"
prs.core_properties.keywords = "Django, hotel PMS, booking, Cambodia, QA"
prs.core_properties.comments = "Class-ready project presentation generated from the latest QA-clean build."
prs.save(OUT)
print(OUT)
