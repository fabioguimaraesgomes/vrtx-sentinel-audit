from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4
L, R, T, B = 50, 50, 56, 52
WIDTH = PAGE_W - L - R


def wrap(text: str, font: str, size: int, width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for w in words[1:]:
        cand = f"{cur} {w}"
        if pdfmetrics.stringWidth(cand, font, size) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def parse(md: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            rows.append(("code", line))
            continue
        if not line.strip():
            rows.append(("space", ""))
            continue
        if line.startswith("# "):
            rows.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            rows.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            rows.append(("h3", line[4:].strip()))
        elif line.startswith("- "):
            rows.append(("bullet", line[2:].strip()))
        else:
            rows.append(("p", line.replace("**", "").strip()))
    return rows


def footer(c: canvas.Canvas, p: int) -> None:
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - R, 24, f"Pagina {p}")


def render(md_path: Path, pdf_path: Path) -> None:
    rows = parse(md_path.read_text(encoding="utf-8"))
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    y = PAGE_H - T
    page = 1

    c.setFont("Helvetica", 9)
    c.drawString(L, y, f"Generado: {date.today().isoformat()}")
    y -= 24

    for kind, text in rows:
        if kind == "space":
            y -= 6
            continue
        if kind == "h1":
            lines = wrap(text, "Helvetica-Bold", 20, WIDTH)
            h = len(lines) * 22 + 8
            if y - h < B:
                footer(c, page)
                c.showPage()
                page += 1
                y = PAGE_H - T
            c.setFont("Helvetica-Bold", 20)
            for ln in lines:
                c.drawString(L, y, ln)
                y -= 22
            y -= 4
            continue
        if kind == "h2":
            lines = wrap(text, "Helvetica-Bold", 14, WIDTH)
            h = len(lines) * 17 + 5
            if y - h < B:
                footer(c, page)
                c.showPage()
                page += 1
                y = PAGE_H - T
            c.setFont("Helvetica-Bold", 14)
            for ln in lines:
                c.drawString(L, y, ln)
                y -= 17
            y -= 3
            continue
        if kind == "h3":
            lines = wrap(text, "Helvetica-Bold", 12, WIDTH)
            h = len(lines) * 15 + 4
            if y - h < B:
                footer(c, page)
                c.showPage()
                page += 1
                y = PAGE_H - T
            c.setFont("Helvetica-Bold", 12)
            for ln in lines:
                c.drawString(L, y, ln)
                y -= 15
            y -= 2
            continue
        if kind == "bullet":
            lines = wrap(text, "Helvetica", 10, WIDTH - 14)
            h = len(lines) * 13 + 3
            if y - h < B:
                footer(c, page)
                c.showPage()
                page += 1
                y = PAGE_H - T
            c.setFont("Helvetica", 10)
            c.drawString(L, y, "•")
            c.drawString(L + 10, y, lines[0])
            y -= 13
            for ln in lines[1:]:
                c.drawString(L + 10, y, ln)
                y -= 13
            y -= 2
            continue
        if kind == "code":
            if y - 12 < B:
                footer(c, page)
                c.showPage()
                page += 1
                y = PAGE_H - T
            c.setFont("Courier", 9)
            c.drawString(L, y, text[:120])
            y -= 11
            continue

        lines = wrap(text, "Helvetica", 10, WIDTH)
        h = len(lines) * 13 + 2
        if y - h < B:
            footer(c, page)
            c.showPage()
            page += 1
            y = PAGE_H - T
        c.setFont("Helvetica", 10)
        for ln in lines:
            c.drawString(L, y, ln)
            y -= 13
        y -= 2

    footer(c, page)
    c.save()


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera PDF desde markdown de accesos")
    parser.add_argument("--input", dest="input_path", default="accesos_operativos_vrtx_v1.md")
    parser.add_argument("--output", dest="output_path", default="accesos_operativos_vrtx_v1.pdf")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    md = (root / args.input_path).resolve()
    out = (root / args.output_path).resolve()
    render(md, out)
    print(f"PDF generado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
