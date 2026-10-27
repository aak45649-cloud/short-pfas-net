"""Convert Sci. Rep. 2026 (APTES-diatomite) short-chain PFBS adsorption data.

Source: Scientific Reports 2026, 16, 10368
DOI: 10.1038/s41598-026-41388-4
"Efficient adsorption of perfluorooctane sulfonate and perfluorobutane
sulfonic acid from aqueous solution onto amine-functionalized diatomite
granules"

Adsorbent: (3-aminopropyl)triethoxysilane (APTES)-modified diatomaceous
earth granules (APTES-DE). PFBS (C4, short-chain) and PFOS (C8, long-chain).

Short-chain PFBS data extracted:
(A) Langmuir qmax = 17.97 mg/g (Table 2; PFOS 26.47 mg/g long-chain, excluded).
    Batch: 0.4 g / 80 mL, 25-100 mg/L PFBS, pH ~8.0, 25 C, 120 rpm.
(B) Max removal efficiency = 89.90% (abstract/conclusions).
(C) GAC Langmuir capacity for PFBS = 48.3 umol/g (cited from
    Zhang et al. 2021, Environ. Technol. 42, 1798-1809, in the Introduction).
    48.3 umol/g * 300.10 g/mol (PFBS K salt MW) = 14.49 mg/g.

Writes data/processed/aptes_diatomite.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "aptes_diatomite.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"  # C4

REF = "Sci. Rep. 2026, 16, 10368 (APTES-diatomite, PFBS). DOI: 10.1038/s41598-026-41388-4"
REF_ID = "scirep2026_aptes_diatomite"
REF_GAC = "Zhang et al., Environ. Technol. 2021, 42, 1798-1809 (GAC, PFBS). DOI: 10.1080/09593330.2020.1720306"


def main() -> int:
    rows = []

    # (A) Langmuir qmax for PFBS
    rows.append({
        "pfas_name": "PFBS",
        "smiles": SMILES_PFBS,
        "chain_length": 4,
        "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": 100.0,    # 25-100 mg/L upper bound
        "ph": 8.0,                         # natural solution pH ~8.0
        "temperature": 25.0,
        "contact_time": float("nan"),      # "optimal duration" not specified
        "adsorbent_dose": 5.0,             # 0.4 g / 80 mL
        "adsorbent_type": "other",         # amine-functionalized diatomite (siliceous)
        "adsorbent_name": "APTES-modified diatomaceous earth granules (APTES-DE)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": 17.97,
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "Langmuir qmax (mg/g), 0.4 g/80 mL, 25-100 mg/L PFBS, pH 8",
    })

    # (B) max removal efficiency
    rows.append({
        "pfas_name": "PFBS",
        "smiles": SMILES_PFBS,
        "chain_length": 4,
        "is_short_chain": True,
        "initial_concentration": 25.0,     # fixed-bed influent 25 mg/L
        "ph": 8.0,
        "temperature": 25.0,
        "contact_time": float("nan"),
        "adsorbent_dose": float("nan"),    # fixed-bed column
        "adsorbent_type": "other",
        "adsorbent_name": "APTES-modified diatomaceous earth granules (APTES-DE)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": float("nan"),
        "removal_efficiency": 89.90,
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": "max removal efficiency (%), fixed-bed column",
    })

    # (C) GAC capacity for PFBS (cited, converted to mg/g)
    rows.append({
        "pfas_name": "PFBS",
        "smiles": SMILES_PFBS,
        "chain_length": 4,
        "is_short_chain": True,
        "initial_concentration": float("nan"),
        "ph": float("nan"),
        "temperature": float("nan"),
        "contact_time": float("nan"),
        "adsorbent_dose": float("nan"),
        "adsorbent_type": "activated_carbon",
        "adsorbent_name": "Granular activated carbon (GAC)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": 14.49,      # 48.3 umol/g * 300.10 g/mol
        "removal_efficiency": float("nan"),
        "ref_ID": "envtechnol2021_gac_pfbs",
        "ref": REF_GAC,
        "source_note": "GAC Langmuir capacity 48.3 umol/g (cited in Sci. Rep. 2026 Intro), =14.49 mg/g",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
