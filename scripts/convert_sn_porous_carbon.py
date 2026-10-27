"""Convert J. Hazard. Mater. 2026 (S/N-functionalized porous carbon) short-chain PFAS data.

Source: J. Hazard. Mater. 2026, 508, 141781
DOI: 10.1016/j.jhazmat.2026.141781
"Toward improving porous carbon performance for adsorption of short-chain PFAS:
Exploring the effects of S- and N- containing surface groups"

Adsorbents (porous carbons from oxidized BP):
- BP   (initial porous carbon, control)
- BN   (HNO3-oxidized carbon)
- BNT6 (thiourea-functionalized, heated 600 C)
- BNA6 (ANSA-functionalized, heated 600 C)

Short-chain PFAS: PFBA (C4) and PFBS (C4).

Data extracted (Table 2, Langmuir-Freundlich fit at Ce=0.2 mmol/L):
- Qe (mmol/g) at Ce=0.2 mmol/L:
    BP   PFBA 0.24 / PFBS 0.26
    BN   PFBA ~0.01 (negligible, skip)
    BNT6 PFBA 0.25 / PFBS 0.28
    BNA6 PFBA 0.14 / PFBS 0.14
- qm (mmol/g):
    BP   PFBA 0.401 / PFBS 0.362
    BNT6 PFBA 0.736 / PFBS 0.331
    BNA6 PFBA 0.204 / PFBS 0.15

Conversions to mg/g using free-acid MW: PFBA 214.04, PFBS 300.10 g/mol.

Conditions: PFBA 0.18 mmol/L at pH 3.8; PFBS 0.16 mmol/L at pH 3.6;
20 mg carbon in 20 mL (= 1 g/L dose), 21 C, 5 h (PFBA) / 30 min (PFBS).

Writes data/processed/sn_porous_carbon.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "sn_porous_carbon.csv"

SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                   # C4
    "PFBS": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",       # C4
}
CHAIN = {"PFBA": 4, "PFBS": 4}
MW = {"PFBA": 214.04, "PFBS": 300.10}

# Qe (mmol/g) at Ce=0.2 mmol/L, Table 2
QE_MMOL = {
    "BP":   {"PFBA": 0.24, "PFBS": 0.26},
    "BNT6": {"PFBA": 0.25, "PFBS": 0.28},
    "BNA6": {"PFBA": 0.14, "PFBS": 0.14},
}
# Langmuir-Freundlich qm (mmol/g), Table 2
QM_MMOL = {
    "BP":   {"PFBA": 0.401, "PFBS": 0.362},
    "BNT6": {"PFBA": 0.736, "PFBS": 0.331},
    "BNA6": {"PFBA": 0.204, "PFBS": 0.15},
}

# conditions differ slightly by PFAS
PH = {"PFBA": 3.8, "PFBS": 3.6}
TIME = {"PFBA": 300.0, "PFBS": 30.0}   # 5 h / 30 min

REF = "J. Hazard. Mater. 2026, 508, 141781 (S/N porous carbon, PFBA/PFBS). DOI: 10.1016/j.jhazmat.2026.141781"
REF_ID = "jhazmat2026_sn_carbon"


def _row(pfas, capacity_mg, ads_name, note, c0) -> dict:
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": c0,
        "ph": PH[pfas],
        "temperature": 21.0,
        "contact_time": TIME[pfas],
        "adsorbent_dose": 1.0,           # 20 mg / 20 mL
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": ads_name,
        "water_matrix": "ultrapure",
        "adsorption_capacity": capacity_mg,
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": note,
    }


def main() -> int:
    rows = []

    # (A) Qe at Ce=0.2 mmol/L -> mg/g
    for ads, d in QE_MMOL.items():
        for pfas, qe_mmol in d.items():
            mg = qe_mmol * MW[pfas]
            rows.append(_row(pfas, round(mg, 3), ads,
                             f"Qe {qe_mmol} mmol/g at Ce=0.2 mmol/L (= {mg:.3f} mg/g), Table 2",
                             c0=round(0.2 * MW[pfas], 1)))

    # (B) Langmuir-Freundlich qm -> mg/g
    for ads, d in QM_MMOL.items():
        for pfas, qm_mmol in d.items():
            mg = qm_mmol * MW[pfas]
            rows.append(_row(pfas, round(mg, 2), ads,
                             f"Langmuir-Freundlich qm {qm_mmol} mmol/g (= {mg:.2f} mg/g), Table 2",
                             c0=round(0.2 * MW[pfas], 1)))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.2f}~{df['adsorption_capacity'].max():.2f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
