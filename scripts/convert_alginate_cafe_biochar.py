"""Convert Environmental Research 2025 (alginate-coated Ca-Fe biochar) data.

Source: Environmental Research 285 (2025) 122395
"Study on the effect of alginate coated Ca-Fe bimetallic composite biochar
microspheres on the removal of short-chain PFAS"
DOI: 10.1016/j.envres.2025.122395

Adsorbent: CA/Ca-Fe/BC — alginate-coated Ca-Fe bimetallic composite biochar
microspheres (pomelo peel + corn stover biochar, Ca-Fe bimetallic, alginate
encapsulation).

Extracted data (abstract + text, Langmuir-Freundlich max capacity):
  - Adsorption capacity (mg/g): PFHxA 68.91, PFBS 48.95, PFBA 42.64
  - Removal efficiency (%):   PFHxA 62.65, PFBS 45.56, PFBA 37.89

Experimental conditions (isotherm / removal tests):
  - initial concentration 20 mg/L, pH 7, temperature 30 +/- 2 C,
    equilibrium time 120 min, dose PFHxA 0.2 g/L, PFBS/PFBA 0.4 g/L.

Writes data/processed/alginate_cafe_biochar.csv
(target = adsorption_capacity primary; removal_efficiency also recorded).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "alginate_cafe_biochar.csv"

# Canonical SMILES (match existing datasets)
SMILES = {
    "PFHxA": "C(=O)(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",   # C6
    "PFBS": "C(C(C(F)(F)S(=O)(=O)[O-])(F)F)(C(F)(F)F)(F)F",       # C4
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",                  # C4
}
CHAIN = {"PFHxA": 6, "PFBS": 4, "PFBA": 4}
CAPACITY = {"PFHxA": 68.91, "PFBS": 48.95, "PFBA": 42.64}
REMOVAL = {"PFHxA": 62.65, "PFBS": 45.56, "PFBA": 37.89}
DOSE = {"PFHxA": 0.2, "PFBS": 0.4, "PFBA": 0.4}

REF = "Environ. Res. 2025, 285, 122395 (alginate Ca-Fe biochar microspheres)"
REF_ID = "envres2025_alginate"


def main() -> int:
    rows = []
    for pfas in ["PFHxA", "PFBS", "PFBA"]:
        rows.append({
            "pfas_name": pfas,
            "smiles": SMILES[pfas],
            "chain_length": CHAIN[pfas],
            "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
            "initial_concentration": 20.0,        # mg/L
            "ph": 7.0,
            "temperature": 30.0,                  # 30 +/- 2 C (room temp)
            "contact_time": 120.0,                # min (isotherm equilibrium)
            "adsorbent_dose": DOSE[pfas],         # g/L (optimal dose)
            "adsorbent_type": "biochar",
            "adsorbent_name": "CA/Ca-Fe/BC",
            "water_matrix": "ultrapure",
            "adsorption_capacity": CAPACITY[pfas],
            "removal_efficiency": REMOVAL[pfas],
            "ref_ID": REF_ID,
            "ref": REF,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS: {df['pfas_name'].tolist()}")
    print(f"吸附容量 (mg/g): {df['adsorption_capacity'].tolist()}")
    print(f"去除率 (%): {df['removal_efficiency'].tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
