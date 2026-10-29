"""Convert J. Environ. Chem. Eng. 2024 (sustainable wood-derived AC) PFHxA data.

Source: Journal of Environmental Chemical Engineering 2024, 12(6), 114855
DOI: 10.1016/j.jece.2024.114855
"Enhancing micropollutant removal efficiency using sustainable activated charcoal"
Selmi, Gentil, Fierro, Celzard.

Adsorbent: steam-activated wood charcoal, AC850C-2h (physical activation,
850-900 C, 1-2.5 h; BET 600-1380 m2/g, mesoporous).

Short-chain data extracted:
PFHxA (C6) maximum experimental adsorbed amount = 3135 mg/g
(abstract: 1977 / 670 / 3135 mg/g for PFOA / PFOS / PFHxA).
Isotherm range 10-1000 mg/L, AC dose 0.2 g/L.
Note: PFHxA isotherm shows no well-defined plateau (multilayer adsorption,
GBS model), so 3135 mg/g is the maximum experimental uptake at the highest
tested concentration (1000 mg/L), not a strict Langmuir saturation value.

Writes data/processed/wood_ac_pfhxa.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "wood_ac_pfhxa.csv"

SMILES_PFHXA = "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]"  # C6

REF = "J. Environ. Chem. Eng. 2024, 12, 114855 (steam-activated wood AC, PFHxA). DOI: 10.1016/j.jece.2024.114855"
REF_ID = "jece2024_wood_ac_pfhxa"


def main() -> int:
    rows = [{
        "pfas_name": "PFHxA",
        "smiles": SMILES_PFHXA,
        "chain_length": 6,
        "is_short_chain": 6 <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 1000.0,   # isotherm upper bound 10-1000 mg/L
        "ph": float("nan"),                # not specified (PFAS-free water)
        "temperature": 25.0,               # room temperature (not explicitly stated)
        "contact_time": float("nan"),      # equilibrium isotherm
        "adsorbent_dose": 0.2,             # 0.2 g AC / L
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": "Steam-activated wood charcoal (AC850C-2h)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": 3135.0,     # max experimental uptake, mg/g
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "max experimental uptake (mg/g) at 1000 mg/L, 0.2 g/L AC; multilayer (no plateau)",
    }]

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}  短链: {int(df['is_short_chain'].sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
