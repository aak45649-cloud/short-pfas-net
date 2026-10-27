"""Convert ACS EST Water 2025 (hydrophobic PAC) short-chain PFAS data.

Source: ACS EST Water 2025, 5, 2322-2332
DOI: 10.1021/acsestwater.4c01222
"Improving the Hydrophobicity of Powder Activated Carbon to Enhance the
Adsorption Kinetics of Per- and Polyfluoroalkyl Substances"

Adsorbents: coconut-shell powder activated carbon (PAC) in three forms:
WWPAC (water-washed), AWPAC (acid-washed), PAC-1050 (acid-washed then
pyrolyzed at 1050 C).

Short-chain data extracted:
(A) PFBS (C4) pseudo-second-order (PSO) equilibrium capacity qe,4h (mg/g)
    from Table 3. Conditions: 30 mg/L PAC, 2 mg/L PFBS, in DI water or
    3 mg/L synthetic NOM solution, 4 h:
      WWPAC:  DI 47.22, NOM 65.39
      AWPAC:  DI 46.30, NOM 41.73
      PAC-1050: DI 53.92, NOM 40.45
(B) PFBA (C4) 167.5 mg/g on polyDADMAC-coated GAC — cited from
    Ramos et al., Environ. Pollut. 2022, 294, 118603 (in the Introduction).

Writes data/processed/hydrophobic_pac.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "hydrophobic_pac.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"  # C4
SMILES_PFBA = "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"             # C4

# (A) PFBS PSO qe,4h (mg/g): (adsorbent, water matrix, qe)
PFBS_PSO = [
    ("WWPAC (water-washed PAC)", "ultrapure", 47.22),
    ("WWPAC (water-washed PAC)", "other", 65.39),       # 3 mg/L NOM
    ("AWPAC (acid-washed PAC)", "ultrapure", 46.30),
    ("AWPAC (acid-washed PAC)", "other", 41.73),
    ("PAC-1050 (pyrolyzed PAC)", "ultrapure", 53.92),
    ("PAC-1050 (pyrolyzed PAC)", "other", 40.45),
]

REF = "ACS EST Water 2025, 5, 2322-2332 (hydrophobic PAC, PFBS). DOI: 10.1021/acsestwater.4c01222"
REF_ID = "acsestwater2025_hydrophobic_pac"
REF_PFBA = "Ramos et al., Environ. Pollut. 2022, 294, 118603 (polyDADMAC-coated GAC, PFBA). DOI: 10.1016/j.envpol.2021.118603"


def main() -> int:
    rows = []

    for ads_name, wm, qe in PFBS_PSO:
        rows.append({
            "pfas_name": "PFBS",
            "smiles": SMILES_PFBS,
            "chain_length": 4,
            "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 2.0,     # 2 mg/L PFBS
            "ph": float("nan"),               # not explicitly adjusted
            "temperature": 25.0,              # room temperature
            "contact_time": 240.0,            # 4 h equilibrium
            "adsorbent_dose": 0.03,           # 30 mg/L
            "adsorbent_type": "activated_carbon",
            "adsorbent_name": ads_name,
            "water_matrix": wm,
            "adsorption_capacity": qe,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "PSO qe,4h (mg/g), 30 mg/L PAC, 2 mg/L PFBS, 4 h"
                           + (" (3 mg/L NOM)" if wm == "other" else " (DI water)"),
        })

    # (B) PFBA on polyDADMAC-coated GAC (cited from Ramos et al. 2022)
    rows.append({
        "pfas_name": "PFBA",
        "smiles": SMILES_PFBA,
        "chain_length": 4,
        "is_short_chain": True,
        "initial_concentration": float("nan"),
        "ph": float("nan"),
        "temperature": float("nan"),
        "contact_time": float("nan"),
        "adsorbent_dose": float("nan"),
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": "polyDADMAC-coated GAC",
        "water_matrix": "other",
        "adsorption_capacity": 167.5,
        "removal_efficiency": float("nan"),
        "ref_ID": "envpollut2022_polydadmac_gac",
        "ref": REF_PFBA,
        "source_note": "PFBA capacity 167.5 mg/g (cited in ACS EST Water 2025 Intro, from Ramos et al. 2022)",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
