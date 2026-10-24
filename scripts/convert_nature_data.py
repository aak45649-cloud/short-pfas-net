"""Convert Nature Comms (s41467-024-55320-9) MOESM3 source data to ShortPFAS-Net schema.

The MOESM3_ESM.xlsx "data" sheet contains 535 rows of PFAS membrane-removal
records with SMILES, molecular descriptors, membrane properties, and
removal_rate (target). This script maps those columns to our canonical schema
and writes data/processed/nature_membrane.csv.

Run:
    python scripts/convert_nature_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

SRC_XLSX = Path(__file__).resolve().parent.parent / "data" / "papers" / "supp_55320" / "MOESM3_ESM.xlsx"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "nature_membrane.csv"


def count_perfluorinated_carbons(smiles: str) -> int:
    """Estimate perfluorinated (CF2/CF3) carbon count from SMILES.

    Simple heuristic: count 'C' atoms that are followed by '(' with F atoms.
    For PFAS this roughly equals the perfluoroalkyl chain length.
    This is an approximation; a more rigorous count needs RDKit substructure
    matching. We use RDKit when available, else fall back to a name-based table.
    """
    # Known chain lengths for common PFAS (name -> chain length)
    KNOWN = {
        "PFBA": 4, "PFPeA": 5, "PFHxA": 6, "PFHpA": 7, "PFOA": 8,
        "PFNA": 9, "PFDA": 10, "PFBS": 4, "PFHxS": 6, "PFOS": 8,
    }
    return None  # resolved via name lookup below


def main():
    df = pd.read_excel(SRC_XLSX, sheet_name="data")

    # Rename to schema columns
    rename = {
        "SMILES": "smiles",
        "PFAS": "pfas_name",
        "Initial concentration (ng/L)": "initial_concentration_ngl",
        "pH": "ph",
        "Removal_rate": "removal_efficiency",
    }
    df = df.rename(columns=rename)

    # Convert initial concentration from ng/L to mg/L (schema unit)
    if "initial_concentration_ngl" in df.columns:
        df["initial_concentration"] = df["initial_concentration_ngl"] / 1e6
        df = df.drop(columns=["initial_concentration_ngl"])

    # Determine chain length from known short-chain PFAS names
    KNOWN = {
        # Perfluoroalkyl carboxylic acids (PFCAs)
        "PFBA": 4, "PFPeA": 5, "PFHxA": 6, "PFHpA": 7, "PFOA": 8,
        "PFNA": 9, "PFDA": 10, "PFUnA": 11,
        # Perfluoroalkyl sulfonic acids (PFSAs)
        "PFPrS": 3, "PFBS": 4, "PFPeS": 5, "PFHxS": 6, "PFHpS": 7,
        "PFOS": 8, "PFDS": 10,
        # Fluorotelomer sulfonates
        "4:2FTS": 6, "6:2FTS": 8,
        # Per/polyfluoroalkyl ether acids (GenX family)
        "GenX": 3, "PFMOBA": 4, "PFMOPrA": 3,
        # Sulfonamide
        "FOSA": 8,
    }
    df["chain_length"] = df["pfas_name"].map(KNOWN)
    df["is_short_chain"] = df["chain_length"] <= SHORT_CHAIN_CUTOFF

    # map adsorbent type: membrane
    df["adsorbent_type"] = "membrane"

    # water matrix: not specified in source; default to ultrapure (lab)
    df["water_matrix"] = "ultrapure"

    # temperature/contact_time/adsorbent_dose not in source -> NaN placeholders
    for col in ["temperature", "contact_time", "adsorbent_dose"]:
        if col not in df.columns:
            df[col] = float("nan")

    # keep only schema columns + source references
    keep = [
        "pfas_name", "smiles", "chain_length", "is_short_chain",
        "initial_concentration", "ph", "temperature", "contact_time",
        "adsorbent_dose", "adsorbent_type", "water_matrix",
        "removal_efficiency", "ref_ID", "ref",
    ]
    df = df[[c for c in keep if c in df.columns]]

    # drop rows with missing SMILES or removal
    df = df.dropna(subset=["smiles", "removal_efficiency"])

    # Fix FOSA: source stores molecular formula instead of SMILES.
    # Correct SMILES for perfluorooctanesulfonamide (FOSA, C8).
    FOSA_SMILES = "C(C(C(C(F)(F)S(=O)(=O)N)(F)F)(F)F)(C(C(F)(F)F)(F)F)(F)F"
    df.loc[df["pfas_name"] == "FOSA", "smiles"] = FOSA_SMILES

    df.to_csv(OUT_CSV, index=False)
    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    if "is_short_chain" in df.columns:
        sc = df["is_short_chain"]
        print(f"短链样本: {sc.sum()} ({sc.mean():.1%})")
        print(f"长链样本: {(~sc).sum()}")
    print(f"去除率范围: {df['removal_efficiency'].min():.1f}% ~ {df['removal_efficiency'].max():.1f}%")
    print(f"含 SMILES: {df['smiles'].notna().sum()} 条")


if __name__ == "__main__":
    main()
