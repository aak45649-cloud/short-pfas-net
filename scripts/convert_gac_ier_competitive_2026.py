"""Convert J. Environ. Manage. 2026 (GAC vs IER competitive adsorption) data.

Source: Journal of Environmental Management 2026, 413, 130333
"Competitive adsorption of PFAS on granulated activated carbon and ion exchange
resins: Effects of co-existing PFASs, DOM, and phosphate"
Hazrati, Kumpiene, Carabante (Lulea University of Technology).

Adsorbents: F400 granular activated carbon (GAC) and Purolite PFA694E
strong-base anion-exchange resin (IER).

Short-chain data extracted from text:
(A) PFBS on GAC = 39.2 mg/g at day 14 (sequential-spiking system,
    2 uM initial per compound).
(B) PFBA on IER = 0.58 mg PFBA/g IER (four-compound mixed system).
Batch: 500 mL, 6 mg/L GAC / 20 mg/L IER, 0.01 M NaCl, pH 6.5 +/- 0.2,
room temperature, 7 days to equilibrium.

Writes data/processed/gac_ier_competitive_2026.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "gac_ier_competitive_2026.csv"

SMILES_PFBS = "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F"   # C4
SMILES_PFBA = "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]"                # C4

REF = "J. Environ. Manage. 2026, 413, 130333 (GAC F400 vs Purolite PFA694E, PFBS/PFBA). DOI: 10.1016/j.jenvman.2026.130333"
REF_ID = "jenvmanage2026_gac_ier_competitive"


def main() -> int:
    rows = [
        {
            "pfas_name": "PFBS",
            "smiles": SMILES_PFBS,
            "chain_length": 4,
            "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.600,   # 2 uM PFBS = 0.6 mg/L
            "ph": 6.5,
            "temperature": 22.0,              # room temperature
            "contact_time": 20160.0,          # day 14 = 336 h = 20160 min
            "adsorbent_dose": 0.006,          # 6 mg/L GAC
            "adsorbent_type": "activated_carbon",
            "adsorbent_name": "F400 granular activated carbon (Calgon)",
            "water_matrix": "ultrapure",
            "adsorption_capacity": 39.2,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "PFBS sorbed on GAC at day 14, sequential spiking, 2 uM initial",
        },
        {
            "pfas_name": "PFBA",
            "smiles": SMILES_PFBA,
            "chain_length": 4,
            "is_short_chain": 4 <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.428,   # 2 uM PFBA = 0.428 mg/L
            "ph": 6.5,
            "temperature": 22.0,
            "contact_time": 10080.0,          # 7 days = 168 h = 10080 min
            "adsorbent_dose": 0.020,          # 20 mg/L IER
            "adsorbent_type": "ion_exchange_resin",
            "adsorbent_name": "Purolite PFA694E strong-base anion-exchange resin",
            "water_matrix": "ultrapure",
            "adsorption_capacity": 0.58,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "PFBA sorbed on IER, four-compound mixed system, 2 uM initial",
        },
    ]

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}  短链: {int(df['is_short_chain'].sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
