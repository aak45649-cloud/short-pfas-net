"""Data schema and constants for the ShortPFAS-Net project.

This module defines the canonical column names and categorical encodings used
across the data pipeline, so that experiment data and literature data are
harmonized into a single tabular format before modeling.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Target variables
# ---------------------------------------------------------------------------
TARGET_REMOVAL = "removal_efficiency"      # R (%)
TARGET_CAPACITY = "adsorption_capacity"    # q_e (mg/g), optional secondary target

# ---------------------------------------------------------------------------
# Molecular identifier
# ---------------------------------------------------------------------------
COL_SMILES = "smiles"
COL_PFAS_NAME = "pfas_name"
COL_CHAIN_LENGTH = "chain_length"          # number of perfluorinated carbon atoms
COL_IS_SHORT_CHAIN = "is_short_chain"      # bool: short-chain vs long-chain

# ---------------------------------------------------------------------------
# Process / water-matrix condition features (continuous)
# ---------------------------------------------------------------------------
CONTINUOUS_FEATURES = [
    "initial_concentration",   # C0 (mg/L)
    "ph",                      # pH
    "temperature",             # °C
    "contact_time",            # min
    "adsorbent_dose",          # g/L
]

# ---------------------------------------------------------------------------
# Categorical features and their canonical levels
# ---------------------------------------------------------------------------
CATEGORICAL_FEATURES = {
    "adsorbent_type": [
        "activated_carbon",
        "ion_exchange_resin",
        "biochar",
        "nanoadsorbent",
        "membrane",
        "other",
    ],
    "water_matrix": [
        "ultrapure",
        "surface_water",
        "groundwater",
        "wastewater",
        "drinking_water",
        "other",
    ],
}

# ---------------------------------------------------------------------------
# Short-chain PFAS reference: PFAS with <= 6 perfluorinated carbons are
# generally regarded as "short-chain" (e.g., PFBS C4, PFHxA C6).
# ---------------------------------------------------------------------------
SHORT_CHAIN_CUTOFF = 6
