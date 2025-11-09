#!/usr/bin/env python3
"""Overlay numbered markers on a PDF using coordinates exported by zathura."""

from __future__ import annotations

import argparse
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import Color, black, lightskyblue
from reportlab.pdfgen.canvas import Canvas

LOGGER = logging.getLogger(__name__)

DEFAULT_INPUT = "input.pdf"
DEFAULT_NUMBERS = "numbers.txt"
DEFAULT_OUTPUT = "marked.pdf"


@dataclass
class Marker:
    index: int
    page: int
    raw_x: float
    raw_y: float
    scale: float


@dataclass
class PageNormalization:
    scale_x: float = 1.0
    scale_y: float = 1.0


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", "-i", default=DEFAULT_INPUT, help="Path to the source PDF"
    )
    parser.add_argument(
        "--numbers",
        "-n",
        default=DEFAULT_NUMBERS,
        help="Path to the coordinates file exported by zathura",
    )
    parser.add_argument(
        "--output", "-o", default=DEFAULT_OUTPUT, help="Destination PDF path"
    )
    parser.add_argument(
        "--font-size", type=float, default=6.0, help="Font size for the marker numbers"
    )
    parser.add_argument(
        "--bubble-radius",
        type=float,
        default=6.0,
        help="Radius of the circle behind each number (in points)",
    )
    parser.add_argument(
        "--bubble-color",
        default="#a1a1ffA7",
        help="Bubble fill color in hex (defaults to reportlab.lightskyblue)",
    )
    parser.add_argument(
        "--text-color", default=None, help="Text color in hex (defaults to black)"
    )
    return parser.parse_args()


def parse_color(value: str | None, fallback: Color) -> Color:
    if not value:
        return fallback
    value = value.lstrip("#")
    if len(value) not in {6, 8}:
        LOGGER.warning("Invalid color '%s', using default", value)
        return fallback
    # Split into RGB and optional alpha
    r = int(value[0:2], 16) / 255
    g = int(value[2:4], 16) / 255
    b = int(value[4:6], 16) / 255
    a = int(value[6:8], 16) / 255 if len(value) == 8 else 1.0
    return Color(r, g, b, a)


def read_markers(path: Path) -> List[Marker]:
    markers: List[Marker] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace(",", " ").split()
            if len(parts) < 4:
                LOGGER.warning(
                    "Skipping malformed line %d: %s", line_no, raw_line.rstrip()
                )
                continue
            try:
                page = int(parts[0])
                x_val = float(parts[1])
                y_val = float(parts[2])
                scale = float(parts[3])
            except ValueError:
                LOGGER.warning(
                    "Skipping unparsable line %d: %s", line_no, raw_line.rstrip()
                )
                continue
            if page <= 0:
                LOGGER.warning(
                    "Skipping line %d with invalid page index: %s",
                    line_no,
                    raw_line.rstrip(),
                )
                continue
            markers.append(Marker(len(markers) + 1, page, x_val, y_val, scale))
    return markers


def collect_page_sizes(reader: PdfReader) -> List[Tuple[float, float]]:
    sizes: List[Tuple[float, float]] = []
    for idx, page in enumerate(reader.pages):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        sizes.append((width, height))
        LOGGER.debug("Page %d size: %sx%s", idx + 1, width, height)
    return sizes


def group_markers(markers: Iterable[Marker]) -> Dict[int, List[Marker]]:
    grouped: Dict[int, List[Marker]] = {}
    for marker in markers:
        grouped.setdefault(marker.page, []).append(marker)
    return grouped


def derive_normalizations(
    grouped: Dict[int, List[Marker]], page_sizes: Sequence[Tuple[float, float]]
) -> Dict[int, PageNormalization]:
    normalizations: Dict[int, PageNormalization] = {}
    for page, page_markers in grouped.items():
        width, height = page_sizes[page - 1]
        max_doc_x = 0.0
        max_doc_y = 0.0
        for marker in page_markers:
            if marker.scale <= 0:
                continue
            doc_x = marker.raw_x / marker.scale
            doc_y = marker.raw_y / marker.scale
            max_doc_x = max(max_doc_x, doc_x)
            max_doc_y = max(max_doc_y, doc_y)

        scale_x = max(1.0, max_doc_x / width if width > 0 else 1.0)
        scale_y = max(1.0, max_doc_y / height if height > 0 else 1.0)

        if scale_x > 1.01 or scale_y > 1.01:
            LOGGER.info(
                "Page %d: adjusting coordinates to page bounds (fx=%.3f, fy=%.3f)",
                page,
                scale_x,
                scale_y,
            )

        normalizations[page] = PageNormalization(scale_x, scale_y)

    return normalizations


