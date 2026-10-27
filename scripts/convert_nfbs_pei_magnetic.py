"""Convert ACS Omega 2024 (NFBS-PEI magnetic nanoadsorbent) short-chain PFAS data.

Source: ACS Omega 2024, 9, 49452-49462 — DOI: 10.1021/acsomega.4c07159
"Cooperative Molecular Interaction-Based Highly Efficient Capturing of
Ultrashort- and Short-Chain Emerging Per- and Polyfluoroalkyl Substances
Using Multifunctional Nanoadsorbents"

Adsorbent: NFBS-PEI-conjugated Fe3O4 magnetic nanoparticles
(nonafluorobutanesulfonyl + polyethyleneimine, cooperative
hydrophobic/fluorophilic/electrostatic interactions). Classified as
nanoadsorbent.

Data from Table 1 (Langmuir maximum capacity qm, mg/g, this work):
  PFNA  246   (C9, long-chain)
  PFBS  234   (C4, short)
  PFHxS 226   (C6, short)
  GenX  219   (C6, short)
  PFBA  202   (C4, short)
  PFPrS 186   (C3, ultrashort)
  TFA   170   (C2, ultrashort)

Conditions (main text): 1 ug/L PFAS, 1 mg/L nanoadsorbent, pH 7,
drinking water, ~30 min to reach equilibrium, room temperature.

Writes data/processed/nfbs_pei_magnetic.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "nfbs_pei_magnetic.csv"

SMILES = {
    "PFBS":  "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",                   # C4
    "PFHxS": "C(C(C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(F)F)(F)F)(C(F)(F)F)(F)F",   # C6
    "GenX":  "OC(=O)C(F)(C(F)(F)F)OC(F)(F)C(F)(F)C(F)(F)F",                    # C6
    "PFBA":  "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                              # C4
    "PFPrS": "FC(F)(F)C(F)(F)C(F)(F)S(=O)(=O)[O-]",                            # C3
    "TFA":   "C(=O)(C(F)(F)F)[O-]",                                            # C2
    "PFNA":  "C(=O)(C(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",  # C9
}
CHAIN = {"PFBS": 4, "PFHxS": 6, "GenX": 6, "PFBA": 4, "PFPrS": 3, "TFA": 2, "PFNA": 9}

CAPACITY = {
    "PFNA": 246.0,
    "PFBS": 234.0,
    "PFHxS": 226.0,
    "GenX": 219.0,
    "PFBA": 202.0,
    "PFPrS": 186.0,
    "TFA": 170.0,
}

ADS_NAME = "NFBS-PEI-Fe3O4 magnetic nanoadsorbent"
REF = "ACS Omega 2024, 9, 49452 (NFBS-PEI magnetic nanoadsorbent). DOI: 10.1021/acsomega.4c07159"
REF_ID = "acsomega2024_nfbspei"


def main() -> int:
    rows = []
    for pfas, qm in CAPACITY.items():
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 0.001,     # 1 ug/L
            "ph": 7.0,
            "temperature": 25.0,                # room temperature
            "contact_time": 30.0,               # ~30 min equilibrium
            "adsorbent_dose": 0.001,            # 1 mg/L
            "adsorbent_type": "nanoadsorbent",
            "adsorbent_name": ADS_NAME,
            "water_matrix": "drinking_water",
            "adsorption_capacity": qm,
            "removal_efficiency": float("nan"),
            "ref_ID": REF_ID,
            "ref": REF,
            "source_note": "Langmuir qm (mg/g), Table 1; 1 ug/L PFAS, 1 mg/L adsorbent, pH 7",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链(≤6): {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    print(f"容量范围: {df['adsorption_capacity'].min():.0f}~{df['adsorption_capacity'].max():.0f} mg/g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
