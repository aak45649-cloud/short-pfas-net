"""Synthetic / demonstration data generation.

Generates a realistic tabular PFAS dataset so the full pipeline
(data -> graph -> model -> train -> evaluate) can be run end-to-end before
real experiment or literature data is available. The synthetic data follows
plausible physical trends (short-chain PFAS show weaker adsorption) but is
NOT scientifically calibrated — replace it with real data for publication.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Representative PFAS compounds with SMILES and perfluorinated chain length
_PFAS_LIBRARY = [
    ("PFBS", "C(F)(F)(F)S(=O)(=O)O", 4),          # perfluorobutane sulfonate
    ("PFHxS", "C(F)(F)(F)C(F)(F)S(=O)(=O)O", 6),  # perfluorohexane sulfonate
    ("PFOS", "C(F)(F)(F)C(F)(F)C(F)(F)C(F)(F)S(=O)(=O)O", 8),
    ("PFBA", "C(F)(F)(F)C(=O)O", 4),              # perfluorobutanoic acid
    ("PFHxA", "C(F)(F)(F)C(F)(F)C(=O)O", 6),      # perfluorohexanoic acid
    ("PFOA", "C(F)(F)(F)C(F)(F)C(F)(F)C(=O)O", 8),
    ("GenX", "C(C(=O)O)(C(F)(F)F)(F)F", 3),
    ("PFPeA", "C(F)(F)(F)C(F)(F)C(F)(F)C(=O)O", 7),
]

ADSOBBENTS = ["activated_carbon", "ion_exchange_resin", "biochar", "nanoadsorbent", "membrane"]
WATER = ["ultrapure", "surface_water", "groundwater", "wastewater", "drinking_water"]


def generate_demo_data(
    n_samples: int = 600,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a synthetic short/long-chain PFAS removal dataset.

    Targets ``removal_efficiency`` (%) and ``adsorption_capacity`` (mg/g) are
    generated from a physically-inspired model:
      - longer chain  -> higher removal (stronger hydrophobic interaction)
      - higher pH     -> lower removal for anionic PFAS
      - adsorbent type -> ion exchange / activated carbon outperform others
    plus substantial noise to mimic real-world scatter.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_samples):
        name, smiles, chain = _PFAS_LIBRARY[int(rng.integers(0, len(_PFAS_LIBRARY)))]
        ads = ADSOBBENTS[int(rng.integers(0, len(ADSOBBENTS)))]
        water = WATER[int(rng.integers(0, len(WATER)))]

        c0 = float(rng.uniform(0.05, 50.0))          # mg/L
        ph = float(rng.uniform(3.0, 11.0))
        temp = float(rng.uniform(15.0, 40.0))        # °C
        time = float(rng.uniform(5.0, 1440.0))       # min
        dose = float(rng.uniform(0.05, 5.0))         # g/L

        # base affinity grows with chain length; short-chain weaker
        base = 0.35 + 0.055 * chain
        ads_boost = {"ion_exchange_resin": 0.20, "activated_carbon": 0.15,
                     "nanoadsorbent": 0.10, "biochar": 0.05, "membrane": 0.12}[ads]
        ph_penalty = -0.012 * (ph - 6.0)
        water_penalty = {"ultrapure": 0.0, "surface_water": -0.08,
                         "groundwater": -0.05, "wastewater": -0.12,
                         "drinking_water": -0.03}[water]
        time_gain = 0.15 * (1.0 - np.exp(-time / 120.0))

        removal = np.clip(base + ads_boost + ph_penalty + water_penalty + time_gain
                          + rng.normal(0, 0.07), 0.02, 0.99)

        capacity = removal * c0 / max(dose, 1e-6) * 0.8 + rng.normal(0, 0.5)

        rows.append({
            "pfas_name": name,
            "smiles": smiles,
            "chain_length": chain,
            "is_short_chain": chain <= 6,
            "initial_concentration": c0,
            "ph": ph,
            "temperature": temp,
            "contact_time": time,
            "adsorbent_dose": dose,
            "adsorbent_type": ads,
            "water_matrix": water,
            "removal_efficiency": float(removal * 100),
            "adsorption_capacity": float(capacity),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_demo_data(seed=42)
    print(df.head().to_string())
    print("\nShort-chain fraction:", df["is_short_chain"].mean())
    print("Mean removal (short-chain):", df[df["is_short_chain"]]["removal_efficiency"].mean())
    print("Mean removal (long-chain):", df[~df["is_short_chain"]]["removal_efficiency"].mean())
