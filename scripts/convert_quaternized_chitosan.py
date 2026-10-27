"""Convert Gels 2026 (quaternized chitosan hydrogels) PFAS removal data.

Source: Gels 2026, 12, 14 — DOI: 10.3390/gels12010014
"Highly Efficient Removal of PFAS from Water Using Surface-Modified
Regenerable Quaternized Chitosan Hydrogels"

Adsorbents (chitosan hydrogels, ion-exchange type):
  - CG   = pristine chitosan hydrogel (primary amine, pH-sensitive)
  - QCG  = quaternized chitosan hydrogel (permanent + charge, GTMAC)
  - MQCG = surface-modified quaternized chitosan hydrogel (PEG microchannels)

Data from Table 1 (500 µg/L PFAS, 24 h equilibrium, DI water, triplicate):
  Removal efficiency (%) and equilibrium capacity qe (mg/g) for:
    long-chain  PFOS (C8), PFOA (C8)
    short-chain PFBS (C4), PFHxA (C6)

Conditions (Section 4.5):
  - 40 mL of 500 µg/L PFAS (0.5 mg/L), rotary mixer 40 rpm, 24 h
  - adsorbent mass ~10 mg (back-calculated from qe = (Ci-Cf)*V/m) -> dose 0.25 g/L
  - room temperature, DI water (pH ~7, unadjusted)

MQCG qe values are reported as ">=2.000 mg/g" because effluent fell below the
instrument LOQ; 2.0 mg/g is the measurable capacity ceiling, recorded here as a
conservative lower bound.

Writes data/processed/quaternized_chitosan.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "quaternized_chitosan.csv"

SMILES = {
    "PFOS":  "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(C(C(F)(F)F)(F)F)(F)F)(F)F",  # C8
    "PFOA":  "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",             # C8
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",                              # C4
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",                           # C6
}
CHAIN = {"PFOS": 8, "PFOA": 8, "PFBS": 4, "PFHxA": 6}

# adsorbent -> {PFAS: (removal %, qe mg/g)}
DATA = {
    "CG (chitosan hydrogel)": {
        "PFOS":  (98.12, 1.962),
        "PFOA":  (92.18, 1.840),
        "PFBS":  (64.43, 1.291),
        "PFHxA": (34.32, 0.691),
    },
    "QCG (quaternized chitosan hydrogel)": {
        "PFOS":  (99.84, 1.997),
        "PFOA":  (99.48, 1.980),
        "PFBS":  (98.70, 1.974),
        "PFHxA": (94.30, 1.884),
    },
    "MQCG (surface-modified quaternized chitosan hydrogel)": {
        "PFOS":  (100.00, 2.000),   # reported >=2.000 (LOQ ceiling)
        "PFOA":  (100.00, 2.000),
        "PFBS":  (99.98, 1.999),    # reported >=1.999
        "PFHxA": (99.96, 1.998),    # reported >=1.998
    },
}

REF = ("Gels 2026, 12, 14 (quaternized chitosan hydrogels CG/QCG/MQCG; "
       "MQCG qe = LOQ ceiling >=2 mg/g). DOI: 10.3390/gels12010014")
REF_ID = "gels2026_chitosan"


def main() -> int:
    rows = []
    for ads_name, pfas_map in DATA.items():
        for pfas, (removal, qe) in pfas_map.items():
            rows.append({
                "pfas_name": pfas,
                "smiles": SMILES[pfas],
                "chain_length": CHAIN[pfas],
                "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
                "initial_concentration": 0.5,     # 500 µg/L = 0.5 mg/L
                "ph": 7.0,                        # DI water, unadjusted
                "temperature": 25.0,              # room temperature
                "contact_time": 1440.0,           # 24 h
                "adsorbent_dose": 0.25,           # ~10 mg / 40 mL
                "adsorbent_type": "ion_exchange_resin",
                "adsorbent_name": ads_name,
                "water_matrix": "ultrapure",
                "adsorption_capacity": qe,
                "removal_efficiency": removal,
                "ref_ID": REF_ID,
                "ref": REF,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    print(f"吸附剂类型: {df['adsorbent_type'].unique().tolist()}")
    print(f"容量范围: {df['adsorption_capacity'].min():.3f}~{df['adsorption_capacity'].max():.3f} mg/g")
    print(f"去除率范围: {df['removal_efficiency'].min():.2f}~{df['removal_efficiency'].max():.2f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
