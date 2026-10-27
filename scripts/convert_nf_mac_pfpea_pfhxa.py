"""Convert J. Water Process Eng. 2024 (NF + magnetic AC) short-chain PFAS data.

Source: J. Water Process Eng. 2024, 64, 105585
DOI: 10.1016/j.jwpe.2024.105585
"Amplified efficacy of short-chain perfluoroalkyl substances removal with
nanofiltration-magnetic activated carbon integration"

Adsorbents/processes:
(A) dNF40 hollow-fiber NF membrane (single process) — removal efficiency
(B) Powder activated carbon (PAC) — Langmuir qm + PSO qe
(C) Magnetic activated carbon (MAC, PAC+Fe3O4 ball-milled 3:1) — Langmuir qm + PSO qe

Short-chain PFAS: PFHxA (C6) and PFPeA (C5). Both short-chain.

Data blocks (Table 3 = isotherm, Table 4 = kinetics):
(A) NF removal: PFHxA 96.6%, PFPeA 86.1%
(B) PAC: Langmuir qm PFHxA 239 / PFPeA 174 mg/g; PSO qe PFHxA 60.18 / PFPeA 37.75 mg/g
(C) MAC: Langmuir qm PFHxA 332 / PFPeA 179 mg/g; PSO qe PFHxA 43.80 / PFPeA 32.70 mg/g

Conditions:
- Isotherm: C0 10–200 mg/L, neutral pH, 25 C, 1 h (60 min)
- Kinetics: C0 50 mg/L, 35 mL, dose 5–15 mg, 25 C, 30 min
- NF: neutral pH, 25 C

Writes data/processed/nf_mac_pfpea_pfhxa.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "nf_mac_pfpea_pfhxa.csv"

SMILES = {
    "PFPeA": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]",                 # C5
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",         # C6
}
CHAIN = {"PFPeA": 5, "PFHxA": 6}

REF = "J. Water Process Eng. 2024, 64, 105585 (NF dNF40 + PAC/MAC, PFHxA/PFPeA). DOI: 10.1016/j.jwpe.2024.105585"
REF_ID = "jwpe2024_nf_mac"


def _row(pfas, removal, capacity, ads_type, ads_name, note, c0, time, dose=float("nan")) -> dict:
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": c0,
        "ph": 7.0,                       # neutral pH (HCl/NaOH adjusted)
        "temperature": 25.0,
        "contact_time": time,
        "adsorbent_dose": dose,
        "adsorbent_type": ads_type,
        "adsorbent_name": ads_name,
        "water_matrix": "ultrapure",
        "adsorption_capacity": capacity if capacity is not None else float("nan"),
        "removal_efficiency": removal if removal is not None else float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": note,
    }


def main() -> int:
    rows = []

    # (A) NF membrane removal (single process)
    nf = [("PFHxA", 96.6), ("PFPeA", 86.1)]
    for pfas, r in nf:
        rows.append(_row(pfas, r, None, "membrane", "dNF40 hollow-fiber NF membrane",
                         f"NF single-process removal {r}% (optimal conditions)",
                         c0=0.3, time=float("nan")))  # 300 ppb feed

    # (B) PAC: Langmuir qm (Table 3) + PSO qe (Table 4)
    pac_qm = [("PFHxA", 239.0), ("PFPeA", 174.0)]
    pac_qe = [("PFHxA", 60.18), ("PFPeA", 37.75)]
    for pfas, qm in pac_qm:
        rows.append(_row(pfas, None, qm, "activated_carbon", "Powder activated carbon (PAC)",
                         f"Langmuir qmax {qm} mg/g (Table 3), C0 10-200 mg/L, 1 h",
                         c0=100.0, time=60.0))
    for pfas, qe in pac_qe:
        rows.append(_row(pfas, None, qe, "activated_carbon", "Powder activated carbon (PAC)",
                         f"pseudo-second-order qe {qe} mg/g (Table 4), C0 50 mg/L, 30 min",
                         c0=50.0, time=30.0))

    # (C) MAC: Langmuir qm (Table 3) + PSO qe (Table 4)
    mac_qm = [("PFHxA", 332.0), ("PFPeA", 179.0)]
    mac_qe = [("PFHxA", 43.80), ("PFPeA", 32.70)]
    for pfas, qm in mac_qm:
        rows.append(_row(pfas, None, qm, "activated_carbon", "Magnetic activated carbon (MAC)",
                         f"Langmuir qmax {qm} mg/g (Table 3), C0 10-200 mg/L, 1 h",
                         c0=100.0, time=60.0))
    for pfas, qe in mac_qe:
        rows.append(_row(pfas, None, qe, "activated_carbon", "Magnetic activated carbon (MAC)",
                         f"pseudo-second-order qe {qe} mg/g (Table 4), C0 50 mg/L, 30 min",
                         c0=50.0, time=30.0))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"含容量: {int(df['adsorption_capacity'].notna().sum())}, 含去除率: {int(df['removal_efficiency'].notna().sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
