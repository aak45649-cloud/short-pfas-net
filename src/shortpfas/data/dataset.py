"""PyTorch Dataset for the multi-modal PFAS model.

Each sample is a (molecular graph, process conditions) pair with an optional
target. The dataset converts SMILES to graph tensors on the fly (or uses a
precomputed cache) and standardizes continuous features.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from .molecular_graph import smiles_to_graph
from .schema import CATEGORICAL_FEATURES, CONTINUOUS_FEATURES


class PFASDataset(Dataset):
    """Multi-modal dataset combining molecular graphs and process conditions."""

    def __init__(
        self,
        df: pd.DataFrame,
        target: str,
        continuous_features: Optional[List[str]] = None,
        categorical_features: Optional[Dict[str, List[str]]] = None,
        precomputed_graphs: Optional[Dict[str, tuple]] = None,
    ):
        self.df = df.reset_index(drop=True)
        self.target = target
        self.continuous_features = continuous_features or CONTINUOUS_FEATURES
        self.categorical_features = categorical_features or CATEGORICAL_FEATURES
        self.precomputed_graphs = precomputed_graphs or {}

        # Precompute continuous feature statistics for standardization
        self._cont_mean = {
            f: float(self.df[f].mean()) for f in self.continuous_features if f in self.df
        }
        self._cont_std = {
            f: float(self.df[f].std()) for f in self.continuous_features if f in self.df
        }

        # Build category -> index mapping
        self._cat_maps: Dict[str, Dict[str, int]] = {}
        for feat, levels in self.categorical_features.items():
            self._cat_maps[feat] = {level: i for i, level in enumerate(levels)}

    def __len__(self) -> int:
        return len(self.df)

    def _get_graph(self, smiles: str) -> tuple:
        if smiles in self.precomputed_graphs:
            return self.precomputed_graphs[smiles]
        node_f, edge_idx, edge_f, adj = smiles_to_graph(smiles)
        self.precomputed_graphs[smiles] = (node_f, edge_idx, edge_f, adj)
        return node_f, edge_idx, edge_f, adj

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        row = self.df.iloc[idx]
        smiles = row["smiles"]

        node_f, edge_idx, edge_f, _ = self._get_graph(smiles)

        # Continuous conditions -> standardized vector
        cont = []
        for f in self.continuous_features:
            if f in row:
                mu = self._cont_mean.get(f, 0.0)
                sd = self._cont_std.get(f, 1.0) or 1.0
                cont.append((float(row[f]) - mu) / sd)
            else:
                cont.append(0.0)

        # Categorical conditions -> one-hot vector
        cat = []
        for feat, levels in self.categorical_features.items():
            one_hot = np.zeros(len(levels), dtype=np.float32)
            if feat in row and row[feat] in self._cat_maps[feat]:
                one_hot[self._cat_maps[feat][row[feat]]] = 1.0
            cat.extend(one_hot)

        conditions = np.concatenate([np.asarray(cont, dtype=np.float32), np.asarray(cat)])

        sample = {
            "node_features": torch.tensor(node_f, dtype=torch.float32),
            "edge_index": torch.tensor(edge_idx, dtype=torch.long),
            "edge_features": torch.tensor(edge_f, dtype=torch.float32),
            "conditions": torch.tensor(conditions, dtype=torch.float32),
        }
        if self.target in row and not pd.isna(row[self.target]):
            sample["target"] = torch.tensor(float(row[self.target]), dtype=torch.float32)
        return sample


def collate_graphs(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """Collate a batch of variable-size molecular graphs into a batched tensor.

    Small molecules (PFAS) are small, so we simply pad node features to the
    max node count in the batch and build a block-diagonal edge index.
    """
    max_nodes = max(s["node_features"].shape[0] for s in batch)
    n_node_feat = batch[0]["node_features"].shape[1]
    n_edge_feat = batch[0]["edge_features"].shape[1]

    node_list, edge_list, edge_feat_list, cond_list, target_list = [], [], [], [], []
    node_offsets = []
    offset = 0
    has_target = all("target" in s for s in batch)

    for s in batch:
        n = s["node_features"].shape[0]
        padded = torch.zeros((max_nodes, n_node_feat), dtype=torch.float32)
        padded[:n] = s["node_features"]
        node_list.append(padded)

        ei = s["edge_index"] + offset  # shift node indices
        edge_list.append(ei)
        edge_feat_list.append(s["edge_features"])
        node_offsets.append(offset)
        offset += n

        cond_list.append(s["conditions"])
        if has_target:
            target_list.append(s["target"])

    node_tensor = torch.stack(node_list, dim=0)  # (B, max_nodes, F)
    edge_tensor = torch.cat(edge_list, dim=1) if edge_list else torch.empty((2, 0), dtype=torch.long)
    edge_feat_tensor = torch.cat(edge_feat_list, dim=0) if edge_feat_list else torch.empty((0, n_edge_feat), dtype=torch.float32)
    cond_tensor = torch.stack(cond_list, dim=0)
    batch_idx = torch.arange(len(batch), dtype=torch.long).unsqueeze(1).repeat(1, max_nodes).reshape(-1)

    out = {
        "node_features": node_tensor,
        "edge_index": edge_tensor,
        "edge_features": edge_feat_tensor,
        "conditions": cond_tensor,
        "batch": batch_idx,
        "node_offsets": torch.tensor(node_offsets, dtype=torch.long),
    }
    if has_target:
        out["target"] = torch.stack(target_list, dim=0)
    return out
