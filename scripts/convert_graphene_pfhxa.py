"""Convert Sustainability 2026 (su18147053) graphene PFHxA adsorption data to schema.

Source: Sustainability 2026, 18, 7053 (10.3390/su18147053)
"Adsorptive Removal of Short-Chain PFAS (PFHxA) from Water Matrices Using
Synthesised Graphene-Based Materials"

Extracts two kinds of PFHxA (C6, short-chain) adsorption data onto four
graphene-based materials and writes them to data/processed/graphene_pfhxa.csv:

  1. Langmuir maximum capacity QL (umol/g) from Table 6 (distilled water,
     pH = 3, 24 h isotherm) -> converted to mg/g.
  2. Highest single-point capacities from Table 3 (no pH correction) across
     four water matrices (DW/RW/TW/TWW) -> converted to mg/g.

PFHxA molecular weight = 313.04 g/mol, so 1 umol/g = 0.31304 mg/g.

Materials: SG-X = in-house thermally reduced graphene (TRG);
           CG-A/CG-B/CG-C = commercial reduced graphene oxides (rGO).

Run:
    python scripts/convert_graphene_pfhxa.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "graphene_pfhxa.csv"

PFHXA_SMILES = "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"
PFHXA_CHAIN = 6
PFHXA_MW = 313.04  # g/mol

# Water matrix -> canonical schema level
MATRIX_MAP = {
    "DW": "ultrapure",        # distilled water
    "RW": "surface_water",    # river water
    "TW": "drinking_water",   # tap water
    "TWW": "wastewater",      # treated wastewater
}

# Table 6: Langmuir maximum capacity QL (umol/g), distilled water, pH 3, 24 h
LANMGAUIR_QL_UMOL_G = {
    "CG-A": 76.31,
    "CG-B": 9.62,
    "CG-C": 81.90,
    "SG-X": 35.03,
}

# Table 3 (no pH correction): highest single-point capacity (umol/g) per matrix
CAPACITY_UMOL_G = {
    "CG-A": {"DW": 24.733, "RW": 3.543, "TW": 4.671, "TWW": 3.493},
    "CG-B": {"DW": 1.578,  "RW": 0.073, "TW": 0.128, "TWW": 0.571},
    "CG-C": {"DW": 17.97,  "RW": 0.426, "TW": 1.172, "TWW": 1.236},
    "SG-X": {"DW": 15.303, "RW": 0.523, "TW": 1.142, "TWW": 0.945},
}

REF = "Sustainability 2026, 18, 7053 (graphene PFHxA adsorption)"


def umol_to_mgg(umol: float) -> float:
    return umol * PFHXA_MW / 1000.0


def main() -> int:
    rows = []

    # 1. Langmuir maximum capacity (Table 6)
    for mat, ql in LANMGAUIR_QL_UMOL_G.items():
        rows.append({
            "pfas_name": "PFHxA",
            "smiles": PFHXA_SMILES,
            "chain_length": PFHXA_CHAIN,
            "is_short_chain": PFHXA_CHAIN <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": float("nan"),  # isotherm over 0.5-20 mg/L
            "ph": 3.0,
            "temperature": float("nan"),
            "contact_time": 1440.0,   # 24 h
            "adsorbent_dose": 1.0,    # 1 mg material / 1 mL
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": mat,
            "water_matrix": "ultrapure",  # distilled water
            "adsorption_capacity": round(umol_to_mgg(ql), 3),  # Langmuir QL -> mg/g
            "ref_ID": "sustainability2026",
            "ref": REF,
        })

    # 2. Single-point highest capacity across water matrices (Table 3)
    for mat, mdict in CAPACITY_UMOL_G.items():
        for matrix_code, val in mdict.items():
            rows.append({
                "pfas_name": "PFHxA",
                "smiles": PFHXA_SMILES,
                "chain_length": PFHXA_CHAIN,
                "is_short_chain": PFHXA_CHAIN <= SHORT_CHAIN_CUTOFF,
                "initial_concentration": float("nan"),
                "ph": 3.0,
                "temperature": float("nan"),
                "contact_time": 1440.0,
                "adsorbent_dose": 1.0,
                "adsorbent_type": "nanoadsorbent",
                "adsorbent_name": mat,
                "water_matrix": MATRIX_MAP[matrix_code],
                "adsorption_capacity": round(umol_to_mgg(val), 3),
                "ref_ID": "sustainability2026",
                "ref": REF,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {df['is_short_chain'].sum()} / {len(df)}")
    print(f"吸附剂类型: {df['adsorbent_type'].value_counts().to_dict()}")
    print(f"水基质: {df['water_matrix'].value_counts().to_dict()}")
    print(f"吸附容量范围: {df['adsorption_capacity'].min():.2f} ~ {df['adsorption_capacity'].max():.2f} mg/g")
    print(f"材料: {df['adsorbent_name'].unique().tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
