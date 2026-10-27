"""Batch-scan the local short-chain PFAS PDF library for extractable data.

Purpose: instead of manually reading 600+ PDFs one by one, this script
extracts full text from every PDF once (cached to disk), then scores each
paper for "extractable short-chain adsorption data" so the human/agent only
needs to closely read the high-scoring candidates.

Signals scored:
  - short-chain PFAS names (PFBA/PFBS/PFHxA/PFHxS/PFPeA/PFPeS/GenX/PFPrA/...)
  - capacity units (mg/g, mg g-1, mmol/g)
  - removal-efficiency language (removal, % efficiency)
  - isotherm/kinetics keywords (Langmuir, Freundlich, qmax, qe, isotherm)

Outputs:
  - <lib>/_全文文本/<stem>.txt      (cleaned full text, cached)
  - <lib>/_扫描结果.csv             (scored candidate ranking)

Run:
  python scripts/batch_scan_library.py --lib "/Users/yzl/Desktop/机器学习PFAS/文献整理/近5年短链PFAS全文库_20261026"
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import pandas as pd

SHORT_CHAIN_NAMES = [
    "PFBA", "PFBS", "PFHxA", "PFHxS", "PFPeA", "PFPeS", "PFHpA", "PFHpS",
    "GenX", "HFPO-DA", "HFPO", "PFPrA", "PFPrS", "PFMOPrA", "4:2FTS",
    "6:2FTS", "6:2FTCA", "perfluorobutanoic", "perfluorobutanesulfonic",
    "perfluoropentanoic", "perfluoropentanesulfonic", "perfluorohexanoic",
    "perfluorohexanesulfonic", "perfluoropropionic",
]
CAPACITY_UNITS = [r"mg\s*g\s*-1", r"mg\s*/\s*g", r"mmol\s*g\s*-1", r"mmol\s*/\s*g",
                  r"mg\s*g−1", r"mmol\s*g−1", r"µmol\s*/g", r"umol\s*/g"]
REMOVAL_WORDS = [r"removal\s+efficien", r"removal\s+rate", r"removal\s+percent",
                 r"adsorption\s+efficien", r"%\s*removal"]
ISOTHERM_WORDS = [r"langmuir", r"freundlich", r"qmax", r"q\s*max", r"\bqe\b",
                  r"adsorption\s+capacity", r"isotherm", r"sorption\s+capacity",
                  r"maximum\s+(uptake|capacity|adsorption)"]


def clean(text: str) -> str:
    return "".join(ch if (ch.isprintable() or ch in "\n\t") else " " for ch in text)


def extract(pdf_path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        parts.append(t)
    return clean("\n".join(parts))


def score(text: str) -> dict:
    low = text.lower()
    found_pfas = sorted({n for n in SHORT_CHAIN_NAMES if n.lower() in low})
    n_cap = sum(len(re.findall(p, low)) for p in CAPACITY_UNITS)
    n_rem = sum(len(re.findall(p, low)) for p in REMOVAL_WORDS)
    n_iso = sum(len(re.findall(p, low)) for p in ISOTHERM_WORDS)
    n_nums = len(re.findall(r"\d+\.?\d*", text))
    n_tokens = max(len(low.split()), 1)
    num_density = n_nums / n_tokens

    s = 0.0
    s += 3.0 * len(found_pfas)                      # short-chain PFAS coverage
    s += 6.0 * min(n_cap, 20)                       # capacity units are the strongest signal
    s += 2.0 * min(n_rem, 20)
    s += 3.0 * min(n_iso, 20)
    s += 10.0 * min(num_density, 0.05) / 0.05       # numeric density (0-10)

    return {
        "pfas_hits": len(found_pfas),
        "pfas_names": ",".join(found_pfas),
        "n_capacity_units": n_cap,
        "n_removal_words": n_rem,
        "n_isotherm_words": n_iso,
        "numeric_density": round(num_density, 4),
        "score": round(s, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True, help="文献库根目录")
    args = ap.parse_args()

    lib = Path(args.lib)
    pdf_dir = lib / "PDF全文"
    text_dir = lib / "_全文文本"
    text_dir.mkdir(exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    print(f"扫描 {len(pdfs)} 篇 PDF ...", flush=True)

    rows = []
    t0 = time.time()
    for i, pdf in enumerate(pdfs, 1):
        txt_path = text_dir / (pdf.stem + ".txt")
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8")
        else:
            try:
                text = extract(pdf)
            except Exception as e:
                text = ""
                print(f"  [warn] {pdf.name}: {e}", flush=True)
            txt_path.write_text(text, encoding="utf-8")
        sc = score(text)
        sc["file"] = pdf.name
        sc["number"] = pdf.stem.split("_")[0]
        sc["chars"] = len(text)
        rows.append(sc)
        if i % 50 == 0 or i == len(pdfs):
            print(f"  {i}/{len(pdfs)} ({(time.time()-t0):.0f}s) ...", flush=True)

    df = pd.DataFrame(rows)
    df = df.sort_values("score", ascending=False)
    out_csv = lib / "_扫描结果.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print(f"\n完成，共 {len(df)} 篇。结果已写入 {out_csv}")
    print(f"含容量单位(mg/g等)的论文: {(df['n_capacity_units'] > 0).sum()} 篇")
    print(f"含短链PFAS名称的论文: {(df['pfas_hits'] > 0).sum()} 篇")
    print(f"\n=== Top 30 候选（按可提取潜力排序）===")
    top = df.head(30)
    for _, r in top.iterrows():
        print(f"  {r['score']:6.1f} | {r['file'][:60]:60s} | PFAS={r['pfas_hits']} "
              f"mg/g={r['n_capacity_units']} 去除率={r['n_removal_words']} 等温={r['n_isotherm_words']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
