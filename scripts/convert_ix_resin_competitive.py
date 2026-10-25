"""Convert Water 2026 (w18151869) ion-exchange resin competitive adsorption data.

Source: Water 2026, 18, 1869 (10.3390/w18151869)
"Competitive Removal of Per- and Poly-Fluoroalkyl Substances (PFAS) in
Multi-PFAS Component Systems by Ion Exchange Resins: Effects of Resin Matrix,
PFAS Property, and Sulfate"

Extracts the Langmuir maximum uptake capacity qm (ng/g) for 10 PFAS on the
polystyrene anion-exchange resin IRA900 (Table 1), and writes them to
data/processed/ix_resin_competitive.csv (target = adsorption_capacity).

Conditions (batch tests): 50 mL multicomponent solution, 0.01 g IRA900 resin,
initial pH 6.8-7.2, room temperature. The initial concentration of each PFAS
was non-uniform (see Table 1, Co in ng/L). qm converted from ng/g to mg/g.

Run:
    python scripts/convert_ix_resin_competitive.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "ix_resin_competitive.csv"

# Canonical SMILES and chain lengths (perfluorinated carbons), matching the
# existing nature_membrane.csv mapping.
PFAS_INFO = {
    "PFBA":   {"chain": 4, "smiles": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"},
    "PFPeA":  {"chain": 5, "smiles": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFHxA":  {"chain": 6, "smiles": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFHpA":  {"chain": 7, "smiles": "C(=O)(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFOA":   {"chain": 8, "smiles": "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"},
    "PFBS":   {"chain": 4, "smiles": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"},
    "PFPeS":  {"chain": 5, "smiles": "C(C(C(F)(F)F)(F)F)(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F"},
    "PFHxS":  {"chain": 6, "smiles": "C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(C(C(F)(F)F)(F)F)(F)F"},
    "PFHpS":  {"chain": 7, "smiles": "C(C(C(C(F)(F)F)(F)F)(F)F)(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F"},
    "PFOS":   {"chain": 8, "smiles": "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(C(C(F)(F)F)(F)F)(F)F)(F)F"},
}

# Table 1: Langmuir qm (ng/g) and initial concentration Co (ng/L) on IRA900.
# These are the maximum uptake capacities in the multicomponent system.
IRA900_QM_NG_G = {
    "PFBA":  1664.0,
    "PFPeA": 2274.0,
    "PFHxA": 2147.0,
    "PFHpA": 3065.0,
    "PFOA":  3137.0,
    "PFBS":  6168.0,
    "PFPeS": 3091.0,
    "PFHxS": 4425.0,
    "PFHpS": 2681.0,
    "PFOS":  6132.0,
}

# Table 1: initial concentration Co (ng/L)
CO_NG_L = {
    "PFBA":  544.0,
    "PFPeA": 567.0,
    "PFHxA": 411.0,
    "PFHpA": 506.0,
    "PFOA":  470.0,
    "PFBS":  780.0,
    "PFPeS": 400.0,
    "PFHxS": 528.0,
    "PFHpS": 392.0,
    "PFOS":  817.0,
}

REF = "Water 2026, 18, 1869 (IRA900 IX resin, multicomponent PFAS)"


def main() -> int:
    rows = []
    for pfas, qm_ngg in IRA900_QM_NG_G.items():
        info = PFAS_INFO[pfas]
        rows.append({
            "pfas_name": pfas,
            "smiles": info["smiles"],
            "chain_length": info["chain"],
            "is_short_chain": info["chain"] <= SHORT_CHAIN_CUTOFF,
            # Co in ng/L -> mg/L
            "initial_concentration": round(CO_NG_L[pfas] / 1e6, 9),
            "ph": 7.0,                  # initial pH 6.8-7.2
            "temperature": float("nan"),  # room temperature
            "contact_time": float("nan"),  # isotherm equilibrium (not stated)
            "adsorbent_dose": 0.2,      # 0.01 g / 50 mL = 0.2 g/L
            "adsorbent_type": "ion_exchange_resin",
            "adsorbent_name": "IRA900",
            "water_matrix": "ultrapure",  # DI water
            "adsorption_capacity": round(qm_ngg / 1e6, 6),  # ng/g -> mg/g
            "ref_ID": "water2026_ix",
            "ref": REF,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    sc = df["is_short_chain"]
    print(f"短链样本: {sc.sum()} / {len(df)}")
    print(f"吸附剂类型: {df['adsorbent_type'].value_counts().to_dict()}")
    print(f"吸附容量范围: {df['adsorption_capacity'].min():.4f} ~ {df['adsorption_capacity'].max():.4f} mg/g")
    print(f"PFAS 种类: {df['pfas_name'].nunique()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
