from __future__ import annotations

import datetime
import os
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import AnchorFlowable

from models import Circuit

# ---------------------------------------------------------------------------
# Font setup — register DejaVu Sans for full Unicode support (Ω, μ, etc.)
# ---------------------------------------------------------------------------

def _register_unicode_font() -> str:
    """Register DejaVuSans if available; fall back to Helvetica."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        candidates = [
            # matplotlib ships DejaVuSans on all platforms
            os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf"),
            r"C:\Windows\Fonts\DejaVuSans.ttf",
        ]
        try:
            import matplotlib
            mpl_data = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
            candidates.insert(0, os.path.join(mpl_data, "DejaVuSans.ttf"))
        except ImportError:
            pass

        for path in candidates:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                return "DejaVuSans"
    except Exception:
        pass
    return "Helvetica"


_FONT = _register_unicode_font()

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    bold = _FONT + "-Bold" if _FONT != "Helvetica" else "Helvetica-Bold"

    def _s(name: str, **kw: Any) -> ParagraphStyle:
        kw.setdefault("fontName", _FONT)
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "title": _s("ne_title", fontSize=24, fontName=bold, spaceAfter=6, leading=28),
        "subtitle": _s("ne_subtitle", fontSize=10, textColor=colors.grey, spaceAfter=4, leading=13),
        "section": _s("ne_section", fontSize=16, fontName=bold, spaceBefore=18, spaceAfter=6, leading=20),
        "subsection": _s("ne_subsection", fontSize=12, fontName=bold, spaceBefore=10, spaceAfter=4),
        "body": _s("ne_body", fontSize=10, spaceAfter=6, leading=14),
        "italic": _s("ne_italic", fontSize=10, textColor=colors.darkslategray, italic=True, spaceAfter=6, leading=14),
        "toc": _s("ne_toc", fontSize=10, spaceAfter=2, leading=14),
        "link": _s("ne_link", fontSize=10, textColor=colors.blue, spaceAfter=4, leading=14),
        "warning": _s("ne_warning", fontSize=9, textColor=colors.darkorange, spaceAfter=4, leading=13),
        "label": _s("ne_label", fontSize=10, fontName=bold, spaceAfter=2),
    }


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

_HDR_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.steelblue),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])

_WARNING_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3cd")),
    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#856404")),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ffc107")),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])

PAGE_W, _ = A4
MARGIN = 2 * cm
USABLE_W = PAGE_W - 2 * MARGIN


def _wrap(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text or "—", style)


def _href(url: str, label: str, style: ParagraphStyle) -> Paragraph:
    safe_url = url.replace("&", "&amp;")
    safe_label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(f'<link href="{safe_url}" color="blue">{safe_label}</link>', style)


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _build_cover(
    styles: dict[str, ParagraphStyle],
    user_prompt: str,
    circuits: list[Circuit],
    count_requested: int,
    model_name: str = "",
) -> list[Any]:
    today = datetime.date.today().isoformat()
    flowables: list[Any] = [
        Spacer(1, 1 * cm),
        Paragraph("NE555 Circuit Recommendations", styles["title"]),
        Paragraph(f"Generated on {today}", styles["subtitle"]),
        Spacer(1, 0.5 * cm),
        Paragraph("<b>User requirement:</b>", styles["label"]),
        Paragraph(user_prompt, styles["body"]),
        Paragraph(
            f"<b>Circuits requested:</b> {count_requested} &nbsp;&nbsp; "
            f"<b>Found:</b> {len(circuits)}",
            styles["body"],
        ),
        Spacer(1, 0.5 * cm),
        HRFlowable(width="100%", thickness=1, color=colors.steelblue),
        Spacer(1, 0.3 * cm),
    ]

    if model_name:
        flowables.append(Paragraph(f"<b>LLM model:</b> {model_name}", styles["subtitle"]))
        flowables.append(Spacer(1, 0.3 * cm))

    flowables.append(Paragraph("<b>Contents</b>", styles["subsection"]))

    for i, circuit in enumerate(circuits):
        anchor = f"circuit_{i}"
        safe_name = circuit.name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        flowables.append(
            Paragraph(
                f'<link href="#{anchor}" color="blue">{i + 1}. {safe_name}</link>',
                styles["toc"],
            )
        )

    flowables.append(Spacer(1, 0.5 * cm))
    return flowables


# ---------------------------------------------------------------------------
# Per-circuit section
# ---------------------------------------------------------------------------

def _build_specs_table(circuit: Circuit, styles: dict[str, ParagraphStyle]) -> list[Any]:
    if not circuit.key_specs:
        return []

    header = [
        Paragraph("<b>Specification</b>", styles["body"]),
        Paragraph("<b>Value</b>", styles["body"]),
        Paragraph("<b>Relevance</b>", styles["body"]),
    ]
    rows = [header]
    for spec in circuit.key_specs:
        rows.append([
            _wrap(spec.name, styles["body"]),
            _wrap(spec.value, styles["body"]),
            _wrap(spec.relevance or "—", styles["body"]),
        ])

    col_w = [USABLE_W * 0.30, USABLE_W * 0.20, USABLE_W * 0.50]
    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(_HDR_STYLE)
    return [table, Spacer(1, 0.3 * cm)]


def _build_bom_table(circuit: Circuit, styles: dict[str, ParagraphStyle]) -> list[Any]:
    flowables: list[Any] = []

    if not circuit.bom.is_complete and circuit.bom.completeness_note:
        warning_table = Table(
            [[Paragraph(f"⚠ {circuit.bom.completeness_note}", styles["warning"])]],
            colWidths=[USABLE_W],
        )
        warning_table.setStyle(_WARNING_STYLE)
        flowables.append(warning_table)
        flowables.append(Spacer(1, 0.2 * cm))

    header = [
        Paragraph("<b>Ref</b>", styles["body"]),
        Paragraph("<b>Part Name</b>", styles["body"]),
        Paragraph("<b>Value</b>", styles["body"]),
        Paragraph("<b>Qty</b>", styles["body"]),
        Paragraph("<b>Notes</b>", styles["body"]),
    ]

    if not circuit.bom.components:
        rows = [
            header,
            [Paragraph("No component data available for this circuit.", styles["italic"]),
             "", "", "", ""],
        ]
        no_data_style = TableStyle(list(_HDR_STYLE._cmds) + [
            ("SPAN", (0, 1), (-1, 1)),
        ])
        col_w = [USABLE_W * 0.08, USABLE_W * 0.30, USABLE_W * 0.20, USABLE_W * 0.08, USABLE_W * 0.34]
        table = Table(rows, colWidths=col_w, repeatRows=1)
        table.setStyle(no_data_style)
    else:
        rows = [header]
        for comp in circuit.bom.components:
            rows.append([
                _wrap(comp.reference, styles["body"]),
                _wrap(comp.part_name, styles["body"]),
                _wrap(comp.value, styles["body"]),
                _wrap(str(comp.quantity), styles["body"]),
                _wrap(comp.notes or "—", styles["body"]),
            ])
        col_w = [USABLE_W * 0.08, USABLE_W * 0.30, USABLE_W * 0.20, USABLE_W * 0.08, USABLE_W * 0.34]
        table = Table(rows, colWidths=col_w, repeatRows=1)
        table.setStyle(_HDR_STYLE)

    flowables.append(table)
    flowables.append(Spacer(1, 0.3 * cm))
    return flowables


def _build_circuit_section(
    i: int,
    circuit: Circuit,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    anchor = f"circuit_{i}"
    safe_name = circuit.name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    flowables: list[Any] = [
        AnchorFlowable(anchor),
        Paragraph(f"Circuit {i + 1}: {safe_name}", styles["section"]),
        Paragraph(circuit.description, styles["body"]),
        Paragraph("<b>Match to Requirements</b>", styles["subsection"]),
        Paragraph(circuit.match_explanation, styles["italic"]),
    ]

    if circuit.key_specs:
        flowables.append(Paragraph("<b>Key Specifications</b>", styles["subsection"]))
        flowables.extend(_build_specs_table(circuit, styles))

    flowables.append(Paragraph("<b>Bill of Materials</b>", styles["subsection"]))
    flowables.extend(_build_bom_table(circuit, styles))

    flowables.append(Paragraph("<b>Sources</b>", styles["subsection"]))
    flowables.append(_href(circuit.source_url, circuit.source_title or circuit.source_url, styles["link"]))
    for url in circuit.additional_urls:
        flowables.append(_href(url, url, styles["link"]))

    flowables.append(Spacer(1, 0.4 * cm))
    flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    flowables.append(Spacer(1, 0.4 * cm))
    return flowables


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_pdf(
    circuits: list[Circuit],
    user_prompt: str,
    output_path: str,
    count_requested: int,
    model_name: str = "",
) -> None:
    styles = _make_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="NE555 Circuit Recommendations",
        author="NE555 Recommender",
    )

    flowables: list[Any] = []
    flowables.extend(_build_cover(styles, user_prompt, circuits, count_requested, model_name))

    for i, circuit in enumerate(circuits):
        flowables.extend(_build_circuit_section(i, circuit, styles))

    doc.build(flowables)
