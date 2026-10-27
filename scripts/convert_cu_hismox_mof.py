"""Convert Small 2025 (Cu-hismox MOF) short-chain PFAS capture data.

Source: Small 2025, 21, e10000 — DOI: 10.1002/smll.2024xxxx
"Efficient Capture of Short- and Long-Chain PFAS from Water by a
Metal-Organic Framework"

Adsorbent: MOF 1 = Cu(II)2(S,S)-hismox (a chiral Cu-MOF, water-stable).

Two data blocks (both short-chain PFAS only, <= C6):

(A) Removal efficiency (%) — Table 1, SPE cartridge (25 mg MOF / 5 mL,
    10 ug/L each PFAS, pH 7.0, contact <30 s), vs powdered activated
    carbon (PAC) control:
      PFBA 70.0, PFBS 86.0, PFPeS 99.7, PFHxA 78.2, PFHxS 100

(B) Maximum uptake capacity (mg/g) — Section 2.5, 50 mg polycrystalline
    MOF soaked in saturated aqueous solution, 2 weeks, elemental analysis:
      PFBS 1221.2, PFPeS 1397.0
    (PFHpS 1108 and PFOS 1054.8 are long-chain C7/C8, excluded here.)

Writes data/processed/cu_hismox_mof.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "cu_hismox_mof.csv"

SMILES = {
    "PFBA":  "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                              # C4
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",                  # C4
    "PFPeS": "C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(C(F)(F)F)(F)F",          # C5
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",               # C6
    "PFHxS": "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(F)(F)F)(F)F",   # C6
}
CHAIN = {"PFBA": 4, "PFBS": 4, "PFPeS": 5, "PFHxA": 6, "PFHxS": 6}

# (A) removal efficiency at 10 ug/L, SPE cartridge
REMOVAL = {"PFBA": 70.0, "PFBS": 86.0, "PFPeS": 99.7, "PFHxA": 78.2, "PFHxS": 100.0}

# (B) maximum uptake capacity (saturated solution, 2 weeks)
CAPACITY = {"PFBS": 1221.2, "PFPeS": 1397.0}

REF = "Small 2025, 21, e10000 (Cu-hismox MOF; SPE removal + saturation capacity)"
REF_ID = "small2025_cuhismox"


def main() -> int:
    rows = []

    # (A) removal-efficiency records
    for pfas, removal in REMOVAL.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.01,     # 10 ug/L = 0.01 mg/L
            "ph": 7.0,
            "temperature": 25.0,               # room temperature
            "contact_time": 0.5,               # <30 s SPE percolation
            "adsorbent_dose": 5.0,             # 25 mg / 5 mL
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": "MOF-1 Cu(II)2(S,S)-hismox",
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
        })

    # (B) maximum-uptake-capacity records
    for pfas, qe in CAPACITY.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": float("nan"),  # saturated solution
            "ph": 7.0,
            "temperature": 25.0,
            "contact_time": 20160.0,           # 2 weeks
            "adsorbent_dose": float("nan"),    # 50 mg, volume not specified
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": "MOF-1 Cu(II)2(S,S)-hismox",
            "water_matrix": "ultrapure",
            "adsorption_capacity": qe,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    print(f"含去除率: {df['removal_efficiency'].notna().sum()} 条")
    print(f"含容量: {df['adsorption_capacity'].notna().sum()} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
