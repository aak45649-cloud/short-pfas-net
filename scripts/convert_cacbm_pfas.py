"""Convert ACS EST Water 2025 (ball-milled colloidal AC) short-chain PFAS data.

Source: ACS EST Water 2025, 5, 6554-6566
DOI: 10.1021/acsestwater.5c00641
"Adsorptive Removal of PFAS from Aqueous Solutions Using GAC, PAC and
Ball-Milled Colloidal Activated Carbon: Characterizing Efficiency,
Kinetics, and Mechanisms"

Adsorbent: ball-milled colloidal activated carbon (CACBM), and GAC control.
Short-chain PFAS: PFBA (C4) and PFBS (C4). Long-chain PFOA/PFOS excluded.

Data extracted:
(A) Langmuir qmax (umol/g) on CACBM (Table 2): PFBA 48.28, PFBS 152.43.
    Converted to mg/g: PFBA 48.28e-6*214.04=0.0103 mg/g; PFBS 152.43e-6*300.10=0.0457 mg/g.
    (Note: umol/g scale => very small mg/g values; reported as-is.)
(B) Pseudo-second-order qe (mg/g) on CACBM (Table 1): PFBA 4.69, PFBS 15.27.

Conditions: isotherm 24 h, adsorbent dose 30 ppm, pH 6.2 (unadjusted),
22 C; kinetics at 1.0 mg/L initial.

Writes data/processed/cacbm_pfas.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "cacbm_pfas.csv"

SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                   # C4
    "PFBS": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",       # C4
}
CHAIN = {"PFBA": 4, "PFBS": 4}
MW = {"PFBA": 214.04, "PFBS": 300.10}

# Langmuir qmL (umol/g) on CACBM, Table 2
QML_UMOL = {"PFBA": 48.28, "PFBS": 152.43}

# PSO qe (mg/g) on CACBM, Table 1
QE_PSO = {"PFBA": 4.69, "PFBS": 15.27}

REF = "ACS EST Water 2025, 5, 6554-6566 (CACBM, short-chain PFAS). DOI: 10.1021/acsestwater.5c00641"
REF_ID = "acsestwater2025_cacbm"


def _row(pfas: str, capacity: float | None, note: str, dose: float, time: float, c0: float) -> dict:
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": c0,
        "ph": 6.2,                         # unadjusted pH
        "temperature": 22.0,               # room temperature
        "contact_time": time,
        "adsorbent_dose": dose,            # mg/L -> g/L
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": "Ball-milled colloidal activated carbon (CACBM)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": capacity if capacity is not None else float("nan"),
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": note,
    }


def main() -> int:
    rows = []

    # (A) Langmuir qmax (umol/g -> mg/g)
    for pfas, qml in QML_UMOL.items():
        mg_per_g = qml * 1e-6 * MW[pfas]
        rows.append(_row(pfas, round(mg_per_g, 4),
                         f"Langmuir qmax {qml} umol/g (= {mg_per_g:.4f} mg/g), Table 2, 24 h, 30 ppm",
                         dose=0.03, time=1440.0, c0=1.0))

    # (B) PSO qe (mg/g)
    for pfas, qe in QE_PSO.items():
        rows.append(_row(pfas, qe,
                         f"pseudo-second-order qe {qe} mg/g, Table 1, 1.0 mg/L",
                         dose=0.03, time=float("nan"), c0=1.0))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
