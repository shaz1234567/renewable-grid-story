"""Build the final PDF report and PowerPoint deck from repository evidence.

Run from the repository root:
    python scripts/build_academic_package.py
"""

from __future__ import annotations

import html
import re
import shutil
import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "report" / "final_report.md"
REPORT_PDF = ROOT / "report" / "final_report.pdf"
SLIDES_PPTX = ROOT / "presentation" / "slides.pptx"
SPEAKER_NOTES_MD = ROOT / "presentation" / "speaker_notes.md"
SCREENSHOTS = ROOT / "report" / "screenshots"
OVERLEAF_DIR = ROOT / "report" / "overleaf"
OVERLEAF_ZIP = ROOT / "report" / "renewable-grid-story-overleaf.zip"

GREEN = RGBColor(20, 125, 100)
DARK = RGBColor(24, 48, 43)
PALE = RGBColor(237, 244, 241)
GOLD = RGBColor(243, 182, 31)
WHITE = RGBColor(255, 255, 255)


def _inline_markdown(text: str) -> str:
    """Convert the small inline Markdown subset used by the report."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    escaped = re.sub(
        r"&lt;(https?://[^&]+)&gt;",
        r'<link href="\1" color="#147d64">\1</link>',
        escaped,
    )
    return escaped


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=colors.HexColor("#18302b"),
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )
    for name, size, before, after in [
        ("H1Custom", 16, 14, 7),
        ("H2Custom", 13, 11, 5),
        ("H3Custom", 11, 8, 4),
    ]:
        styles.add(
            ParagraphStyle(
                name=name,
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=size,
                leading=size + 3,
                textColor=colors.HexColor("#147d64"),
                spaceBefore=before,
                spaceAfter=after,
                keepWithNext=True,
            )
        )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.2,
            textColor=colors.HexColor("#18302b"),
            spaceAfter=6,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CaptionCustom",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#4f625d"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeCustom",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=12,
            backColor=colors.HexColor("#edf4f1"),
            borderPadding=5,
            spaceAfter=7,
        )
    )
    return styles


def _parse_table(lines: list[str], styles) -> Table:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append([Paragraph(_inline_markdown(cell), styles["BodyCustom"]) for cell in cells])
    width = 7.0 * inch
    table = Table(rows, colWidths=[width / len(rows[0])] * len(rows[0]), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#147d64")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.4),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8cbc5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8f7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_pdf() -> None:
    styles = _pdf_styles()
    lines = REPORT_MD.read_text(encoding="utf-8").splitlines()
    story = []
    paragraph_buffer: list[str] = []
    list_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph_buffer:
            story.append(
                Paragraph(_inline_markdown(" ".join(paragraph_buffer)), styles["BodyCustom"])
            )
            paragraph_buffer.clear()

    def flush_list() -> None:
        if list_buffer:
            items = [
                ListItem(Paragraph(_inline_markdown(item), styles["BodyCustom"]))
                for item in list_buffer
            ]
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    leftIndent=20,
                    bulletFontName="Helvetica",
                    bulletFontSize=7,
                    spaceAfter=6,
                )
            )
            list_buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                story.append(
                    Paragraph(
                        "<br/>".join(html.escape(x) for x in code_buffer),
                        styles["CodeCustom"],
                    )
                )
                code_buffer.clear()
            in_code = not in_code
            i += 1
            continue
        if in_code:
            code_buffer.append(line)
            i += 1
            continue
        image_match = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph()
            flush_list()
            caption, relative_path = image_match.groups()
            image_path = REPORT_MD.parent / relative_path
            image = Image(str(image_path), width=7.0 * inch, height=3.8 * inch)
            story.append(
                KeepTogether(
                    [
                        image,
                        Spacer(1, 3),
                        Paragraph(_inline_markdown(caption), styles["CaptionCustom"]),
                    ]
                )
            )
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            flush_paragraph()
            flush_list()
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(_parse_table(table_lines, styles))
            story.append(Spacer(1, 7))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            title = heading.group(2)
            if level == 1:
                style = styles["ReportTitle"]
            elif level == 2:
                style = styles["H1Custom"]
                if title.startswith(("4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.", "References")):
                    story.append(PageBreak())
            else:
                style = styles["H2Custom"]
            story.append(Paragraph(_inline_markdown(title), style))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line) or line.startswith("- "):
            flush_paragraph()
            list_buffer.append(re.sub(r"^(?:\d+\.|-)\s+", "", line))
            i += 1
            continue
        if line.startswith(r"\[") or (line.startswith(r"\(") and line.endswith(r"\]")):
            flush_paragraph()
            flush_list()
            story.append(Paragraph(html.escape(line), styles["CodeCustom"]))
            i += 1
            continue
        if not line.strip():
            flush_paragraph()
            flush_list()
        else:
            paragraph_buffer.append(line.strip())
        i += 1
    flush_paragraph()
    flush_list()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#b8cbc5"))
        canvas.line(0.7 * inch, 0.52 * inch, 7.8 * inch, 0.52 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#4f625d"))
        canvas.drawString(0.7 * inch, 0.34 * inch, "Shazab Ali · The Renewable Grid, Hour by Hour")
        canvas.drawRightString(7.8 * inch, 0.34 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.68 * inch,
        title="The Renewable Grid, Hour by Hour",
        author="Shazab Ali",
        subject="Final academic report",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def _set_background(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_title(slide, title: str, subtitle: str | None = None, dark: bool = False) -> None:
    box = slide.shapes.add_textbox(Inches(0.65), Inches(0.38), Inches(12), Inches(0.8))
    p = box.text_frame.paragraphs[0]
    p.text = title
    p.font.name = "Aptos Display"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE if dark else DARK
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.68), Inches(1.05), Inches(11.8), Inches(0.45))
        p = sub.text_frame.paragraphs[0]
        p.text = subtitle
        p.font.name = "Aptos"
        p.font.size = Pt(12)
        p.font.color.rgb = PALE if dark else GREEN


def _add_footer(slide, number: int, dark: bool = False) -> None:
    line = slide.shapes.add_shape(1, Inches(0.65), Inches(7.16), Inches(12), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = GREEN if not dark else PALE
    line.line.fill.background()
    box = slide.shapes.add_textbox(Inches(0.68), Inches(7.2), Inches(11.9), Inches(0.2))
    p = box.text_frame.paragraphs[0]
    p.text = f"Shazab Ali · Renewable Grid Story                                      {number}"
    p.font.name = "Aptos"
    p.font.size = Pt(8)
    p.font.color.rgb = PALE if dark else DARK


def _speaker_notes_by_slide() -> dict[int, str]:
    """Extract the 13 timed slide sections for native PowerPoint notes."""
    notes: dict[int, list[str]] = {}
    current: int | None = None
    for line in SPEAKER_NOTES_MD.read_text().splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            slide_match = re.search(r"\bSlide\s+(\d+)\b", heading.group(1))
            if slide_match:
                current = int(slide_match.group(1))
                notes[current] = [heading.group(1)]
            elif current and not any(
                marker in heading.group(1)
                for marker in ("Live-demo route checklist", "Backup checklist")
            ):
                notes[current].append(heading.group(1))
            else:
                current = None
            continue
        if current:
            notes[current].append(line)
    return {
        number: "\n".join(lines).strip()
        for number, lines in notes.items()
        if "\n".join(lines).strip()
    }


def _add_native_speaker_notes(prs: Presentation) -> None:
    notes = _speaker_notes_by_slide()
    if len(notes) != len(prs.slides):
        raise RuntimeError(
            f"Expected notes for {len(prs.slides)} slides, found {len(notes)}."
        )
    for number, slide in enumerate(prs.slides, start=1):
        slide.notes_slide.notes_text_frame.text = notes[number]


def _add_bullets(slide, bullets: list[str], x=0.8, y=1.55, w=5.5, h=5.1, dark=False) -> None:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.clear()
    for index, text in enumerate(bullets):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = text
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(19)
        p.font.color.rgb = WHITE if dark else DARK
        p.space_after = Pt(12)
        p.bullet = True


def _add_picture(slide, filename: str, x=6.25, y=1.45, w=6.45) -> None:
    slide.shapes.add_picture(str(SCREENSHOTS / filename), Inches(x), Inches(y), width=Inches(w))


def _stat_card(slide, x: float, y: float, value: str, label: str, width=2.75) -> None:
    shape = slide.shapes.add_shape(5, Inches(x), Inches(y), Inches(width), Inches(1.25))
    shape.fill.solid()
    shape.fill.fore_color.rgb = PALE
    shape.line.color.rgb = GREEN
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = value
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Aptos Display"
    p.font.size = Pt(23)
    p.font.bold = True
    p.font.color.rgb = GREEN
    p2 = tf.add_paragraph()
    p2.text = label
    p2.alignment = PP_ALIGN.CENTER
    p2.font.name = "Aptos"
    p2.font.size = Pt(10)
    p2.font.color.rgb = DARK


def build_slides() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    slide = prs.slides.add_slide(blank)
    _set_background(slide, DARK)
    accent = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.22), Inches(7.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = GOLD
    accent.line.fill.background()
    box = slide.shapes.add_textbox(Inches(0.85), Inches(1.45), Inches(11.7), Inches(2.0))
    p = box.text_frame.paragraphs[0]
    p.text = "The Renewable Grid,\nHour by Hour"
    p.font.name = "Aptos Display"
    p.font.size = Pt(43)
    p.font.bold = True
    p.font.color.rgb = WHITE
    sub = slide.shapes.add_textbox(Inches(0.9), Inches(4.1), Inches(10.8), Inches(1.2))
    p = sub.text_frame.paragraphs[0]
    p.text = "A six-view interactive story using 2025 EIA-930 data\nShazab Ali · 13-minute explanation and live demo"
    p.font.name = "Aptos"
    p.font.size = Pt(20)
    p.font.color.rgb = PALE
    _add_footer(slide, 1, dark=True)

    slide = prs.slides.add_slide(blank)
    _add_title(slide, "Question, audience, and design")
    _add_bullets(
        slide,
        [
            "Question: how do renewable patterns change across hours, seasons, and regions?",
            "Audience: students, instructors, and interested public readers.",
            "Design: context → rhythm → seasons → regions → variability → portfolio.",
            "Guardrail: descriptive evidence, not dispatch causation or forecasting.",
        ],
        w=11.5,
    )
    _add_footer(slide, 2)

    slide = prs.slides.add_slide(blank)
    _add_title(slide, "Reproducible data workflow", "EIA-930 → verified archives → 35,040 hourly records → six views")
    steps = [
        ("1", "Verify", "MD5 + SHA-256"),
        ("2", "Prepare", "adjusted → imputed → raw"),
        ("3", "Aggregate", "solar + wind + hydro"),
        ("4", "Validate", "11 explicit checks"),
    ]
    for idx, (n, title, detail) in enumerate(steps):
        x = 0.65 + idx * 3.15
        shape = slide.shapes.add_shape(5, Inches(x), Inches(2.0), Inches(2.65), Inches(2.35))
        shape.fill.solid()
        shape.fill.fore_color.rgb = PALE
        shape.line.color.rgb = GREEN
        tf = shape.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = n
        p.font.size = Pt(31)
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.alignment = PP_ALIGN.CENTER
        p = tf.add_paragraph()
        p.text = title
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = DARK
        p.alignment = PP_ALIGN.CENTER
        p = tf.add_paragraph()
        p.text = detail
        p.font.size = Pt(12)
        p.font.color.rgb = GREEN
        p.alignment = PP_ALIGN.CENTER
    _add_bullets(
        slide,
        ["One-hour average MW sums to MWh; daily charts use available-hour means."],
        x=1.2,
        y=5.05,
        w=11.0,
        h=1,
    )
    _add_footer(slide, 3)

    slide = prs.slides.add_slide(blank)
    _add_title(slide, "Validation is transparent—not “all clean”")
    _stat_card(slide, 0.8, 1.5, "10 / 11", "validation checks passed")
    _stat_card(slide, 3.85, 1.5, "31", "missing renewable/mix rows")
    _stat_card(slide, 6.9, 1.5, "0", "aggregation mismatches")
    _stat_card(slide, 9.95, 1.5, "20", "automated tests")
    _add_bullets(
        slide,
        [
            "All four authorities have 8,760 rows and continuous hourly UTC timestamps.",
            "25 demand and net-generation values are also missing.",
            "Gaps remain gaps and are disclosed beside each chart.",
        ],
        x=1.0,
        y=3.35,
        w=11.2,
        h=2.6,
    )
    _add_footer(slide, 4)

    view_slides = [
        (
            "View 1 · Whole-system context",
            "view-1-generation-mix.png",
            ["Daily stacked mix", "CISO June 15: solar leads at 35.1% of positive reported mix"],
        ),
        (
            "View 2 · Hourly rhythm",
            "view-2-hourly-rhythm.png",
            ["Previous / Play / Next / Reset", "Dynamic 23-, 24-, or 25-observation boundary"],
        ),
        (
            "View 3 · Annual pulse",
            "view-3-source-comparison.png",
            ["Daily means expose seasonal structure", "Normalized = percent of each source’s own peak"],
        ),
        (
            "View 4 · Regional context",
            "view-4-regional-comparison.png",
            ["Matched source and dates", "ERCO mean solar ≈ 1.36× CISO in 2025"],
        ),
        (
            "View 5 · Quantified variability",
            "view-5-variability.png",
            ["CISO solar mean 5,667.9 MW", "CV 1.203; zero mean returns undefined"],
        ),
        (
            "View 6 · Portfolio test",
            "view-6-portfolio.png",
            ["CISO combined CV 0.590", "Lower than solar/wind—not lower than hydro (0.463)"],
        ),
    ]
    for number, (title, filename, bullets) in enumerate(view_slides, start=5):
        slide = prs.slides.add_slide(blank)
        _add_title(slide, title)
        _add_bullets(slide, bullets, x=0.72, y=1.55, w=4.65, h=4.7)
        _add_picture(slide, filename, x=5.1, y=1.42, w=7.75)
        _add_footer(slide, number)

    slide = prs.slides.add_slide(blank)
    _add_title(slide, "2025: scale and share tell different stories")
    cards = [
        ("CISO", "90.8M MWh", "48.744%"),
        ("ERCO", "182.8M MWh", "37.583%"),
        ("NYIS", "31.1M MWh", "23.500%"),
        ("PJM", "72.3M MWh", "8.255%"),
    ]
    for idx, (ba, energy, share) in enumerate(cards):
        x = 0.7 + idx * 3.15
        shape = slide.shapes.add_shape(5, Inches(x), Inches(1.65), Inches(2.7), Inches(3.25))
        shape.fill.solid()
        shape.fill.fore_color.rgb = PALE
        shape.line.color.rgb = GREEN
        tf = shape.text_frame
        tf.clear()
        for j, text in enumerate([ba, energy, "renewable energy", share, "share of net generation"]):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.text = text
            p.alignment = PP_ALIGN.CENTER
            p.font.name = "Aptos"
            p.font.size = Pt(23 if j in (0, 1, 3) else 10)
            p.font.bold = j in (0, 1, 3)
            p.font.color.rgb = GREEN if j in (0, 1, 3) else DARK
    _add_bullets(
        slide,
        ["ERCO leads absolute renewable output; CISO leads renewable share."],
        x=1.15,
        y=5.35,
        w=11,
        h=0.7,
    )
    _add_footer(slide, 11)

    slide = prs.slides.add_slide(blank)
    _add_title(slide, "Evaluation, limitations, and next step")
    _add_bullets(
        slide,
        [
            "Completed: 21 tests; internal desktop/mobile checks; one visual-feedback revision.",
            "Pending: broader target-audience comprehension testing.",
            "Limits: one year, four authorities, reporting gaps, schematic map, descriptive CV.",
            "Verified Render deployment; local app and screenshots remain presentation backups.",
        ],
        w=11.5,
    )
    _add_footer(slide, 12)

    slide = prs.slides.add_slide(blank)
    _set_background(slide, DARK)
    _add_title(slide, "Class question", "Before the final demo result…", dark=True)
    q = slide.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(11.3), Inches(2.3))
    p = q.text_frame.paragraphs[0]
    p.text = "If solar, wind, and hydropower are combined,\nwill the portfolio always have the lowest CV?"
    p.font.name = "Aptos Display"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    a = slide.shapes.add_textbox(Inches(1.5), Inches(5.05), Inches(10.3), Inches(0.8))
    p = a.text_frame.paragraphs[0]
    p.text = "CISO 2025 answer: no—the portfolio beats solar and wind, but not hydropower."
    p.font.name = "Aptos"
    p.font.size = Pt(19)
    p.font.color.rgb = GOLD
    p.alignment = PP_ALIGN.CENTER
    _add_footer(slide, 13, dark=True)

    _add_native_speaker_notes(prs)
    SLIDES_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(SLIDES_PPTX)


def validate_outputs() -> None:
    if REPORT_PDF.stat().st_size < 10_000:
        raise RuntimeError("Generated PDF is unexpectedly small.")
    if not REPORT_PDF.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError("Generated report does not have a PDF signature.")
    if SLIDES_PPTX.stat().st_size < 10_000:
        raise RuntimeError("Generated PPTX is unexpectedly small.")
    if not zipfile.is_zipfile(SLIDES_PPTX):
        raise RuntimeError("Generated PPTX is not a valid Office ZIP package.")
    with zipfile.ZipFile(SLIDES_PPTX) as archive:
        slide_files = [
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        media_files = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        notes_files = [
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        if len(slide_files) != 13:
            raise RuntimeError(f"Expected 13 slides, found {len(slide_files)}.")
        if len(media_files) < 6:
            raise RuntimeError("Expected all six screenshots in the slide package.")
        if len(notes_files) != 13:
            raise RuntimeError(
                f"Expected native notes for 13 slides, found {len(notes_files)}."
            )


def build_overleaf_package() -> None:
    """Synchronize report figures and create an upload-ready Overleaf archive."""
    images = OVERLEAF_DIR / "images"
    images.mkdir(parents=True, exist_ok=True)
    for screenshot in SCREENSHOTS.glob("*.png"):
        shutil.copy2(screenshot, images / screenshot.name)

    with zipfile.ZipFile(OVERLEAF_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OVERLEAF_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OVERLEAF_DIR))


def main() -> None:
    build_pdf()
    build_slides()
    build_overleaf_package()
    validate_outputs()
    print(f"Wrote {REPORT_PDF.relative_to(ROOT)} ({REPORT_PDF.stat().st_size:,} bytes)")
    print(f"Wrote {SLIDES_PPTX.relative_to(ROOT)} ({SLIDES_PPTX.stat().st_size:,} bytes)")
    print(f"Wrote {OVERLEAF_ZIP.relative_to(ROOT)} ({OVERLEAF_ZIP.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
