from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


@dataclass
class Element:
    kind: str  # heading, paragraph, bullet, code
    text: str
    level: int = 0


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT = 50
RIGHT = 50
TOP = 56
BOTTOM = 52
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT


def wrap_text(text: str, font: str, size: int, width: float) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def parse_markdown(md_text: str) -> List[Element]:
    elements: List[Element] = []
    in_code = False
    code_lines: List[str] = []

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip("\n")

        if line.strip().startswith("```"):
            if in_code:
                elements.append(Element("code", "\n".join(code_lines)))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            continue

        if line.startswith("### "):
            elements.append(Element("heading", line[4:].strip(), level=3))
        elif line.startswith("## "):
            elements.append(Element("heading", line[3:].strip(), level=2))
        elif line.startswith("# "):
            elements.append(Element("heading", line[2:].strip(), level=1))
        elif line.startswith("- "):
            elements.append(Element("bullet", line[2:].strip()))
        elif line[:3].isdigit() and line[1:3] == ". ":
            elements.append(Element("bullet", line[3:].strip()))
        elif len(line) > 3 and line[0].isdigit() and line[1:3] == ". ":
            elements.append(Element("bullet", line[3:].strip()))
        else:
            cleaned = line.replace("**", "")
            cleaned = cleaned.replace("  ", " ")
            elements.append(Element("paragraph", cleaned.strip()))

    return elements


def extract_metadata_and_summary(md_text: str) -> Tuple[str, str, str, str, str]:
    title = "Diagnóstico VRTX Sentinel Audit"
    version = "v1.0"
    author = "Equipo Técnico VRTX Sentinel"
    dt = str(date.today())

    summary_lines: List[str] = []
    in_summary = False
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        if line.startswith("**Versión:**"):
            version = line.split("**Versión:**", 1)[1].strip()
        if line.startswith("**Autor:**"):
            author = line.split("**Autor:**", 1)[1].strip()
        if line.startswith("**Fecha:**"):
            dt = line.split("**Fecha:**", 1)[1].strip()
        if line.strip() == "## Resumen ejecutivo":
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if in_summary and line.strip():
            summary_lines.append(line.replace("**", "").strip())

    summary = " ".join(summary_lines)
    return title, version, author, dt, summary


def filtered_body_elements(elements: List[Element]) -> List[Element]:
    body: List[Element] = []
    include = False
    for el in elements:
        if el.kind == "heading" and el.text.startswith("1. Objetivos"):
            include = True
        if include:
            body.append(el)
    return body


def estimate_toc_lines(body: List[Element]) -> int:
    return sum(1 for e in body if e.kind == "heading" and e.level in (1, 2, 3))


def measure_element_height(el: Element) -> float:
    if el.kind == "heading":
        if el.level == 1:
            size = 18
            lines = wrap_text(el.text, "Helvetica-Bold", size, CONTENT_WIDTH)
            return len(lines) * 24 + 10
        if el.level == 2:
            size = 14
            lines = wrap_text(el.text, "Helvetica-Bold", size, CONTENT_WIDTH)
            return len(lines) * 19 + 6
        size = 12
        lines = wrap_text(el.text, "Helvetica-Bold", size, CONTENT_WIDTH)
        return len(lines) * 16 + 5
    if el.kind == "bullet":
        lines = wrap_text(el.text, "Helvetica", 10, CONTENT_WIDTH - 14)
        return len(lines) * 13 + 4
    if el.kind == "code":
        lines = el.text.splitlines() or [""]
        return len(lines) * 11 + 10
    lines = wrap_text(el.text, "Helvetica", 10, CONTENT_WIDTH)
    return len(lines) * 13 + 5


def simulate_heading_pages(body: List[Element], start_page: int) -> List[Tuple[str, int, int]]:
    y = PAGE_HEIGHT - TOP
    page = start_page
    toc: List[Tuple[str, int, int]] = []

    for el in body:
        block_h = measure_element_height(el)
        if y - block_h < BOTTOM:
            page += 1
            y = PAGE_HEIGHT - TOP
        if el.kind == "heading" and el.level in (1, 2, 3):
            toc.append((el.text, el.level, page))
        y -= block_h

    return toc


def draw_footer(c: canvas.Canvas, page_number: int) -> None:
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_WIDTH - RIGHT, 24, f"Página {page_number}")


