"""Convert npj Clean Water 2025 (beta-CD-TriPod polymer) PFAS data.

Source: npj Clean Water 2025, 8, 93 — DOI: 10.1038/s41545-025-00519-6
"Cyclodextrin polymer networks synthesis via amine-functionalized
tripodal crosslinker for ultra-rapid removal of PFAS from water"

Adsorbent: beta-CD-TriPod polymer (cyclodextrin polymer network,
amine-functionalized tripodal crosslinker). Classified as nanoadsorbent
(polymeric network adsorbent).

Data blocks (all values from main text + tables):

(A) Isotherm max capacity (Langmuir qm,cal) — Table 2, pH 2.2, dose
    200 mg/L, contact 360 min, 25 C (PFBS 1-25 mg/L, PFOS 3-40 mg/L):
      PFBS (C4, short)  246.20 mg/g   (qm,exp 245 +/- 17)
      PFOS (C8, long)   587.10 mg/g   (qm,exp 563 +/- 15)

(B) Removal efficiency in mixture of nine PFAS (Fig. 3a), 1 ug/L each,
    dose 10 mg/L. Values recorded at pH 7 (neutral, environmentally
    representative): PFBA 75.45 (from kinetics text, ~2-15 min), PFBS 86.70,
    PFHxA ~27 (reported as "27%"), PFHxS 42.40 (from pH 9 list at pH 7
    interpolation is ambiguous -> only pH-2 and pH-9 endpoints are exact).
    -> To stay strictly factual, only the pH-2 removal endpoints are kept
       where all nine are explicitly listed, plus the kinetics equilibrium
       removals (1 ug/L, pH 5, 2 min) which are clearly stated.

(C) Kinetics equilibrium removal (Fig. 4b, 1 ug/L individual, dose 10 mg/L,
    pH 5.0, within 2 min):
      PFBS 99.50% (">99.50%"), PFOS ~100%.

To avoid over-fitting the model to approximate/ambiguous numbers, only
(A) the exact Langmuir capacities and (B) the explicitly-listed pH-2
removal endpoints for the short-chain PFAS are extracted, plus the
kinetics individual PFBS/PFOS removals where clearly quantified.

Writes data/processed/beta_cd_tripod.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "beta_cd_tripod.csv"

SMILES = {
    "PFBA":  "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                              # C4
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",                   # C4
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",               # C6
    "PFHxS": "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(F)(F)F)(F)F",   # C6
    "PFOS":  "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(C(C(F)(F)F)(F)F)(F)F)(F)F",  # C8
}
CHAIN = {"PFBA": 4, "PFBS": 4, "PFHxA": 6, "PFHxS": 6, "PFOS": 8}

ADS_NAME = "beta-CD-TriPod polymer (cyclodextrin network)"
REF = "npj Clean Water 2025, 8, 93 (beta-CD-TriPod cyclodextrin polymer). DOI: 10.1038/s41545-025-00519-6"
REF_ID = "npjcleanwater2025_cdtripod"


def main() -> int:
    rows = []

    # (A) Langmuir maximum capacities (Table 2)
    capacity = {"PFBS": 246.20, "PFOS": 587.10}
    for pfas, qe in capacity.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 25.0 if pfas == "PFBS" else 40.0,  # upper isotherm bound (mg/L)
            "ph": 2.2,
            "temperature": 25.0,
            "contact_time": 360.0,          # 6 h
            "adsorbent_dose": 0.2,          # 200 mg/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": qe,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
        })

    # (B) pH-2 removal endpoints for the nine-PFAS mixture (Fig. 3a) — short-chain only
    removal_ph2 = {"PFBA": 66.50, "PFBS": 88.90, "PFHxA": 90.20, "PFHxS": 94.30}
    for pfas, removal in removal_ph2.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.001,     # 1 ug/L
            "ph": 2.0,
            "temperature": 25.0,
            "contact_time": 120.0,              # equilibrium within 2 min
            "adsorbent_dose": 0.01,             # 10 mg/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
        })

    # (C) kinetics individual removals (Fig. 4b, 1 ug/L, dose 10 mg/L, pH 5, 2 min)
    kinetics = {"PFBS": 99.50, "PFOS": 100.0}
    for pfas, removal in kinetics.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.001,     # 1 ug/L
            "ph": 5.0,
            "temperature": 25.0,
            "contact_time": 2.0,
            "adsorbent_dose": 0.01,             # 10 mg/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    print(f"含容量: {df['adsorption_capacity'].notna().sum()} 条")
    print(f"含去除率: {df['removal_efficiency'].notna().sum()} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
