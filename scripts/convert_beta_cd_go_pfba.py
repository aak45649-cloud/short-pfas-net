"""Convert Chem. Eur. J. 2023 (β-cyclodextrin-GO) short-chain PFAS removal data.

Source: Chem. Eur. J. 2023, 29, e202301854
DOI: 10.1002/chem.202301854
"Chemical Tailoring of β-Cyclodextrin-Graphene Oxide for Enhanced
Perfluorobutanoic Acid Adsorption"

Adsorbents: graphene oxide (GO) functionalized with β-cyclodextrin via
alkyl linkers (GO-Cn-βCD, n=0/2/6/12). Best = GO-C6-βCD.

Short-chain PFAS: PFBA (C4). Target = removal efficiency (%) from tap water.

Data extracted (Fig. 4a, batch in tap water, 0.5 ug/L PFBA, 25 mL):
- GO-C6-βCD: 65% removal at 15 min (equilibrium)
- GAC (benchmark): 70% removal at 24 h

Conditions: tap water, PFBA 0.5 ug/L, room temp, 15 min / 24 h.

Writes data/processed/beta_cd_go_pfba.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "beta_cd_go_pfba.csv"

SMILES_PFBA = "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"  # C4

REMOVAL = [
    ("GO-C6-βCD (hexyl-linker β-CD-graphene oxide)", 65.0, 15.0),
    ("Granular activated carbon (GAC, Norit 830)", 70.0, 1440.0),
]

REF = "Chem. Eur. J. 2023, 29, e202301854 (β-CD-GO, PFBA). DOI: 10.1002/chem.202301854"
REF_ID = "chemeurj2023_betacd_go"


def _row(ads_name, removal, time) -> dict:
    return {
        "pfas_name": "PFBA",
        "smiles": SMILES_PFBA,
        "chain_length": 4,
        "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 0.0005,   # 0.5 ug/L
        "ph": float("nan"),                # tap water, neutral
        "temperature": float("nan"),       # room temp
        "contact_time": time,
        "adsorbent_dose": float("nan"),
        "adsorbent_type": "nanoadsorbent" if "β-CD" in ads_name else "activated_carbon",
        "adsorbent_name": ads_name,
        "water_matrix": "drinking_water",  # tap water
        "adsorption_capacity": float("nan"),
        "removal_efficiency": removal,
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": f"removal {removal}% from tap water, 0.5 ug/L PFBA, {time} min",
    }


def main() -> int:
    rows = [_row(ads, r, t) for ads, r, t in REMOVAL]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"去除率: {df['removal_efficiency'].tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
