"""Convert Tsinghua subnanoporous activated biochar (2026) PFBA data.

Source: (Tsinghua University, Shubo Deng group) 2026
"Highly subnanoporous-basic activated biochar for enhanced removal of
short-chain PFAS from drinking water"
(open-access; see local literature library PDF 0019)

Adsorbent: C34%b — steam-activated (34% burn-off) subnanoporous-basic
activated biochar. Adsorbent type: activated_carbon (activated biochar).

Extracted (single-component isotherm, Langmuir max uptake):
  - PFBA: 141.8 mg/g on C34%b (text, single-component, pH 7.5)

Conditions:
  - initial concentration range 12.5-200 mg/L (isotherm), pH 7.5,
    room temperature, equilibrium 7 days, dose 20 mg / 400 mL = 0.05 g/L.

Note: only PFBA max capacity is stated numerically in the main text;
capacities for HFPO-DA/PFHxS/PFOA are in Table S5 (supplementary).

Writes data/processed/subnanoporous_biochar_pfba.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "subnanoporous_biochar_pfba.csv"

SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",   # C4
}
CHAIN = {"PFBA": 4}

REF = "Tsinghua 2026 (subnanoporous-basic activated biochar C34%b)"
REF_ID = "tsinghua2026_subnanobiochar"


def main() -> int:
    rows = [{
        "pfas_name": "PFBA",
        "smiles": SMILES["PFBA"],
        "chain_length": CHAIN["PFBA"],
        "is_short_chain": True,
        "initial_concentration": 200.0,       # upper isotherm bound (mg/L)
        "ph": 7.5,
        "temperature": 25.0,                  # room temperature (assumed)
        "contact_time": 10080.0,              # 7 days in minutes
        "adsorbent_dose": 0.05,               # 20 mg / 400 mL = 0.05 g/L
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": "C34%b (subnanoporous-basic activated biochar)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": 141.8,         # Langmuir qmax (mg/g)
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
    }]

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}，短链: {int(df['is_short_chain'].sum())}")
    print(f"PFBA 最大吸附容量: {df['adsorption_capacity'].tolist()} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
