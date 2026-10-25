"""Convert Nature Comms (s41467-024-52690-y) fluoropolymer sorbent data to schema.

Source: Nature Communications 2024, 15, 8269 (10.1038/s41467-024-52690-y)
"Fluoropolymer sorbent for efficient and selective capturing of PFAS"

Extracts single-point equilibrium sorption capacities (qe, mg/g) for six PFAS on
the PFPE-IEX+ (perfluoropolyether-containing anion-exchange resin) sorbent, from
Supplementary Fig. 9 / Fig. 2e, and writes them to
data/processed/fluoropolymer_sorbent.csv using the canonical ShortPFAS-Net schema
(target = adsorption_capacity).

Conditions (Supplementary Fig. 9):
  - sorbent dose = 0.2 mg/mL (0.2 g/L)
  - PFAS concentration = 0.4 mg/mL each (400 mg/L), Milli-Q water
  - sorption duration = 24 h
  - capacity = removal% * C0 / dose

Run:
    python scripts/convert_fluoropolymer_sorbent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "fluoropolymer_sorbent.csv"

# Canonical SMILES and chain lengths (perfluorinated carbons), matching
# nature_membrane.csv mapping for consistency.
PFAS_INFO = {
    "PFBA":  {"chain": 4, "smiles": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"},
    "PFPeA": {"chain": 5, "smiles": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFHxA": {"chain": 6, "smiles": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFHpA": {"chain": 7, "smiles": "C(=O)(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFOA":  {"chain": 8, "smiles": "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFBS":  {"chain": 4, "smiles": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"},
}

# Single-point equilibrium sorption capacity qe (mg/g) on PFPE-IEX+ (SI Fig 9).
CAPACITY = {
    "PFBA": 524.1,
    "PFPeA": 700.1,
    "PFHxA": 844.3,
    "PFHpA": 967.8,
    "PFOA": 1178.5,
    "PFBS": 928.6,
}

REF = "Nat Commun 2024, 15, 8269 (fluoropolymer PFPE-IEX+ sorbent)"


def main() -> int:
    rows = []
    for pfas, qe in CAPACITY.items():
        info = PFAS_INFO[pfas]
        rows.append({
            "pfas_name": pfas,
            "smiles": info["smiles"],
            "chain_length": info["chain"],
            "is_short_chain": info["chain"] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 400.0,   # 0.4 mg/mL = 400 mg/L (SI Fig 9)
            "ph": float("nan"),               # not quantified
            "temperature": float("nan"),      # room temperature, not quantified
            "contact_time": 1440.0,           # 24 h
            "adsorbent_dose": 0.2,            # 0.2 mg/mL = 0.2 g/L
            "adsorbent_type": "ion_exchange_resin",
            "adsorbent_name": "PFPE-IEX+",
            "water_matrix": "ultrapure",      # Milli-Q water
            "adsorption_capacity": qe,        # single-point qe (mg/g)
            "ref_ID": "natcommun2024_sorbent",
            "ref": REF,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    sc = df["is_short_chain"]
    print(f"短链样本: {sc.sum()} / {len(df)}")
    print(f"吸附剂类型: {df['adsorbent_type'].value_counts().to_dict()}")
    print(f"吸附容量范围: {df['adsorption_capacity'].min():.1f} ~ {df['adsorption_capacity'].max():.1f} mg/g")
    print(f"PFAS 种类: {df['pfas_name'].nunique()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