def convert_to_pdf(
    marker: Marker, page_size: Tuple[float, float], normalization: PageNormalization
) -> Tuple[float, float]:
    width, height = page_size
    if marker.scale <= 0:
        raise ValueError("Scale must be positive to convert coordinates")

    doc_x = (marker.raw_x / marker.scale) / normalization.scale_x
    doc_y = (marker.raw_y / marker.scale) / normalization.scale_y

    pdf_x = clamp(doc_x, 0.0, width)
    pdf_y = clamp(height - doc_y, 0.0, height)
    return pdf_x, pdf_y


def draw_page_markers(
    canvas: Canvas,
    markers: Sequence[Marker],
    page_size: Tuple[float, float],
    normalization: PageNormalization,
    font_size: float,
    radius: float,
    bubble_color: Color,
    text_color: Color,
):
    width, height = page_size
    if radius <= 0:
        radius = font_size * 0.6
    for marker in markers:
        try:
            x_pt, y_pt = convert_to_pdf(marker, (width, height), normalization)
        except ValueError as exc:
            LOGGER.warning("Skipping marker %d: %s", marker.index, exc)
            continue

        # Bubble
        canvas.setFillColor(bubble_color)
        canvas.setStrokeColor(bubble_color)
        if bubble_color.alpha < 1.0:
            canvas.setFillAlpha(bubble_color.alpha)
            canvas.setStrokeAlpha(bubble_color.alpha)
        canvas.circle(x_pt, y_pt, radius, stroke=0, fill=1)

        # Number
        canvas.setFillColor(text_color)
        canvas.setFont("Helvetica-Bold", font_size)
        # Align baseline to circle centre
        text_y = y_pt - font_size * 0.35
        canvas.drawCentredString(x_pt, text_y, str(marker.index))


def build_overlay_pdf(
    target: Path,
    page_sizes: Sequence[Tuple[float, float]],
    grouped_markers: Dict[int, List[Marker]],
    normalizations: Dict[int, PageNormalization],
    font_size: float,
    radius: float,
    bubble_color: Color,
    text_color: Color,
):
    canvas = Canvas(str(target))
    total_pages = len(page_sizes)
    for page_idx in range(total_pages):
        width, height = page_sizes[page_idx]
        canvas.setPageSize((width, height))
        markers = grouped_markers.get(page_idx + 1, [])
        if markers:
            LOGGER.debug("Drawing %d markers on page %d", len(markers), page_idx + 1)
        normalization = normalizations.get(page_idx + 1, PageNormalization())
        draw_page_markers(
            canvas,
            markers,
            (width, height),
            normalization,
            font_size,
            radius,
            bubble_color,
            text_color,
        )
        canvas.showPage()
    canvas.save()


def merge_pdfs(original_path: Path, overlay_path: Path, output_path: Path):
    original_reader = PdfReader(original_path)
    overlay_reader = PdfReader(overlay_path)
    writer = PdfWriter()

    overlay_pages = len(overlay_reader.pages)
    for idx, page in enumerate(original_reader.pages):
        if idx < overlay_pages:
            page.merge_page(overlay_reader.pages[idx])
        writer.add_page(page)

    with output_path.open("wb") as handle:
        writer.write(handle)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    input_path = Path(args.input)
    numbers_path = Path(args.numbers)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input PDF '{input_path}' does not exist")
    if not numbers_path.exists():
        raise SystemExit(f"Coordinates file '{numbers_path}' does not exist")

    markers = read_markers(numbers_path)
    if not markers:
        LOGGER.warning(
            "No markers found in %s. The output will match the input.", numbers_path
        )

    reader = PdfReader(input_path)
    page_sizes = collect_page_sizes(reader)
    grouped = group_markers(markers)
    normalizations = derive_normalizations(grouped, page_sizes)

    missing_pages = sorted(p for p in grouped.keys() if p < 1 or p > len(page_sizes))
    if missing_pages:
        LOGGER.warning(
            "Markers reference pages outside the document: %s", missing_pages
        )

    bubble_color = parse_color(args.bubble_color, lightskyblue)
    text_color = parse_color(args.text_color, black)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        overlay_path = Path(tmp_file.name)

    try:
        build_overlay_pdf(
            overlay_path,
            page_sizes,
            grouped,
            normalizations,
            args.font_size,
            args.bubble_radius,
            bubble_color,
            text_color,
        )
        merge_pdfs(input_path, overlay_path, output_path)
        LOGGER.info("Saved marked PDF to %s", output_path)
    finally:
        if overlay_path.exists():
            overlay_path.unlink()


if __name__ == "__main__":
    main()
