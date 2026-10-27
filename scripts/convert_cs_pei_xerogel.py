"""Convert Chem. Eng. J. 2023 (CS/PEI xerogel) short-chain PFBS data.

Source: Chemical Engineering Journal 466 (2023) 143236
DOI: 10.1016/j.cej.2023.143236
"Efficient removal of perfluorobutanesulfonic acid from water through a
chitosan/polyethyleneimine xerogel"

Adsorbent: CS/PEI composite xerogel (chitosan + polyethyleneimine,
cryogelation, 30x water swelling). Classified as nanoadsorbent
(polymeric xerogel).

Data (main text, Fig. 5):
  - Maximum PFBS adsorption capacity: 305 +/- 45 mg/g (isotherm plateau,
    C0 up to 600 ppm)
  - Equilibrium reached within ~24 h

Conditions (Section 2.4): 13 mL PFBS solution, ~22.5 mg dry xerogel
(dose ~1.73 g/L), pH ~6.5, static, room temperature.

Writes data/processed/cs_pei_xerogel.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "cs_pei_xerogel.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"  # C4

REF = "Chem. Eng. J. 2023, 466, 143236 (CS/PEI xerogel, PFBS). DOI: 10.1016/j.cej.2023.143236"
REF_ID = "cej2023_cspei"


def main() -> int:
    rows = []
    rows.append({
        "pfas_name": "PFBS",
        "smiles": SMILES_PFBS,
        "chain_length": 4,
        "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 600.0,        # C0 up to 600 ppm
        "ph": 6.5,
        "temperature": 25.0,                   # room temperature
        "contact_time": 1440.0,                # 24 h equilibrium
        "adsorbent_dose": 1.73,                # ~22.5 mg / 13 mL
        "adsorbent_type": "nanoadsorbent",
        "adsorbent_name": "CS/PEI xerogel (chitosan/polyethyleneimine)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": 305.0,
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "max capacity 305 +/- 45 mg/g (isotherm plateau, C0 up to 600 ppm), pH 6.5",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量: {df['adsorption_capacity'].tolist()} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
