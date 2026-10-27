"""Convert J. Hazard. Mater. 2023 (GAC competitive adsorption) short-chain data.

Source: Journal of Hazardous Materials 460 (2023) 132378
DOI: 10.1016/j.jhazmat.2023.132378
"Coexisting ions and long-chain per- and polyfluoroalkyl substances (PFAS)
inhibit the adsorption of short-chain PFAS by granular activated carbon"

Adsorbent: granular activated carbon (GAC), Filtrasorb 400 (F400).
Single-solute equilibrium sorption capacity Qe (mmol/g), Fig. 1 / Table 1:

  PFOS  0.42  (C8, long, excluded)
  8:2 FTS 0.36 (C8 telomer, long, excluded)
  PFOA  0.33  (C8, long, excluded)
  PFBS  0.31  (C4, short)
  4:2 FTS 0.26 (C4 telomer, short)
  PFBA  0.22  (C4, short)

Short-chain subset extracted: PFBS, 4:2 FTS, PFBA. Converted to mg/g using
free-acid molar masses: PFBS 300.10, 4:2 FTS 328.14, PFBA 214.04 g/mol.

Conditions: 2 uM PFAS single solute in Milli-Q water, GAC F400, batch,
room temperature.

Writes data/processed/gac_f400_competitive.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "gac_f400_competitive.csv"

SMILES = {
    "PFBS":   "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",      # C4
    "4:2 FTS": "FC(F)(F)C(F)(F)C(F)(F)C(F)(F)CCS(=O)(=O)[O-]",     # C4 telomer sulfonate
    "PFBA":   "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                  # C4
}
CHAIN = {"PFBS": 4, "4:2 FTS": 4, "PFBA": 4}
MW = {"PFBS": 300.10, "4:2 FTS": 328.14, "PFBA": 214.04}

# single-solute equilibrium capacity Qe (mmol/g)
QE_MMOL = {"PFBS": 0.31, "4:2 FTS": 0.26, "PFBA": 0.22}

REF = "J. Hazard. Mater. 2023, 460, 132378 (GAC F400, short-chain PFAS). DOI: 10.1016/j.jhazmat.2023.132378"
REF_ID = "jhazmat2023_gac_f400"


def main() -> int:
    rows = []
    for pfas, qe_mmol in QE_MMOL.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 2.0,     # 2 uM PFAS (converted to mg/L ~0.4-0.6)
            "ph": float("nan"),               # Milli-Q water, unadjusted
            "temperature": 25.0,              # room temperature
            "contact_time": float("nan"),     # equilibrium (not explicit)
            "adsorbent_dose": float("nan"),   # batch, dose not in main text
            "adsorbent_type": "activated_carbon",
            "adsorbent_name": "GAC Filtrasorb 400 (F400)",
            "water_matrix": "ultrapure",
            "adsorption_capacity": round(qe_mmol * MW[pfas], 2),
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": f"single-solute equilibrium Qe {qe_mmol} mmol/g (= {qe_mmol*MW[pfas]:.1f} mg/g), Fig. 1/Table 1",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
