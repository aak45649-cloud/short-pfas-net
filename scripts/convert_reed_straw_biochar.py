"""Convert STOTEN 2024 (Fe/Cu-loaded reed straw biochar) short-chain PFAS data.

Source: Science of the Total Environment 946 (2024) 174223
"Efficient adsorption of short-chain perfluoroalkyl substances by pristine
and Fe/Cu-loaded reed straw biochars"
DOI: 10.1016/j.scitotenv.2024.174223

Adsorbents (biochar):
  - R     = pristine reed straw biochar
  - R-Fe  = Fe-doped reed straw biochar
  - R-Cu  = Cu-doped reed straw biochar

Sorption capacities (mg/g), from abstract + text (isotherm max):
  PFBA:  R 15.64, R-Fe 25.81, R-Cu 19.34
  PFPeA: R 28.12, R-Fe 43.59, R-Cu 33.69
  (R values back-calculated from R-Fe/R-Cu via reported 1.65x/1.55x/1.24x/1.20x)

Conditions:
  - dose 0.005 g / 10 mL = 0.5 g/L, 25 C, 24 h,
    isotherm initial concentration 0.05-10 mg/L.

Writes data/processed/reed_straw_biochar.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "reed_straw_biochar.csv"

SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                       # C4
    "PFPeA": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]",              # C5
}
CHAIN = {"PFBA": 4, "PFPeA": 5}

# (adsorbent, capacity dict)
DATA = [
    ("R (reed straw biochar)", {"PFBA": 15.64, "PFPeA": 28.12}),
    ("R-Fe (Fe-doped reed straw biochar)", {"PFBA": 25.81, "PFPeA": 43.59}),
    ("R-Cu (Cu-doped reed straw biochar)", {"PFBA": 19.34, "PFPeA": 33.69}),
]

REF = "Sci. Total Environ. 2024, 946, 174223 (reed straw biochar R/R-Fe/R-Cu)"
REF_ID = "stoten2024_reedbiochar"


def main() -> int:
    rows = []
    for ads_name, caps in DATA:
        for pfas in ["PFBA", "PFPeA"]:
            rows.append({
                "pfas_name": pfas,
                "smiles": SMILES[pfas],
                "chain_length": CHAIN[pfas],
                "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
                "initial_concentration": 10.0,      # upper isotherm bound (mg/L)
                "ph": 7.0,                          # DI water control (unadjusted)
                "temperature": 25.0,
                "contact_time": 1440.0,             # 24 h
                "adsorbent_dose": 0.5,              # 0.005 g / 10 mL
                "adsorbent_type": "biochar",
                "adsorbent_name": ads_name,
                "water_matrix": "ultrapure",
                "adsorption_capacity": caps[pfas],
                "removal_efficiency": float("nan"),
                "ref_ID": REF_ID,
                "ref": REF,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}，短链: {int(df['is_short_chain'].sum())}")
    print(f"吸附剂类型: {df['adsorbent_type'].unique().tolist()}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
