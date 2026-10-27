"""Convert Adv. Sci. 2026 (PPy@P-CF conductive carbon cloth) short-chain PFAS data.

Source: Adv. Sci. 2026
DOI: 10.1002/advs.76133
"Efficient Concentration and Complete Destruction of Short-Chain and
Emerging PFAS in Contaminated Water via Integrated Interface Engineering"

Adsorbent: PPy1@P0.5-CF700 (polypyrrole + phosphate groups on pyrolytic
carbon cloth, conductive 3D porous). Benchmarks: GAC, CF700.

Short-chain PFAS: TFA (C2), PFBA (C4), GenX (C3/ether). All short-chain.

Data extracted (Langmuir qm, Table S2 / Fig. 2d-f):
- PPy1@P0.5-CF700 qm (mg/g): TFA 283.2, PFBA 572.1, GenX 510.2

Conditions: isotherm 1-500 mg/L, 24 h, room temp; kinetics 100 ug/L.

Writes data/processed/ppy_carbon_cloth.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "ppy_carbon_cloth.csv"

SMILES = {
    "TFA":  "C(=O)(C(F)(F)F)[O-]",                        # C2
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",          # C4
    "GenX": "C(=O)(C(C(F)(F)F)(OC(C(C(F)(F)F)(F)F)(F)F)F)[O-]",  # HFPO-DA
}
CHAIN = {"TFA": 2, "PFBA": 4, "GenX": 3}

# Langmuir qm (mg/g) on PPy1@P0.5-CF700
QM = [
    ("TFA", 283.2),
    ("PFBA", 572.1),
    ("GenX", 510.2),
]

REF = "Adv. Sci. 2026 (PPy@P-CF conductive carbon cloth, TFA/PFBA/GenX). DOI: 10.1002/advs.76133"
REF_ID = "advsci2026_ppy_cf"


def _row(pfas, qm) -> dict:
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 250.0,  # isotherm range 1-500 mg/L midpoint
        "ph": float("nan"),              # not reported (DI water)
        "temperature": float("nan"),     # room temp
        "contact_time": 1440.0,          # 24 h
        "adsorbent_dose": float("nan"),  # not reported numerically
        "adsorbent_type": "nanoadsorbent",
        "adsorbent_name": "PPy1@P0.5-CF700 (polypyrrole/phosphate pyrolytic carbon cloth)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": qm,
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": f"Langmuir qmax {qm} mg/g (Table S2), 1-500 mg/L, 24 h",
    }


def main() -> int:
    rows = [_row(pfas, qm) for pfas, qm in QM]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
