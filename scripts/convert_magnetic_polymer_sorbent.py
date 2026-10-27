"""Convert Adv. Mater. 2026 (non-PFAS magnetic polymer sorbents) short-chain PFAS data.

Source: Adv. Mater. 2026, 38, e02427
DOI: 10.1002/adma.202502427
"Non-PFAS-Based Magnetic Polymer Sorbents for Efficient Removal of Perfluorinated
Compounds from Landfill Leachate"

Adsorbents: crosslinked non-PFAS magnetic polymer sorbents on IONPs
- PFS-R1+@IONPs (best, high quaternary ammonium ratio)
- PFS-R2+@IONPs, Sty-R+@IONPs, PFS-LP+@IONPs (controls)

Short-chain PFAS (PFS-R1+@IONPs, Figure 2b): PFBA, PFPeA, PFBS, PFHxS.
Target = removal efficiency (%) in real landfill leachate.

Removal efficiencies (Figure 2b, PFS-R1+@IONPs):
- PFBA  65.7%  (others: R2+ 42.0%, Sty 29.6%, LP 16.9%)
- PFPeA 84.1%
- PFBS  98.8%
- PFHxS 99.7%

Conditions: each PFAS initial concentration 44–118 ppb, treatment 25 h,
pH 8.24 (leachate), room temperature. Dose not reported numerically (mg/L).

Writes data/processed/magnetic_polymer_sorbent.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "magnetic_polymer_sorbent.csv"

SMILES = {
    "PFBA":   "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                         # C4
    "PFPeA":  "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]",                  # C5
    "PFBS":   "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",              # C4
    "PFHxS":  "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(F)(F)F)(F)F",  # C6
}
CHAIN = {"PFBA": 4, "PFPeA": 5, "PFBS": 4, "PFHxS": 6}

# PFS-R1+@IONPs removal efficiencies (%), Figure 2b (real leachate)
REMOVAL = [
    ("PFBA", 65.7),
    ("PFPeA", 84.1),
    ("PFBS", 98.8),
    ("PFHxS", 99.7),
]

REF = "Adv. Mater. 2026, 38, e02427 (non-PFAS magnetic polymer sorbent, leachate). DOI: 10.1002/adma.202502427"
REF_ID = "advmater2026_magpoly"


def _row(pfas, removal) -> dict:
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 0.08,   # 44–118 ppb midpoint ~0.08 mg/L
        "ph": 8.24,                      # landfill leachate pH
        "temperature": float("nan"),     # room temp, not reported
        "contact_time": 1500.0,          # 25 h
        "adsorbent_dose": float("nan"),  # not reported numerically
        "adsorbent_type": "ion_exchange_resin",
        "adsorbent_name": "PFS-R1+@IONPs (non-PFAS magnetic polymer sorbent)",
        "water_matrix": "wastewater",
        "adsorption_capacity": float("nan"),
        "removal_efficiency": removal,
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": f"removal {removal}% in landfill leachate, 25 h, pH 8.24 (Fig. 2b)",
    }


def main() -> int:
    rows = [_row(pfas, r) for pfas, r in REMOVAL]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"去除率范围: {df['removal_efficiency'].min():.1f}~{df['removal_efficiency'].max():.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
