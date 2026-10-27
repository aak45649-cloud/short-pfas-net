"""Convert Environ. Res. 2023 (polyamide microplastics) short-chain PFAS data.

Source: Environmental Research 216 (2023) 114834
DOI: 10.1016/j.envres.2022.114834
"Adsorption of perfluoroalkyl substances on polyamide microplastics: Effect
of sorbent and influence of environmental factors"

Adsorbent: polyamide (PA, nylon) microplastics, 50 um particle size.
PFASs adsorb via pore filling, hydrophobic interactions and hydrogen bonds.

Langmuir qmax (mg/g) from isotherms (0.1-25 mg/L, pH 5.88, 0% salinity,
0% dissolved organic matter), from the abstract:
  PFOS 0.873 > PFOA 0.235 > PFHpA 0.231 > PFHxA 0.201 > PFPeA 0.192 >
  PFBA 0.188
Short-chain (<=C6) subset extracted here: PFHxA (C6), PFPeA (C5), PFBA (C4).
(PFOS/PFOA/PFHpA are C8/C8/C7 long-chain and excluded.)

Also: removal % at 50 um particle size (Fig. 3), 99% for PFBuA (=PFBA).

Writes data/processed/pa_microplastics.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "pa_microplastics.csv"

SMILES = {
    "PFBA":  "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                              # C4
    "PFPeA": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]",                       # C5
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",                # C6
}
CHAIN = {"PFBA": 4, "PFPeA": 5, "PFHxA": 6}

# Langmuir qmax (mg/g), abstract, pH 5.88, 0% salinity, 0% DOM
QMAX = {"PFHxA": 0.201, "PFPeA": 0.192, "PFBA": 0.188}

REF = "Environ. Res. 2023, 216, 114834 (polyamide microplastics). DOI: 10.1016/j.envres.2022.114834"
REF_ID = "envres2023_pa_microplastics"


def main() -> int:
    rows = []
    for pfas, qmax in QMAX.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 25.0,    # isotherm upper bound (0.1-25 mg/L)
            "ph": 5.88,                       # pH 5.88, 0% salinity, 0% DOM
            "temperature": 25.0,
            "contact_time": 1440.0,           # 24 h equilibrium
            "adsorbent_dose": 16.7,           # 0.5 g / 30 mL
            "adsorbent_type": "other",        # microplastic (not in canonical levels)
            "adsorbent_name": "Polyamide (nylon) microplastic, 50 um",
            "water_matrix": "ultrapure",
            "adsorption_capacity": qmax,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "Langmuir qmax (mg/g), pH 5.88, 0% salinity, 0% DOM",
        })

    # removal % at 50 um (Fig. 3), PFBuA = PFBA
    rows.append({
        "pfas_name": "PFBA",
        "smiles": SMILES["PFBA"],
        "chain_length": 4,
        "is_short_chain": True,
        "initial_concentration": 0.5,         # 0.5 mg/L fortified mixture
        "ph": 5.88,
        "temperature": 25.0,
        "contact_time": 1440.0,
        "adsorbent_dose": 16.7,
        "adsorbent_type": "other",
        "adsorbent_name": "Polyamide (nylon) microplastic, 50 um",
        "water_matrix": "ultrapure",
        "adsorption_capacity": float("nan"),
        "removal_efficiency": 99.0,           # Fig. 3, 50 um particle size
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "removal % at 50 um particle size (Fig. 3)",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.3f}~{df['adsorption_capacity'].max():.3f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
