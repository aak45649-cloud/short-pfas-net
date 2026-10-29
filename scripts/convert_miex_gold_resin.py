"""Convert Appl. Sci. 2023 (MIEX GOLD ion-exchange resin) PFHxS removal data.

Source: Applied Sciences 2023, 13(10), 6263
DOI: 10.3390/app13106263
"Ion Exchange MIEX(R) GOLD Resin as a Promising Sorbent for the Removal of
PFAS Compounds"
Tamanna et al.

Adsorbent: MIEX(R) GOLD strong-base anion-exchange resin (magnetic).

Short-chain data extracted (Table 1, PFHxS = C6):
  - no interference ............................ 100.00 %
  - 20 ppm sulfate + 5 ppm nitrate .............  99.88 %
  - 5 ppm humic acid + 5 ppm tannic acid .......  99.82 %
  - high inorganic + NOM (50 HA + 50 TA +
    250 nitrate + 250 sulfate) .................  91.00 %
Batch: 0.5 mL resin (~0.11 g) / 25 mL, 1 ppm PFHxS, 30 min, 180 rpm, RT.

Writes data/processed/miex_gold_pfhxs.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "miex_gold_pfhxs.csv"

SMILES_PFHXS = "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(F)(F)F)(F)F"  # C6

REF = "Appl. Sci. 2023, 13, 6263 (MIEX GOLD resin, PFHxS). DOI: 10.3390/app13106263"
REF_ID = "applsei2023_miex_gold_pfhxs"

# (removal %, water_matrix, note)
CONDITIONS = [
    (100.00, "ultrapure", "no interference (Milli-Q water)"),
    (99.88, "groundwater", "20 ppm sulfate + 5 ppm nitrate"),
    (99.82, "surface_water", "5 ppm humic acid + 5 ppm tannic acid"),
    (91.00, "surface_water", "high inorganic + NOM (50 HA + 50 TA + 250 nitrate + 250 sulfate)"),
]


def main() -> int:
    rows = []
    for removal, matrix, note in CONDITIONS:
        rows.append({
            "pfas_name": "PFHxS",
            "smiles": SMILES_PFHXS,
            "chain_length": 6,
            "is_short_chain": 6 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 1.0,   # 1 ppm = 1 mg/L
            "ph": float("nan"),             # not adjusted / not reported
            "temperature": 25.0,            # room temperature
            "contact_time": 30.0,           # 30 min
            "adsorbent_dose": 4.4,          # 0.11 g resin / 0.025 L
            "adsorbent_type": "ion_exchange_resin",
            "adsorbent_name": "MIEX(R) GOLD magnetic anion-exchange resin",
            "water_matrix": matrix,
            "adsorption_capacity": float("nan"),
            "removal_efficiency": removal,
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": f"removal efficiency (%), {note}",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}  短链: {int(df['is_short_chain'].sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
