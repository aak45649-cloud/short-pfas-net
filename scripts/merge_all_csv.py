"""Merge all extracted literature CSVs into a single harmonized dataset.

Reads every data/processed/*.csv (excluding literature_template.csv), aligns
columns (missing columns become NaN), and writes:

    data/processed/all_literature.csv

The merged file is the input for cross-source modeling experiments.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROC = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT = PROC / "all_literature.csv"

# Canonical column order (from schema + per-record metadata)
COLUMNS = [
    "pfas_name", "smiles", "chain_length", "is_short_chain",
    "initial_concentration", "ph", "temperature", "contact_time", "adsorbent_dose",
    "adsorbent_type", "adsorbent_name", "water_matrix",
    "removal_efficiency", "adsorption_capacity",
    "ref_ID", "ref", "source_note",
]


def main() -> int:
    frames = []
    n_sources = 0
    for f in sorted(PROC.glob("*.csv")):
        if f.name == "literature_template.csv" or f.name == "all_literature.csv":
            continue
        df = pd.read_csv(f)
        frames.append(df)
        n_sources += 1
        print(f"  {f.name:42s} {len(df):5d} rows")

    merged = pd.concat(frames, ignore_index=True, sort=False)

    # Reorder to canonical columns, keeping any extra columns at the end
    present = [c for c in COLUMNS if c in merged.columns]
    extra = [c for c in merged.columns if c not in COLUMNS]
    merged = merged[present + extra]

    merged.to_csv(OUT, index=False)

    n_short = int(merged["is_short_chain"].sum()) if "is_short_chain" in merged else 0
    n_cap = int(merged["adsorption_capacity"].notna().sum()) if "adsorption_capacity" in merged else 0
    n_rem = int(merged["removal_efficiency"].notna().sum()) if "removal_efficiency" in merged else 0

    print(f"\n合并完成: {OUT}")
    print(f"  数据源: {n_sources} 个")
    print(f"  总样本: {len(merged)}")
    print(f"  短链样本: {n_short}")
    print(f"  含去除率: {n_rem}, 含吸附容量: {n_cap}")
    print(f"  PFAS 种类: {merged['pfas_name'].nunique()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
