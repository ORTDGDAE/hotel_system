from pathlib import Path
from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Aurelia_Collection_Hotel_Management_Project_17_Slides_KH_Latest.pptx"
prs = Presentation(str(OUT))

FONT = "Noto Sans Khmer"


def set_font(run, size=None, bold=None):
    run.font.name = FONT
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    # Set the East Asian and complex-script typefaces as well as Latin so
    # Khmer and English labels render consistently in PowerPoint.
    rpr = run._r.get_or_add_rPr()
    for attr in ("latin", "ea", "cs"):
        rpr.set(qn(f"a:{attr}"), FONT)


def style_shape(shape, size, *, bold=None, fit=False, margins=True):
    if not hasattr(shape, "text_frame") or not shape.text.strip():
        return
    tf = shape.text_frame
    tf.word_wrap = True
    if margins:
        tf.margin_left = Inches(0.06)
        tf.margin_right = Inches(0.06)
        tf.margin_top = Inches(0.03)
        tf.margin_bottom = Inches(0.03)
    if fit:
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    for p in tf.paragraphs:
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        p.line_spacing = 1.0
        for run in p.runs:
            set_font(run, size, bold=bold)


# Tighten the two densest narrative areas without sacrificing any project facts.
slide5 = prs.slides[4]
for shape in slide5.shapes:
    if hasattr(shape, "text") and shape.text.startswith("Room Board បង្ហាញ Dirty"):
        shape.text = (
            "Room Board បង្ហាញ Dirty; បង្កើត Cleaning Task ដែលបង្ហាញលេខបន្ទប់ "
            "និងប្រភេទបន្ទប់។ Property Manager ប្រគល់ទៅ Housekeeping។"
        )

slide15 = prs.slides[14]
for shape in slide15.shapes:
    if hasattr(shape, "text") and "Booking រក្សា Rate Detail" in shape.text:
        shape.text = (
            "• Booking រក្សា Rate Detail និង Total។\n"
            "• Discount, Tax និង Total រក្សាជាមួយការកក់។\n"
            "• Catalog ថ្មីមិនកែប្រវត្តិ; Invoice ចាស់ និង Pricing Snapshot ចាស់ "
            "មិនត្រូវបានសរសេរឡើងវិញ។\n"
            "• Deposit និង Partial Payment កត់ត្រាតាមដំណាក់កាល; បង់លើសត្រូវបានបដិសេធ។\n"
            "• Check-out ត្រូវទូទាត់សមតុល្យ; Cancellation និង Refund មាន Audit។"
        )

slide16 = prs.slides[15]
for shape in slide16.shapes:
    if hasattr(shape, "text") and shape.text.startswith("កំណែបច្ចុប្បន្នត្រៀម"):
        shape.text = (
            "កំណែបច្ចុប្បន្នត្រៀមសម្រាប់ Demo និងប្រើប្រាស់: ១០ Receptionists "
            "(១ ក្នុងមួយសណ្ឋាគារ), ១០ Property Manager (១ ក្នុងមួយសណ្ឋាគារ) "
            "និង ៣០ Housekeepers (៣ ក្នុងមួយសណ្ឋាគារ)។"
        )

slide17 = prs.slides[16]
for shape in slide17.shapes:
    if hasattr(shape, "text") and shape.text.startswith("កំណែនេះត្រៀមសម្រាប់ការបង្ហាញ"):
        shape.text = (
            "QA និងទិន្នន័យបច្ចុប្បន្ន: ៤១/៤១ តេស្ត · ២,១៦០ Invariant checks · "
            "១៧០ Booking · ១០៣ Payment។"
        )

# Apply a restrained type scale: strong titles, readable Khmer body copy,
# compact metadata, and a consistent footer/page-number treatment.
for slide_no, slide in enumerate(prs.slides, start=1):
    for shape in slide.shapes:
        if not hasattr(shape, "text") or not shape.text.strip():
            continue
        text = " ".join(shape.text.split())
        top = shape.top / 914400
        height = shape.height / 914400
        width = shape.width / 914400

        # Footer and slide number.
        if top > 7.0 or text.isdigit() and len(text) == 2:
            style_shape(shape, 8.0 if top > 7.0 else 8.5)
            continue

        # Small section kicker.
        if top < 0.62:
            style_shape(shape, 9.5)
            continue

        # Main title.
        if 0.62 <= top < 1.2 and height >= 0.45:
            style_shape(shape, 25.0 if slide_no >= 11 else 24.0, bold=True)
            continue

        # Intro/standfirst immediately below the title.
        if 1.2 <= top < 1.85:
            style_shape(shape, 10.0)
            continue

        # Large numeric/value callouts retain their visual weight.
        if (text.startswith("$") and height >= 0.25) or text in {"10", "24", "5%", "0%", "1"}:
            style_shape(shape, 24.0, bold=True)
            continue
        if text == "$30" and slide_no == 6:
            style_shape(shape, 38.0, bold=True)
            continue
        if text == "$30 → $460":
            style_shape(shape, 28.0, bold=True)
            continue

        # Slide 14 is a compact permissions matrix.
        if slide_no == 14 and 2.0 <= top < 6.1:
            style_shape(shape, 8.6, fit=True)
            continue

        # Slide 15 narrative panel is dense by design; keep it readable.
        if slide_no == 15 and text.startswith("•"):
            style_shape(shape, 8.9, fit=True)
            continue

        # Demo/list panels benefit from a slightly tighter line height.
        if height >= 1.0:
            style_shape(shape, 9.3, fit=True)
        elif height >= 0.4:
            style_shape(shape, 9.6, fit=True)
        elif height <= 0.3 and top >= 2.0:
            style_shape(shape, 12.0, bold=True)
        else:
            style_shape(shape, 9.6, fit=True)

# Reassert especially important callouts after the generic pass.
for slide_no, indices in {
    1: [(10, 24), (14, 24), (18, 24)],
    2: [(19, 24), (23, 24), (27, 24), (31, 24)],
    6: [(6, 38), (20, 28)],
    17: [(18, 17), (19, 17), (20, 17), (21, 15), (27, 9.5)],
}.items():
    slide = prs.slides[slide_no - 1]
    for idx, size in indices:
        if idx < len(slide.shapes):
            style_shape(slide.shapes[idx], size, bold=True)

prs.core_properties.comments = (
    "Refined Khmer presentation layout: balanced type scale, consistent Khmer font, "
    "readable dense panels, and clearer visual hierarchy."
)
prs.save(OUT)
print(OUT)
