"""Convert Chem. Eng. J. 2026 (fluorinated activated carbon) PFBS removal data.

Source: Chemical Engineering Journal 539 (2026) 176796
DOI: 10.1016/j.cej.2026.176796
"Selective removal of long- and short-chain PFAS via fluorinated activated
carbon: Role of fluorophilic interactions"

Adsorbents: superfine activated carbon (SFAC) and fluorinated superfine
activated carbon (FSFAC). Short-chain PFBS (C4) removal via hydrophobic
+ fluorine-fluorine (F...F) interactions.

PFBS removal-efficiency data (Fig. 4), no mg/g capacity reported:
  SFAC  (2 ppm,  500 ppm adsorbent, 30 min):  >70%
  FSFAC (2 ppm,  500 ppm adsorbent, 30 min):  >90%
  SFAC  (50 ppb, 100 ppm adsorbent, 2 h):     76%
  FSFAC (50 ppb, 100 ppm adsorbent, 6 h):     ~90%

Writes data/processed/fsfac_pfbs.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "fsfac_pfbs.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"  # C4

# (adsorbent, c0 mg/L, dose mg/L, time min, removal %)
DATA = [
    ("SFAC (superfine activated carbon)", 2.0, 500.0, 30.0, 70.0),
    ("FSFAC (fluorinated superfine activated carbon)", 2.0, 500.0, 30.0, 90.0),
    ("SFAC (superfine activated carbon)", 0.05, 100.0, 120.0, 76.0),
    ("FSFAC (fluorinated superfine activated carbon)", 0.05, 100.0, 360.0, 90.0),
]

REF = "Chem. Eng. J. 2026, 539, 176796 (FSFAC, PFBS removal). DOI: 10.1016/j.cej.2026.176796"
REF_ID = "cej2026_fsfac"


def main() -> int:
    rows = []
    for ads_name, c0, dose, t, removal in DATA:
        rows.append({
            "pfas_name": "PFBS",
            "smiles": SMILES_PFBS,
            "chain_length": 4,
            "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": c0,
            "ph": float("nan"),
            "temperature": 25.0,
            "contact_time": t,
            "adsorbent_dose": dose / 1000.0,   # ppm -> g/L
            "adsorbent_type": "activated_carbon",
            "adsorbent_name": ads_name,
            "water_matrix": "ultrapure",
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": f"PFBS removal %, {c0} mg/L PFBS, {dose} ppm adsorbent, {t} min (Fig. 4)",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
