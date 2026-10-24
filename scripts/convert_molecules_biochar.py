"""Convert Molecules (pinewood biochar) short-chain PFAS adsorption data to schema.

Source: Molecules 2026, 31, 1100 (10.3390/molecules31071100)
"Pinewood Biochar as an Affordable Adsorbent for Short- and Medium-Chain PFAS Removal"

Extracts Hill-model maximum adsorption capacities (Qmax, mg/g) for five
short-/medium-chain PFAS on four biochars and one activated carbon, and writes
them to data/processed/molecules_biochar.csv using the canonical ShortPFAS-Net
schema (target = adsorption_capacity).

Run:
    python scripts/convert_molecules_biochar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "molecules_biochar.csv"

# Canonical SMILES and chain lengths (perfluorinated carbons) for the five PFAS.
# These match the existing nature_membrane.csv mapping.
PFAS_INFO = {
    "PFBA":  {"chain": 4, "smiles": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"},
    "PFBS":  {"chain": 4, "smiles": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"},
    "PFHxA": {"chain": 6, "smiles": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFHxS": {"chain": 6, "smiles": "C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(C(C(F)(F)F)(F)F)(F)F"},
    "GenX":  {"chain": 3, "smiles": "C(=O)(C(C(F)(F)F)(OC(C(C(F)(F)F)(F)F)(F)F)F)[O-]"},
}

# Hill-model Qmax (mg/g) for single-compound equilibrium tests.
# Source: main text Table 1; PFHxS on PW-C taken from text (qe, Freundlich fit).
# Adsorbent legend:
#   PW-A1 = pinewood biochar 850 C, sieved >200 um
#   PW-A2 = pinewood biochar 850 C, sieved <200 um
#   PW-B  = pinewood biochar 1000 C
#   PW-C  = CTAB-functionalized PW-A2
#   AC    = activated carbon (FILTERCARB PHA)
DATA = {
    "PFBA":  {"PW-A1": 18.14, "PW-A2": 26.01, "PW-B": 28.60, "PW-C": 23.95, "AC": 31.68},
    "PFBS":  {"PW-A1": 40.21, "PW-A2": 65.14, "PW-B": 94.74, "PW-C": 72.38, "AC": 83.13},
    "PFHxA": {"PW-A1": 13.04, "PW-A2": 15.48, "PW-B": 28.08, "PW-C": 26.66, "AC": 22.46},
    "PFHxS": {"PW-A1": 101.3, "PW-A2": 23.55, "PW-B": 38.62, "PW-C": 31.20, "AC": 55.96},
    "GenX":  {"PW-A1": 51.49, "PW-A2": 58.33, "PW-B": 72.41, "PW-C": 56.14},
}

REF = "Molecules 2026, 31, 1100 (pinewood biochar, short-chain PFAS)"


def main() -> int:
    rows = []
    for pfas, ads in DATA.items():
        info = PFAS_INFO[pfas]
        for adsorbent, qmax in ads.items():
            rows.append({
                "pfas_name": pfas,
                "smiles": info["smiles"],
                "chain_length": info["chain"],
                "is_short_chain": info["chain"] <= SHORT_CHAIN_CUTOFF,
                # Single-compound isotherms used a range of concentrations;
                # no single C0 applies, so leave initial_concentration blank.
                "initial_concentration": float("nan"),
                "ph": float("nan"),          # "near-neutral pH" reported, not quantified
                "temperature": float("nan"),  # room temperature, not quantified
                "contact_time": 1440.0,      # equilibrium reached after 24 h
                "adsorbent_dose": 0.133,     # ~20 mg adsorbent / 150 mL solution
                "adsorbent_type": "activated_carbon" if adsorbent == "AC" else "biochar",
                "adsorbent_name": adsorbent,
                "water_matrix": "ultrapure",  # deionized (MilliQ) water
                "adsorption_capacity": qmax,  # Hill Qmax (mg/g)
                "ref_ID": "molecules2026",
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
