"""Convert J. Hazard. Mater. 2023 (functionalized PMO) short-chain PFBA data.

Source: Journal of Hazardous Materials 449 (2023) 131047
DOI: 10.1016/j.jhazmat.2023.131047
"Enhanced adsorption of short-chain perfluorobutanoic acid by functionalized
periodic mesoporous organosilica: Performance and mechanisms"

Adsorbents: functionalized periodic mesoporous organosilica (PMO) with
tunable amine (NH) and fluoroalkyl (CF) groups. Classified as nanoadsorbent
(mesoporous organosilica).

Data (Langmuir qmax, mg/g, PFBA, pH 7, adsorbent loading 0.5 g/L,
room temperature, Fig. 3b):
  PMO-NH-0     (amine only)          303.0 mg/g
  PMO-NH-CF-1  (fluoroalkyl:amine 1) 263.2 mg/g
  PMO-NH-CF-2  (fluoroalkyl:amine 2) 227.3 mg/g
  PMO-NH-CF-3  (fluoroalkyl:amine 3) 192.3 mg/g

Also: ~85% PFBA removal efficiency at low concentration (200 ug/L,
5 min equilibrium).

Writes data/processed/pmos_pfba.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "pmos_pfba.csv"

SMILES_PFBA = "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"  # C4

# adsorbent -> Langmuir qmax (mg/g)
DATA = [
    ("PMO-NH-0 (amine-functionalized PMO)", 303.0),
    ("PMO-NH-CF-1 (fluoroalkyl/amine=1 PMO)", 263.2),
    ("PMO-NH-CF-2 (fluoroalkyl/amine=2 PMO)", 227.3),
    ("PMO-NH-CF-3 (fluoroalkyl/amine=3 PMO)", 192.3),
]

REF = "J. Hazard. Mater. 2023, 449, 131047 (functionalized PMO, PFBA). DOI: 10.1016/j.jhazmat.2023.131047"
REF_ID = "jhazmat2023_pmo"


def main() -> int:
    rows = []
    for ads_name, qmax in DATA:
        rows.append({
            "pfas_name": "PFBA",
            "smiles": SMILES_PFBA,
            "chain_length": 4,
            "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 10.0,     # isotherm up to 10 mg/L (upper bound)
            "ph": 7.0,
            "temperature": 25.0,               # room temperature
            "contact_time": 60.0,              # equilibrium within 60 min at 10 mg/L
            "adsorbent_dose": 0.5,             # 0.5 g/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": ads_name,
            "water_matrix": "ultrapure",
            "adsorption_capacity": qmax,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "Langmuir qmax (mg/g), pH 7, 0.5 g/L",
        })

    # removal efficiency record (low concentration, fast kinetics)
    rows.append({
        "pfas_name": "PFBA",
        "smiles": SMILES_PFBA,
        "chain_length": 4,
        "is_short_chain": True,
        "initial_concentration": 0.2,          # 200 ug/L
        "ph": 7.0,
        "temperature": 25.0,
        "contact_time": 5.0,                   # equilibrium within 5 min
        "adsorbent_dose": 0.5,
        "adsorbent_type": "nanoadsorbent",
        "adsorbent_name": "PMO-NH-0 (amine-functionalized PMO)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": float("nan"),
        "removal_efficiency": 85.0,            # ~85%
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "~85% removal at 200 ug/L, 5 min",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
