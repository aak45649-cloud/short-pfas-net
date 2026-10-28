"""Convert JACS 2025 (functionalized porous polymer networks) short-chain PFAS data.

Source: J. Am. Chem. Soc. 2025, 147, 21832-21843
DOI: 10.1021/jacs.5c04689
"Functionalized Porous Polymer Networks as High-Performance PFAS Adsorbents"

Adsorbent: PPN-6 postsynthetically functionalized with charged/hydrophobic/
fluorophilic moieties. Best = PPN-6-FNDMB (fluorinated alkylammonium).

Short-chain PFAS: PFPeA (C5) and PFBS (C4). Long-chain PFOA/PFOS excluded.

Data extracted (single-solute gravimetric equilibrium capacities, Fig. 2a /
Table S9, ~1 mmol/L initial, 8 h, DI water):
- Short-chain maximum capacities (among charged PPNs):
    PFPeA: 2.3 mmol/g  (= 2.3 * 264.05 = 607.3 mg/g)
    PFBS:  3.5 mmol/g  (= 3.5 * 300.10 = 1050.4 mg/g)

Note: these are the upper bounds across the 5 charged PPNs (QA/NB/NDMB/
FNB/FNDMB), reported as "up to" in text. The per-adsorbent table (Table S9)
is in SI.

Writes data/processed/ppn6_fndmb.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "ppn6_fndmb.csv"

SMILES = {
    "PFPeA": "C(=O)(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)[O-]",      # C5
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",  # C4
}
CHAIN = {"PFPeA": 5, "PFBS": 4}
MW = {"PFPeA": 264.05, "PFBS": 300.10}

# short-chain maximum gravimetric capacities (mmol/g), text "up to"
QM_MMOL = [
    ("PFPeA", 2.3),
    ("PFBS", 3.5),
]

REF = "JACS 2025, 147, 21832-21843 (PPN-6-FNDMB, PFPeA/PFBS). DOI: 10.1021/jacs.5c04689"
REF_ID = "jacs2025_ppn6"


def _row(pfas, qm_mmol) -> dict:
    mg = qm_mmol * MW[pfas]
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": round(1.0 * MW[pfas], 1),  # ~1 mmol/L
        "ph": float("nan"),              # DI water, not reported
        "temperature": float("nan"),     # room temp
        "contact_time": 480.0,           # 8 h
        "adsorbent_dose": float("nan"),  # not reported numerically
        "adsorbent_type": "nanoadsorbent",
        "adsorbent_name": "PPN-6-FNDMB (fluorinated alkylammonium porous polymer network)",
        "water_matrix": "ultrapure",
        "adsorption_capacity": round(mg, 1),
        "removal_efficiency": float("nan"),
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": f"gravimetric equilibrium capacity {qm_mmol} mmol/g (= {mg:.1f} mg/g), ~1 mmol/L, 8 h",
    }


def main() -> int:
    rows = [_row(pfas, qm) for pfas, qm in QM_MMOL]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"容量范围: {df['adsorption_capacity'].min():.1f}~{df['adsorption_capacity'].max():.1f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
