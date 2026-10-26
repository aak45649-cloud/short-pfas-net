"""Convert Clean Technologies 2026 (cleantechnol8010021) modified-zeolite PFAS
removal data to the ShortPFAS-Net schema.

Source: Clean Technol. 2026, 8, 21 (10.3390/cleantechnol8010021)
"Modified Zeolites as Alternative Adsorbents for PFAS Removal:
A Comparative Study with Granular Activated Carbon"

This study is exceptionally valuable because it reports REMOVAL EFFICIENCY for
the short-chain PFBA (C4) across many surface-modified clinoptilolite zeolites
and two GAC benchmarks — a rich source of "short-chain PFAS is hard to remove"
negative/positive examples, which is exactly the data scarcity the model
struggles with.

Experimental conditions (fixed for all batch tests):
  - contact_time = 1 h (60 min), room temperature ~21 +/- 2 C
  - Milli-Q water (ultrapure), no pH adjustment
  - single-solute tests: PFBA (100 ug/L) and PFOA (100 ug/L)
  - high-conc screening: PFOA 1 mg/L
  - mixed-solute: PFBA + PFOA + PFTDA each 100 ug/L (total 300 ug/L)
  - adsorbent dose: NOT reported numerically in the main text (see note below)

Only data points with an EXACT percentage stated in the text are extracted.
Ranges (e.g. "17-22%") are recorded at the midpoint with a source_note, except
where a single explicit value is given.

Target = removal_efficiency (%). Adsorbent type: zeolites -> "other" (modified
mineral adsorbent; the schema has no "zeolite" level), GAC -> "activated_carbon".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data.schema import SHORT_CHAIN_CUTOFF  # noqa: E402

OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "modified_zeolite.csv"

# Canonical SMILES matching existing datasets
SMILES = {
    "PFBA": "C(=O)(C(C(C(F)(F)F)(F)F)(F)F)[O-]",   # C4, short
    "PFOA": "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)[O-]",  # C8, long
}
CHAIN = {"PFBA": 4, "PFOA": 8}

REF = "Clean Technol. 2026, 8, 21 (modified clinoptilolite zeolite vs GAC)"
REF_ID = "cleantechnol2026"

# ---- experimental conditions (common) ----
ROOM_TEMP = 21.0          # ~21 +/- 2 C
CONTACT_TIME = 60.0       # 1 h


def _row(pfas, conc, matrix, adsorbent, a_type, removal, note=""):
    return {
        "pfas_name": pfas,
        "smiles": SMILES[pfas],
        "chain_length": CHAIN[pfas],
        "is_short_chain": CHAIN[pfas] <= SHORT_CHAIN_CUTOFF,
        "initial_concentration": conc,   # mg/L
        "ph": float("nan"),              # no pH adjustment reported
        "temperature": ROOM_TEMP,
        "contact_time": CONTACT_TIME,
        "adsorbent_dose": float("nan"),  # not reported numerically in main text
        "adsorbent_type": a_type,
        "adsorbent_name": adsorbent,
        "water_matrix": matrix,
        "removal_efficiency": removal,
        "ref_ID": REF_ID,
        "ref": REF,
        "source_note": note,
    }


def main() -> int:
    rows = []

    # ------------------------------------------------------------------
    # 3.1  High-concentration PFOA (1 mg/L) screening — single solute
    # ------------------------------------------------------------------
    conc_hi = 1.0  # 1 ppm = 1 mg/L
    hi = [
        ("AZ (raw zeolite)", "zeolite", 4.0, "raw clinoptilolite"),
        ("GAC1 (coconut)", "activated_carbon", 84.0, "coconut-based GAC"),
        ("GAC2 (coal)", "activated_carbon", 97.0, "coal-based GAC"),
        ("AZ-D:A(1:1)-AW", "zeolite", 93.0, "APTES+DTMS co-grafted 1:1, acid-washed"),
        ("AZ-D:A(1:3)-AW", "zeolite", 90.0, "DTMS:APTES 1:3, acid-washed"),
        ("AZ-D:A(3:1)-AW", "zeolite", 78.0, "DTMS:APTES 3:1, acid-washed"),
        ("AZ-D:A(1:1)-NW", "zeolite", 81.0, "APTES+DTMS co-grafted 1:1, normal-washed"),
        ("AZ-DTMS-NW", "zeolite", 6.0, "DTMS-only, normal-washed"),
        ("AZ-DTMS-AW", "zeolite", 43.0, "DTMS-only, acid-washed"),
        ("AZ-APTES-NW (AZ-A-NW)", "zeolite", 14.0, "APTES-only, normal-washed"),
        ("AZ-A-AW", "zeolite", 58.0, "APTES-only, acid-washed"),
        ("AZ-D+A-NW (physical 1:1)", "zeolite", 35.0, "physical mixture, normal-washed"),
        ("AZ-D+A-AW (physical 1:1)", "zeolite", 41.0, "physical mixture, acid-washed"),
        ("AZ-La-NW", "zeolite", 58.0, "La-exchanged, normal-washed"),
        ("AZ-Fe-NW", "zeolite", 15.0, "Fe-exchanged, normal-washed"),
        ("AZ-Fe-AW", "zeolite", 48.0, "Fe-exchanged, acid-washed"),
        ("AZ-GO", "zeolite", 11.0, "graphene-oxide-coated"),
    ]
    for name, a_type, rem, note in hi:
        rows.append(_row("PFOA", conc_hi, "ultrapure", name, a_type, rem, note))

    # ------------------------------------------------------------------
    # 3.2  100 ug/L single-solute (PFBA + PFOA) — 9 adsorbents
    # ------------------------------------------------------------------
    conc_lo = 0.1  # 100 ug/L = 0.1 mg/L

    # PFBA (short-chain) single solute — exact values stated in text
    pfba_single = [
        ("AZ (raw zeolite)", "zeolite", 17.0, "raw clinoptilolite"),
        ("AZ-Fe-NW", "zeolite", 17.0, "Fe-exchanged"),
        ("AZ-La-NW", "zeolite", 20.0, "La-exchanged"),
        ("AZ-APTES-NW", "zeolite", 19.5, "APTES, reported 17-22% (midpoint)"),
        ("AZ-D:A(x:y)-NW", "zeolite", 19.5, "co-grafted, reported 17-22% (midpoint)"),
        ("GAC2 (coal)", "activated_carbon", 98.0, "coal-based GAC"),
    ]
    for name, a_type, rem, note in pfba_single:
        rows.append(_row("PFBA", conc_lo, "ultrapure", name, a_type, rem, note))

    # PFOA single solute — exact values
    pfoa_single = [
        ("GAC2 (coal)", "activated_carbon", 100.0, "essentially complete removal"),
        ("AZ (raw zeolite)", "zeolite", 22.0, "raw clinoptilolite"),
        ("AZ-La-NW", "zeolite", 44.0, "La-exchanged"),
        ("AZ-Fe-NW", "zeolite", 36.0, "Fe-exchanged"),
        ("AZ-APTES-NW", "zeolite", 100.0, "APTES, 100% at 100 ppb"),
        ("AZ-DTMS-NW", "zeolite", 100.0, "DTMS, 100% at 100 ppb"),
        ("AZ-D:A(x:y)-NW", "zeolite", 100.0, "dual-silane, 100% at 100 ppb"),
    ]
    for name, a_type, rem, note in pfoa_single:
        rows.append(_row("PFOA", conc_lo, "ultrapure", name, a_type, rem, note))

    # ------------------------------------------------------------------
    # 3.3  Mixed solute (PFBA + PFOA + PFTDA, each 100 ug/L)
    # ------------------------------------------------------------------
    # PFBA in mixture — exact values
    pfba_mix = [
        ("AZ-Fe-NW", "zeolite", 23.0, "mixed solute"),
        ("AZ-La-NW", "zeolite", 24.0, "mixed solute"),
        ("AZ-DTMS-NW", "zeolite", 18.0, "mixed solute"),
        ("AZ-APTES-NW", "zeolite", 19.0, "mixed solute"),
        ("AZ-D:A(x:y)-NW", "zeolite", 21.5, "mixed solute, 21-22% (midpoint)"),
        ("GAC2 (coal)", "activated_carbon", 98.0, "mixed solute, coal-based GAC"),
    ]
    for name, a_type, rem, note in pfba_mix:
        rows.append(_row("PFBA", conc_lo, "ultrapure", name, a_type, rem, note))

    # PFOA in mixture — exact values
    pfoa_mix = [
        ("GAC2 (coal)", "activated_carbon", 100.0, "mixed solute"),
        ("AZ (raw zeolite)", "zeolite", 24.0, "mixed solute"),
        ("AZ-DTMS-NW", "zeolite", 30.0, "mixed solute"),
        ("AZ-APTES-NW", "zeolite", 73.0, "mixed solute"),
        ("AZ-D:A(x:y)-NW", "zeolite", 72.5, "mixed solute, 70-75% (midpoint)"),
        ("AZ-La-NW", "zeolite", 43.0, "mixed solute"),
        ("AZ-Fe-NW", "zeolite", 33.0, "mixed solute"),
    ]
    for name, a_type, rem, note in pfoa_mix:
        rows.append(_row("PFOA", conc_lo, "ultrapure", name, a_type, rem, note))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"转换完成: {OUT_CSV}")
    print(f"总样本数: {len(df)}")
    print(f"短链样本: {int(df['is_short_chain'].sum())} / {len(df)}")
    print(f"PFAS 分布: {df['pfas_name'].value_counts().to_dict()}")
    print(f"吸附剂类型: {df['adsorbent_type'].value_counts().to_dict()}")
    print(f"去除率范围: {df['removal_efficiency'].min():.0f}~{df['removal_efficiency'].max():.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
