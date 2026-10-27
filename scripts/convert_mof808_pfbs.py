"""Convert ACS Omega 2025 (MOF-808) short-chain PFBS adsorption data.

Source: ACS Omega 2025, 10, 44311-44320
DOI: 10.1021/acsomega.5c05815
"Influence of Charge Compensating Anions on the Adsorption of
Perfluorobutanesulfonate in MOF-808"

Adsorbents: MOF-808 derivatives with different charge-compensating anions
(cca): formate (FA), acetate (AA), trifluoroacetate (TFA), and chloride (AF,
acetate-derived then HCl-exchanged). PFBS (C4, short-chain) adsorbs via
ion-exchange.

Two data blocks (all PFBS, short-chain):
(A) Equilibrium capacity under "standard conditions" (10 mg MOF, 1 mL
    500 mg/L PFBS, 25 C, 300 rpm, equilibrium <50 min), Fig. 4b:
      MOF-808-FA 95, -AA 139, -TFA 263, -AF 372 mg/g
(B) Langmuir qmax from isotherms (100-2500 mg/L, 2 h), Table 4:
      MOF-808-FA 385, -AA 511, -TFA 721, -AF 837 mg/g

pH not explicitly adjusted (ultrapure/DI water). Dose = 10 mg / 1 mL = 10 g/L.

Writes data/processed/mof808_pfbs.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "mof808_pfbs.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"  # C4, 44 chars

# (A) equilibrium capacity under standard conditions (500 mg/L challenge)
CAPACITY_500 = [
    ("MOF-808-FA (formate cca)", 95.0),
    ("MOF-808-AA (acetate cca)", 139.0),
    ("MOF-808-TFA (trifluoroacetate cca)", 263.0),
    ("MOF-808-AF (chloride cca)", 372.0),
]

# (B) Langmuir qmax from isotherms
LANGMUIR_QMAX = [
    ("MOF-808-FA (formate cca)", 385.0),
    ("MOF-808-AA (acetate cca)", 511.0),
    ("MOF-808-TFA (trifluoroacetate cca)", 721.0),
    ("MOF-808-AF (chloride cca)", 837.0),
]

REF = "ACS Omega 2025, 10, 44311-44320 (MOF-808, PFBS). DOI: 10.1021/acsomega.5c05815"
REF_ID = "acsomega2025_mof808"


def _row(ads_name: str, capacity: float | None, note: str) -> dict:
    return {
        "pfas_name": "PFBS",
        "smiles": SMILES_PFBS,
        "chain_length": 4,
        "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 500.0,   # standard 500 mg/L challenge
        "ph": float("nan"),               # not explicitly adjusted (DI water)
        "temperature": 25.0,
        "contact_time": 50.0,             # equilibrium within 50 min
        "adsorbent_dose": 10.0,           # 10 mg / 1 mL
        "adsorbent_type": "nanoadsorbent",
        "adsorbent_name": ads_name,
        "water_matrix": "ultrapure",
        "adsorption_capacity": capacity if capacity is not None else float("nan"),
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": note,
    }


def main() -> int:
    rows = []

    for ads_name, qe in CAPACITY_500:
        rows.append(_row(ads_name, qe, "equilibrium capacity, 500 mg/L PFBS, 25 C"))

    for ads_name, qmax in LANGMUIR_QMAX:
        rows.append(_row(ads_name, qmax, "Langmuir qmax (mg/g), 100-2500 mg/L, 2 h"))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
