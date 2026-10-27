"""Convert Toxics 2026 (ZnCl2-modified banana peel biochar) short-chain PFAS data.

Source: Toxics 2026, 14, 204 — DOI: 10.3390/toxics14030204
"A Novel Graphitic Biochar Derived from Banana Peels for Efficient PFAS
Removal: Mechanistic Insight from Integrated Experiments and DFT Calculations"

Adsorbent: Zn-BBC (ZnCl2-modified banana peel biochar, one-step pyrolysis).
Classified as biochar.

Data extracted from main text (exact values only; per-PFAS isotherm
capacities are in SI Table S8, so only the explicitly reported short-chain
endpoints are kept):

(A) Fitted maximum adsorption capacity (Sips/Langmuir, pH 7-8):
      PFBA 6.07 mg/g (lower bound of the reported 6.07-9.41 range)

(B) Removal efficiency at neutral pH (3-9 plateau, 100 ug/L, 0.25 g/L):
      PFBA 94.2% (>=94.2%), PFBS 100%, PFHxA 100%, GenX 100%

(C) Removal efficiency at pH 11 (electrostatic repulsion suppresses
    short-chain adsorption): PFBA 2.77%, PFBS 58.1%, PFHxA 40.4%,
    GenX 38.2%

Conditions (Section 2.3): 40 mL ultrapure water + 10 mg Zn-BBC
(0.25 g/L), 100 ug/L each PFAS, 25 C, pH 7.0, 1440 min.

Writes data/processed/banana_peel_biochar.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "banana_peel_biochar.csv"

SMILES = {
    "PFBA":  "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                              # C4
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",                  # C4
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",               # C6
    "GenX":  "OC(=O)C(F)(C(F)(F)F)OC(F)(F)C(F)(F)C(F)(F)F",                    # C6 (HFPO-DA)
}
CHAIN = {"PFBA": 4, "PFBS": 4, "PFHxA": 6, "GenX": 6}

ADS_NAME = "Zn-BBC (ZnCl2-modified banana peel biochar)"
REF = "Toxics 2026, 14, 204 (ZnCl2 banana peel biochar). DOI: 10.3390/toxics14030204"
REF_ID = "toxics2026_bananabiochar"


def main() -> int:
    rows = []

    # (A) fitted max capacity (Sips/Langmuir, pH 7-8)
    capacity = {"PFBA": 6.07}
    for pfas, qe in capacity.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 2.0,       # upper isotherm bound (2000 ug/L)
            "ph": 7.5,                          # pH 7-8 (isotherm)
            "temperature": 25.0,
            "contact_time": 1440.0,
            "adsorbent_dose": 0.25,             # 10 mg / 40 mL
            "adsorbent_type": "biochar",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": qe,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "Sips/Langmuir fitted max capacity (lower bound of 6.07-9.41 mg/g range)",
        })

    # (B) neutral pH (3-9 plateau) removal, 100 ug/L
    removal_neutral = {"PFBA": 94.2, "PFBS": 100.0, "PFHxA": 100.0, "GenX": 100.0}
    for pfas, removal in removal_neutral.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.1,       # 100 ug/L
            "ph": 7.0,
            "temperature": 25.0,
            "contact_time": 1440.0,
            "adsorbent_dose": 0.25,
            "adsorbent_type": "biochar",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "pH 3-9 plateau; PFBA reported as >=94.2% (lower bound)",
        })

    # (C) pH 11 removal (electrostatic repulsion)
    removal_ph11 = {"PFBA": 2.77, "PFBS": 58.1, "PFHxA": 40.4, "GenX": 38.2}
    for pfas, removal in removal_ph11.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.1,
            "ph": 11.0,
            "temperature": 25.0,
            "contact_time": 1440.0,
            "adsorbent_dose": 0.25,
            "adsorbent_type": "biochar",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "pH 11 removal (short-chain suppressed by electrostatic repulsion)",
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
