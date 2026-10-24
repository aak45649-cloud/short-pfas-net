"""Extract text from downloaded PDFs for data-mining literature tables.

Run:
    python scripts/extract_pdf_text.py                     # extract all papers
    python scripts/extract_pdf_text.py --paper <name>      # extract one paper
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PAPERS_DIR = Path(__file__).resolve().parent.parent / "data" / "papers"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "papers" / "_text"


def extract_pdf(pdf_path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    parts = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        parts.append(f"\n----- PAGE {i + 1} -----\n{text}")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", default=None, help="PDF filename (optional)")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.paper:
        pdfs = [PAPERS_DIR / args.paper]
    else:
        pdfs = sorted(PAPERS_DIR.glob("*.pdf"))

    for pdf in pdfs:
        if not pdf.exists():
            print(f"未找到: {pdf}")
            continue
        print(f"提取: {pdf.name}")
        text = extract_pdf(pdf)
        out_path = OUT_DIR / (pdf.stem + ".txt")
        out_path.write_text(text, encoding="utf-8")
        print(f"  -> {out_path.name} ({len(text)} 字符, {text.count('----- PAGE')} 页)")


if __name__ == "__main__":
    main()