def draw_cover(c: canvas.Canvas, title: str, version: str, author: str, dt: str, summary: str) -> None:
    y = PAGE_HEIGHT - 120
    c.setFont("Helvetica-Bold", 26)
    c.drawString(LEFT, y, title)

    y -= 48
    c.setFont("Helvetica", 13)
    c.drawString(LEFT, y, f"Versión: {version}")
    y -= 22
    c.drawString(LEFT, y, f"Autor: {author}")
    y -= 22
    c.drawString(LEFT, y, f"Fecha: {dt}")

    y -= 40
    c.setFont("Helvetica-Bold", 15)
    c.drawString(LEFT, y, "Resumen ejecutivo")
    y -= 20

    c.setFont("Helvetica", 11)
    for line in wrap_text(summary, "Helvetica", 11, CONTENT_WIDTH):
        if y < BOTTOM + 24:
            break
        c.drawString(LEFT, y, line)
        y -= 15


def draw_toc(c: canvas.Canvas, toc: List[Tuple[str, int, int]]) -> None:
    y = PAGE_HEIGHT - TOP
    c.setFont("Helvetica-Bold", 20)
    c.drawString(LEFT, y, "Índice automático")
    y -= 28

    c.setFont("Helvetica", 10)
    for title, level, page in toc:
        indent = (level - 1) * 14
        label = title
        max_w = CONTENT_WIDTH - 70 - indent
        while pdfmetrics.stringWidth(label, "Helvetica", 10) > max_w and len(label) > 8:
            label = label[:-1]
        dots_count = max(4, int((CONTENT_WIDTH - indent - pdfmetrics.stringWidth(label, "Helvetica", 10) - 26) / 4.5))
        dots = "." * dots_count
        line = f"{label} {dots} {page}"
        c.drawString(LEFT + indent, y, line)
        y -= 13
        if y < BOTTOM + 20:
            c.showPage()
            draw_footer(c, 2)
            y = PAGE_HEIGHT - TOP
            c.setFont("Helvetica", 10)


def draw_body(c: canvas.Canvas, body: List[Element], start_page_number: int) -> None:
    y = PAGE_HEIGHT - TOP
    page = start_page_number

    for el in body:
        block_h = measure_element_height(el)
        if y - block_h < BOTTOM:
            draw_footer(c, page)
            c.showPage()
            page += 1
            y = PAGE_HEIGHT - TOP

        if el.kind == "heading":
            if el.level == 1:
                c.setFont("Helvetica-Bold", 18)
                lines = wrap_text(el.text, "Helvetica-Bold", 18, CONTENT_WIDTH)
                for line in lines:
                    c.drawString(LEFT, y, line)
                    y -= 24
                y -= 6
            elif el.level == 2:
                c.setFont("Helvetica-Bold", 14)
                lines = wrap_text(el.text, "Helvetica-Bold", 14, CONTENT_WIDTH)
                for line in lines:
                    c.drawString(LEFT, y, line)
                    y -= 19
                y -= 4
            else:
                c.setFont("Helvetica-Bold", 12)
                lines = wrap_text(el.text, "Helvetica-Bold", 12, CONTENT_WIDTH)
                for line in lines:
                    c.drawString(LEFT, y, line)
                    y -= 16
                y -= 2

        elif el.kind == "bullet":
            c.setFont("Helvetica", 10)
            lines = wrap_text(el.text, "Helvetica", 10, CONTENT_WIDTH - 14)
            c.drawString(LEFT, y, "•")
            c.drawString(LEFT + 10, y, lines[0])
            y -= 13
            for line in lines[1:]:
                c.drawString(LEFT + 10, y, line)
                y -= 13
            y -= 3

        elif el.kind == "code":
            c.setFont("Courier", 9)
            for line in el.text.splitlines() or [""]:
                trimmed = line[:120]
                c.drawString(LEFT, y, trimmed)
                y -= 11
            y -= 5

        else:
            c.setFont("Helvetica", 10)
            lines = wrap_text(el.text, "Helvetica", 10, CONTENT_WIDTH)
            for line in lines:
                c.drawString(LEFT, y, line)
                y -= 13
            y -= 3

    draw_footer(c, page)


def build_pdf(md_path: Path, out_pdf: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    title, version, author, dt, summary = extract_metadata_and_summary(md_text)
    elements = parse_markdown(md_text)
    body = filtered_body_elements(elements)

    toc = simulate_heading_pages(body, start_page=3)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)

    draw_cover(c, title, version, author, dt, summary)
    draw_footer(c, 1)
    c.showPage()

    draw_toc(c, toc)
    draw_footer(c, 2)
    c.showPage()

    draw_body(c, body, start_page_number=3)
    c.save()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    md_path = repo_root / "diagnostico_vrtx_sentinel_audit_v1.md"
    pdf_root = repo_root / "diagnostico_vrtx_sentinel_audit_v1.pdf"

    build_pdf(md_path, pdf_root)
    print(f"PDF generado: {pdf_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
