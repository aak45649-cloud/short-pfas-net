"""Convert Fibers 2025 (fib13040042) PANI nanofiber GenX adsorption data to schema.

Source: Fibers 2025, 13, 42 (10.3390/fib13040042)
"Polyaniline-Coated Electrospun Polyacrylonitrile Nanofibers for Effective
Short-Chain PFAS (GenX) Removal from Water"

Extracts GenX (HFPO-DA, short-chain, C3) adsorption data on the PANI-coated
electrospun polyacrylonitrile nanofiber adsorbent (PANI-ESPAN) and writes them
to data/processed/polyaniline_nanofiber_genx.csv
(target = adsorption_capacity, with removal_efficiency where reported).

Key reported values:
  - Max capacity: ~146 mg/g at pH 6 (0.06 g in 50 mL of 520 ppm GenX, 12 h)
  - Removal: 98% at pH 6, 78% at pH 3 (100 mL of 100 ppb GenX, 0.6 g/L, 12 h)

Run:
    python scripts/convert_polyaniline_nanofiber.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "polyaniline_nanofiber_genx.csv"

# GenX (HFPO-DA) canonical SMILES, matching nature_membrane.csv / molecules_biochar.csv
GENX_SMILES = "C(=O)(C(C(F)(F)F)(OC(C(C(F)(F)F)(F)F)(F)F)F)[O-]"
GENX_CHAIN = 3  # perfluorinated carbons (short-chain)

REF = "Fibers 2025, 13, 42 (PANI-ESPAN nanofiber, GenX)"


def main() -> int:
    rows = [
        # Maximum adsorption capacity (single point, 520 ppm)
        {
            "pfas_name": "GenX",
            "smiles": GENX_SMILES,
            "chain_length": GENX_CHAIN,
            "is_short_chain": GENX_CHAIN <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 520.0,   # 520 ppm = 520 mg/L
            "ph": 6.0,
            "temperature": float("nan"),
            "contact_time": 720.0,            # 12 h
            "adsorbent_dose": 1.2,            # 0.06 g / 50 mL = 1.2 g/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": "PANI-ESPAN",
            "water_matrix": "ultrapure",
            "adsorption_capacity": 146.0,     # ~146 mg/g at pH 6
            "ref_ID": "fibers2025",
            "ref": REF,
        },
        # Removal efficiency at pH 6 (100 ppb)
        {
            "pfas_name": "GenX",
            "smiles": GENX_SMILES,
            "chain_length": GENX_CHAIN,
            "is_short_chain": GENX_CHAIN <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.1,     # 100 ppb = 0.1 mg/L
            "ph": 6.0,
            "temperature": float("nan"),
            "contact_time": 720.0,
            "adsorbent_dose": 0.6,            # 0.6 g/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": "PANI-ESPAN",
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": 98.0,
            "ref_ID": "fibers2025",
            "ref": REF,
        },
        # Removal efficiency at pH 3 (100 ppb)
        {
            "pfas_name": "GenX",
            "smiles": GENX_SMILES,
            "chain_length": GENX_CHAIN,
            "is_short_chain": GENX_CHAIN <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.1,
            "ph": 3.0,
            "temperature": float("nan"),
            "contact_time": 720.0,
            "adsorbent_dose": 0.6,
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": "PANI-ESPAN",
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": 78.0,
            "ref_ID": "fibers2025",
            "ref": REF,
        },
    ]

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {df['is_short_chain'].sum()} / {len(df)}")
    print(f"吸附剂类型: {df['adsorbent_type'].value_counts().to_dict()}")
    cap = df[df['adsorption_capacity'].notna()]
    print(f"含吸附容量样本: {len(cap)}（范围 {cap['adsorption_capacity'].min():.0f}~{cap['adsorption_capacity'].max():.0f} mg/g）")
    rem = df[df['removal_efficiency'].notna()] if 'removal_efficiency' in df else pd.DataFrame()
    if len(rem):
        print(f"含去除率样本: {len(rem)}（{rem['removal_efficiency'].tolist()}%）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
