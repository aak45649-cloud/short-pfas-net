"""Convert ACS Appl. Mater. Interfaces 2026 (BSA-PEI) short-chain PFAS data.

Source: ACS Appl. Mater. Interfaces 2026, 18, 5026-5037
DOI: 10.1021/acsami.5c13467
"Rapid, High-Capacity, and Reusable Bovine Serum Albumin-Based Adsorbents
for Perfluoroalkyl and Polyfluoroalkyl Substance Removal"

Adsorbent: PEI-functionalized BSA nanoclusters PB(0.75) (PEI:BSA = 0.75).
Electrostatic attraction + hydrophobic interactions.

Short-chain PFAS data (Table 1, isotherm fits):
  PFBA (C4):  Langmuir qm 9.3,  qmax_measured 0.30 mg/g
  PFBS (C4):  Langmuir qm 3.0,  qmax_measured 1.12 mg/g
  GenX (C6):  Langmuir qm 1.8,  qmax_measured 0.60 mg/g
For these short-chain PFAS only the Freundlich model fitted well
(R2 > 0.99), so the measured maximum uptake (qmax_measured) is recorded
as the capacity (more physically defensible than the poor Langmuir qm).

Conditions: isotherm, 40 mL PFAS solution, PB dosage 20 mg/L, pH 7,
room temperature, 2 h equilibrium.

Writes data/processed/bsa_pei_pfas.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "bsa_pei_pfas.csv"

SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                        # C4
    "PFBS": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",            # C4
    "GenX": "OC(=O)C(F)(C(F)(F)F)OC(F)(F)C(F)(F)C(F)(F)F",             # C6
}
CHAIN = {"PFBA": 4, "PFBS": 4, "GenX": 6}

# pfas -> (Langmuir qm, qmax_measured), both mg/g
DATA = {
    "PFBA": (9.3, 0.30),
    "PFBS": (3.0, 1.12),
    "GenX": (1.8, 0.60),
}

REF = "ACS Appl. Mater. Interfaces 2026, 18, 5026-5037 (BSA-PEI, short-chain PFAS). DOI: 10.1021/acsami.5c13467"
REF_ID = "acsami2026_bsa_pei"


def main() -> int:
    rows = []
    for pfas, (qm_langmuir, qmax_meas) in DATA.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": float("nan"),   # variable concentration isotherm
            "ph": 7.0,
            "temperature": 25.0,                     # room temperature
            "contact_time": 120.0,                   # 2 h equilibrium
            "adsorbent_dose": 0.02,                  # 20 mg/L
            "adsorbent_type": "other",               # protein-based adsorbent
            "adsorbent_name": "PB(0.75) PEI-functionalized BSA nanoclusters",
            "water_matrix": "ultrapure",
            "adsorption_capacity": qmax_meas,        # measured max uptake
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": (f"measured qmax {qmax_meas} mg/g (Langmuir qm "
                            f"{qm_langmuir} mg/g, poor fit; Freundlich R2>0.99)"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
