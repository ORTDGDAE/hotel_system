from __future__ import annotations

from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "Aurelia_Collection_Hotel_Management_Project_16_Slides_KH.pptx"
OUT = ROOT / "Aurelia_Collection_Hotel_Management_Project_17_Slides_KH_Latest.pptx"
prs = Presentation(str(BASE))
slide = prs.slides.add_slide(prs.slide_layouts[6])

NAVY = RGBColor(11, 20, 39)
NAVY2 = RGBColor(25, 52, 92)
NAVY3 = RGBColor(43, 77, 119)
GOLD = RGBColor(195, 161, 90)
PALE_GOLD = RGBColor(243, 227, 184)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(15, 23, 42)
MUTED = RGBColor(100, 116, 139)
GREEN = RGBColor(6, 118, 71)
BLUE = RGBColor(37, 99, 235)
LINE = RGBColor(226, 232, 240)
LIGHT_GOLD = RGBColor(246, 239, 223)
LIGHT_GREEN = RGBColor(236, 253, 243)

slide.background.fill.solid(); slide.background.fill.fore_color.rgb = NAVY


def shape(kind, x, y, w, h, fill=None, line=None):
    shp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = line; shp.line.width = Pt(.8)
    return shp


def rounded(x, y, w, h, fill=WHITE, line=None):
    return shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, y, w, h, fill, line)


def rect(x, y, w, h, fill, line=None):
    return shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, y, w, h, fill, line)


def text(value, x, y, w, h, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = value; r.font.name = "Noto Sans Khmer"; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return box


def bullets(items, x, y, w, h, size=10.5, color=INK, bullet_color=GOLD):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.04); tf.margin_top = tf.margin_bottom = Inches(.02)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(7); p.text = ""
        r = p.add_run(); r.text = "•  "; r.font.name = "Noto Sans Khmer"; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = bullet_color
        r2 = p.add_run(); r2.text = item; r2.font.name = "Noto Sans Khmer"; r2.font.size = Pt(size); r2.font.color.rgb = color
    return box

# Heading
text("សេចក្តីសង្ខេបចុងក្រោយ", .62, .40, 5.5, .25, 9.5, GOLD, True, margin=0)
text("Aurelia Collection ក្នុងមួយប្រយោគ", .62, .72, 11.8, .58, 26, WHITE, True, margin=0)
text("ប្រព័ន្ធតែមួយ សម្រាប់ភ្ញៀវ ក្រុមសណ្ឋាគារ និងម្ចាស់អាជីវកម្ម — ចាប់ពីការស្វែងរក រហូតដល់ការទូទាត់ និងរបាយការណ៍។", .64, 1.35, 11.45, .38, 10.8, RGBColor(205,216,232), margin=0)
text("17", 12.35, .42, .40, .22, 9, RGBColor(205,216,232), True, align=PP_ALIGN.RIGHT, margin=0)

# Three summary pillars
items = [
    ("សម្រាប់ភ្ញៀវ", "ស្វែងរកបន្ទប់, កក់ដោយងាយ, មើលតម្លៃសរុប, គ្រប់គ្រង My Stays និងទទួលសេវាដែលច្បាស់លាស់។", GOLD),
    ("សម្រាប់ក្រុមការងារ", "Reception, Housekeeping និង Manager ប្រើទិន្នន័យតែមួយ ដើម្បីគ្រប់គ្រងការកក់, បន្ទប់ និងការស្នាក់នៅ។", GREEN),
    ("សម្រាប់អាជីវកម្ម", "ម្ចាស់សណ្ឋាគារឃើញ Occupancy, Revenue, Payment និង Folio ដោយមាន Snapshot និង Audit ដែលអាចទុកចិត្តបាន។", BLUE),
]
for i, (title, desc, accent) in enumerate(items):
    x = .78 + i * 4.13
    rounded(x, 2.02, 3.63, 1.72, RGBColor(23,40,68), RGBColor(69,92,125))
    rect(x, 2.02, .055, 1.72, accent)
    text(title, x+.24, 2.28, 3.15, .25, 13, PALE_GOLD, True, margin=0)
    text(desc, x+.24, 2.80, 3.12, .62, 9.6, RGBColor(215,226,239), margin=0)

# Key facts band
rounded(.78, 4.18, 11.84, 1.25, PALE_GOLD, None)
text("ចំណុចសំខាន់ៗ", 1.08, 4.43, 2.0, .22, 12, NAVY, True, margin=0)
text("សណ្ឋាគារ ១០", 3.25, 4.37, 1.65, .28, 17, NAVY, True, margin=0)
text("ប្រភេទបន្ទប់ ២៤", 5.05, 4.37, 2.05, .28, 17, NAVY, True, margin=0)
text("$30–$460", 7.28, 4.37, 1.65, .28, 17, NAVY, True, margin=0)
text("Tax 5% · Service 0%", 9.15, 4.37, 2.80, .28, 15, NAVY, True, margin=0)
text("តម្លៃចាប់ផ្តើម", 3.25, 4.82, 1.65, .18, 8.8, RGBColor(85,67,27), margin=0)
text("ទិន្នន័យបន្ទប់", 5.05, 4.82, 2.05, .18, 8.8, RGBColor(85,67,27), margin=0)
text("Catalog បច្ចុប្បន្ន", 7.28, 4.82, 1.65, .18, 8.8, RGBColor(85,67,27), margin=0)
text("ពន្ធតែប៉ុណ្ណោះ", 9.15, 4.82, 2.80, .18, 8.8, RGBColor(85,67,27), margin=0)

# Closing message
rounded(.78, 5.82, 11.84, .72, NAVY2, RGBColor(69,92,125))
text("កំណែនេះត្រៀមសម្រាប់ការបង្ហាញ និងការផ្ទៀងផ្ទាត់ Database របស់ម្ចាស់ប្រព័ន្ធ។ ជំហានបន្ទាប់: MySQL/Navicat និង OTA Channel Manager។", 1.04, 6.05, 11.34, .22, 10.4, WHITE, True, align=PP_ALIGN.CENTER, margin=0)

rect(.62, 7.10, 12.08, .008, RGBColor(70,92,125))
text("Aurelia Collection · គម្រោងគ្រប់គ្រងសណ្ឋាគារ · ២៩ កញ្ញា ២០២៦", .64, 7.16, 10.0, .18, 8.0, RGBColor(185,198,218), margin=0)
text("17", 12.15, 7.13, .55, .22, 8.5, RGBColor(185,198,218), True, align=PP_ALIGN.RIGHT, margin=0)

prs.core_properties.title = "Aurelia Collection — គម្រោងគ្រប់គ្រងសណ្ឋាគារ · ១៧ ស្លាយជាភាសាខ្មែរ"
prs.core_properties.subject = "បទបង្ហាញ Khmer ចុងក្រោយ ជាមួយសេចក្តីសង្ខេបគម្រោងនៅស្លាយចុងក្រោយ"
prs.core_properties.comments = "Latest 17-slide Khmer deck with a concise final summary slide."
prs.save(OUT)
print(OUT)
