"""Lesson PDFs for teachers (TZ 8.9), built from the lesson text in the chosen language."""

import json
from functools import lru_cache
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.i18n import t

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
LOGO = Path(__file__).parent / "assets" / "brand" / "eco-master-mark.png"
# Manrope has no modifier-letter apostrophes; Uzbek o‘/g‘ variants are drawn as a plain one.
APOSTROPHES = str.maketrans({"ʻ": "'", "ʼ": "'", "‘": "'", "’": "'"})
GREEN = (4, 120, 87)
INK = (0, 33, 23)
GREY = (91, 107, 98)


class LessonPdf(FPDF):
    def __init__(self, lang: str):
        super().__init__(format="A4")
        self.lang = lang
        self.add_font("Manrope", "", FONT_DIR / "Manrope-Regular.ttf")
        self.add_font("Manrope", "B", FONT_DIR / "Manrope-Bold.ttf")
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(True, margin=18)

    def header(self) -> None:
        top = self.t_margin
        self.image(LOGO, x=self.l_margin, y=top - 1, h=8)
        self.set_xy(self.l_margin + 10, top + 0.5)
        self.set_font("Manrope", "B", 9)
        self.set_text_color(*GREEN)
        self.cell(0, 6, t("pdf_header", self.lang))
        self.set_xy(self.l_margin, top + 10)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Manrope", "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 6, f"{t('pdf_footer', self.lang)} · {self.page_no()}", align="C")

    def write_text(self, text: str, size: float = 11, bold: bool = False, color=INK) -> None:
        self.set_font("Manrope", "B" if bold else "", size)
        self.set_text_color(*color)
        # Left-aligned: justified lines leave wide gaps between words.
        self.multi_cell(0, size * 0.55, clean(text), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section(self, title: str) -> None:
        self.ln(4)
        self.write_text(title, size=13, bold=True, color=GREEN)
        self.ln(1)

    def items(self, values: list[str], numbered: bool = False) -> None:
        for i, value in enumerate(values, start=1):
            self.set_font("Manrope", "", 11)
            self.set_text_color(*INK)
            # Hanging indent: wrapped lines start under the text, not under the marker.
            self.cell(6, 11 * 0.55, f"{i}." if numbered else "•")
            self.multi_cell(
                0, 11 * 0.55, clean(value), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )
            self.ln(0.5)


def clean(text: str) -> str:
    return text.translate(APOSTROPHES)


@lru_cache(maxsize=32)
def _render(slug: str, version: str, lang: str, title: str, grade: str, body_json: str) -> bytes:
    body = json.loads(body_json)
    pdf = LessonPdf(lang)
    pdf.add_page()
    pdf.write_text(title, size=20, bold=True)
    pdf.ln(1)
    pdf.write_text(
        f"{t('pdf_grade', lang, grade=grade)} · {t('pdf_duration', lang)}", size=10, color=GREY
    )

    # .get(): admins preview drafts whose parts may still be empty.
    pdf.section(t("pdf_goal", lang))
    pdf.write_text(body.get("goal") or "")
    pdf.section(t("pdf_materials", lang))
    pdf.items(body.get("materials") or [])
    pdf.section(t("pdf_plan", lang))
    for step in body.get("plan") or []:
        pdf.write_text(f"{step['title']} — {t('pdf_minutes', lang, n=step['minutes'])}", bold=True)
        pdf.write_text(step["text"])
        pdf.ln(1.5)
    pdf.section(t("pdf_questions", lang))
    pdf.items(body.get("questions") or [], numbered=True)
    pdf.section(t("pdf_homework", lang))
    pdf.write_text(body.get("homework") or "")
    pdf.section(t("pdf_app_task", lang))
    pdf.write_text(body.get("app_task") or "")
    return bytes(pdf.output())


def lesson_pdf(slug: str, version: str, lang: str, title: str, grade: str, body: dict) -> bytes:
    """Render (and cache per lesson version and language) the lesson as an A4 PDF."""
    return _render(
        slug, version, lang, title, grade, json.dumps(body, ensure_ascii=False, sort_keys=True)
    )
