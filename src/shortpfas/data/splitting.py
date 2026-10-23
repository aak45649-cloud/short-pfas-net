"""Data splitting strategies for transfer learning.

Supports:
- ``random``: simple stratified/random train/val/test split.
- ``pretrain_finetune``: literature (long-chain) data for pre-training,
  experiment (short-chain) data for fine-tuning and held-out evaluation.
- ``leave_one_pfas_out`` (LOPO): leave one PFAS compound out entirely, to
  measure generalization to unseen molecules (the realistic short-chain gap).
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .schema import COL_PFAS_NAME, COL_SMILES


def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.15,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """Simple random train/val/test split (no molecule-aware grouping)."""
    train, test = train_test_split(df, test_size=test_size, random_state=seed)
    val_frac = val_size / (1.0 - test_size)
    train, val = train_test_split(train, test_size=val_frac, random_state=seed)
    return {"train": train.reset_index(drop=True),
            "val": val.reset_index(drop=True),
            "test": test.reset_index(drop=True)}


def pretrain_finetune_split(
    pretrain_df: pd.DataFrame,
    finetune_df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.2,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """Split literature data for pre-training, experiment data for fine-tuning.

    ``pretrain_df``: literature / long-chain data (source domain).
    ``finetune_df``: experiment / short-chain data (target domain).
    """
    pre_train, pre_val = train_test_split(pretrain_df, test_size=val_size, random_state=seed)
    ft_train, ft_test = train_test_split(finetune_df, test_size=test_size, random_state=seed)
    ft_train, ft_val = train_test_split(ft_train, test_size=val_size, random_state=seed)
    return {
        "pretrain_train": pre_train.reset_index(drop=True),
        "pretrain_val": pre_val.reset_index(drop=True),
        "finetune_train": ft_train.reset_index(drop=True),
        "finetune_val": ft_val.reset_index(drop=True),
        "finetune_test": ft_test.reset_index(drop=True),
    }


def leave_one_pfas_out_split(
    df: pd.DataFrame,
    col: str = COL_PFAS_NAME,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """Grouped split that leaves entire PFAS compounds out of training.

    Returns a dict of {pfas_name: {"train": ..., "test": ...}} for every
    unique compound, so evaluation reflects generalization to unseen molecules.
    """
    rng = np.random.default_rng(seed)
    compounds = df[col].unique()
    folds: Dict[str, Dict[str, pd.DataFrame]] = {}
    for compound in compounds:
        test = df[df[col] == compound].reset_index(drop=True)
        train = df[df[col] != compound].reset_index(drop=True)
        # keep a small validation slice from train
        train, val = train_test_split(train, test_size=0.15, random_state=int(rng.integers(0, 2**31)))
        folds[str(compound)] = {"train": train, "val": val, "test": test}
    return folds
