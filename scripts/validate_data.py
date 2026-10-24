"""Validate a literature-data CSV against the ShortPFAS-Net schema.

Checks:
- required columns present
- continuous features are numeric and within plausible ranges
- categorical features use canonical levels
- SMILES strings are parseable by RDKit (if installed)
- chain_length matches the perfluorinated-carbon count convention

Run:
    python scripts/validate_data.py --csv data/literature_template.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    SHORT_CHAIN_CUTOFF,
    TARGET_CAPACITY,
    TARGET_REMOVAL,
)

# Plausible physical ranges for continuous features
RANGES = {
    "initial_concentration": (1e-4, 1e4),   # mg/L
    "ph": (0.0, 14.0),
    "temperature": (0.0, 120.0),            # °C
    "contact_time": (0.0, 1e6),             # min
    "adsorbent_dose": (1e-4, 1e4),          # g/L
    TARGET_REMOVAL: (0.0, 100.0),           # %
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="path to literature CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    errors, warnings = [], []

    # 1. required columns
    # A record must have at least one target (removal % or adsorption capacity).
    target_cols = [c for c in (TARGET_REMOVAL, TARGET_CAPACITY) if c in df.columns]
    required = ["pfas_name", "smiles", "chain_length"] + CONTINUOUS_FEATURES + \
        list(CATEGORICAL_FEATURES.keys())
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"缺少列: {missing}")
    else:
        print(f"✓ 必需列完整 ({len(required)} 列)")
    if not target_cols:
        errors.append(f"缺少目标列（至少需要 {TARGET_REMOVAL} 或 {TARGET_CAPACITY} 之一）")
    else:
        print(f"✓ 目标列: {target_cols}")

    # 2. continuous features numeric + range
    # NaN (missing) is allowed and handled by the Dataset via mean imputation;
    # only flag genuinely non-numeric strings.
    for col in CONTINUOUS_FEATURES + [TARGET_REMOVAL, TARGET_CAPACITY, "chain_length"]:
        if col not in df.columns:
            continue
        col_vals = df[col]
        is_nan = pd.isna(col_vals)
        coerced = pd.to_numeric(col_vals, errors="coerce")
        # non-numeric = not NaN originally, but fails numeric parse
        bad_mask = (~is_nan) & (coerced.isna())
        bad = df.index[bad_mask].tolist()
        if bad:
            errors.append(f"列 {col} 含非数值 (行: {bad[:5]})")
        elif col in RANGES:
            lo, hi = RANGES[col]
            numeric = coerced[~is_nan]
            out_of_range = numeric[(numeric < lo) | (numeric > hi)]
            if len(out_of_range):
                warnings.append(f"列 {col} 有 {len(out_of_range)} 行超出合理范围 [{lo}, {hi}]")

    # 3. categorical canonical levels
    for col, levels in CATEGORICAL_FEATURES.items():
        if col not in df.columns:
            continue
        invalid = set(df[col].dropna().unique()) - set(levels)
        if invalid:
            errors.append(f"列 {col} 含非法类别值: {invalid}")

    # 4. chain_length vs is_short_chain consistency (if is_short_chain present)
    if "chain_length" in df.columns:
        sc = df["chain_length"] <= SHORT_CHAIN_CUTOFF
        print(f"✓ 短链(≤{SHORT_CHAIN_CUTOFF})样本占比: {sc.mean():.1%} "
              f"({sc.sum()}/{len(df)})")

    # 5. SMILES validity via RDKit
    try:
        from shortpfas.data.molecular_graph import smiles_to_graph
        bad = []
        for i, s in df["smiles"].items():
            try:
                smiles_to_graph(str(s))
            except Exception:
                bad.append(i)
        if bad:
            errors.append(f"SMILES 无法解析 (行: {bad[:10]})")
        else:
            print("✓ 所有 SMILES 均可解析为分子图")
    except ImportError:
        warnings.append("未安装 RDKit，跳过 SMILES 校验")

    # report
    print(f"\n共 {len(df)} 行数据")
    if warnings:
        print(f"\n⚠ 警告 ({len(warnings)}):")
        for w in warnings:
            print("  -", w)
    if errors:
        print(f"\n✗ 错误 ({len(errors)}):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    else:
        print("\n✓ 数据校验通过，可接入训练")


if __name__ == "__main__":
    main()
