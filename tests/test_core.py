"""Unit tests for data and model modules."""

import sys
import os

import numpy as np
import pandas as pd
import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from shortpfas.data import (
    PFASDataset,
    collate_graphs,
    generate_demo_data,
    random_split,
    smiles_to_graph,
)
from shortpfas.data.schema import CONTINUOUS_FEATURES, CATEGORICAL_FEATURES, TARGET_REMOVAL
from shortpfas.models import ShortPFASNet
from shortpfas.utils import compute_regression_metrics


class TestDemoData:
    def test_generate_returns_expected_columns(self):
        df = generate_demo_data(n_samples=50, seed=0)
        for col in ["smiles", "pfas_name", "chain_length", "is_short_chain",
                    "removal_efficiency", "adsorption_capacity", "adsorbent_type"]:
            assert col in df.columns
        assert len(df) == 50

    def test_short_chain_weaker_than_long_chain(self):
        df = generate_demo_data(n_samples=500, seed=0)
        short = df[df["is_short_chain"]]["removal_efficiency"].mean()
        long_ = df[~df["is_short_chain"]]["removal_efficiency"].mean()
        assert short < long_


class TestMolecularGraph:
    def test_smiles_to_graph_valid(self):
        node_f, edge_idx, edge_f, adj = smiles_to_graph("C(F)(F)(F)C(=O)O")
        assert node_f.shape[0] > 0
        assert node_f.shape[1] == 44
        assert edge_idx.shape[1] % 2 == 0  # undirected: 2x bonds
        assert adj.shape[0] == node_f.shape[0]

    def test_invalid_smiles_raises(self):
        with pytest.raises(ValueError):
            smiles_to_graph("NOT_A_VALID_SMILES_!!!")


class TestDataset:
    def test_dataset_and_collate(self):
        df = generate_demo_data(n_samples=20, seed=0)
        ds = PFASDataset(df, target=TARGET_REMOVAL)
        loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_graphs)
        batch = next(iter(loader))
        assert "node_features" in batch
        assert "conditions" in batch
        assert "target" in batch
        assert batch["node_features"].ndim == 3

    def test_condition_dimension(self):
        df = generate_demo_data(n_samples=5, seed=0)
        ds = PFASDataset(df, target=TARGET_REMOVAL)
        cond_dim = len(CONTINUOUS_FEATURES) + sum(len(v) for v in CATEGORICAL_FEATURES.values())
        assert ds[0]["conditions"].shape[0] == cond_dim


class TestModel:
    def test_forward_shape(self):
        df = generate_demo_data(n_samples=8, seed=0)
        ds = PFASDataset(df, target=TARGET_REMOVAL)
        loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_graphs)
        batch = next(iter(loader))
        cond_dim = batch["conditions"].shape[1]
        model = ShortPFASNet(node_feat_dim=44, edge_feat_dim=6, cond_dim=cond_dim)
        out = model(batch["node_features"], batch["edge_index"], batch["edge_features"],
                    batch["batch"], batch["conditions"])
        assert out.shape == (4, 1)

    def test_uncertainty(self):
        df = generate_demo_data(n_samples=4, seed=0)
        ds = PFASDataset(df, target=TARGET_REMOVAL)
        loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_graphs)
        batch = next(iter(loader))
        cond_dim = batch["conditions"].shape[1]
        model = ShortPFASNet(node_feat_dim=44, edge_feat_dim=6, cond_dim=cond_dim)
        result = model.predict_with_uncertainty(
            batch["node_features"], batch["edge_index"], batch["edge_features"],
            batch["batch"], batch["conditions"], n_samples=5,
        )
        assert result["mean"].shape == (4, 1)
        assert result["std"].shape == (4, 1)


class TestMetrics:
    def test_perfect_prediction(self):
        y = np.array([1.0, 2.0, 3.0, 4.0])
        m = compute_regression_metrics(y, y)
        assert abs(m["r2"] - 1.0) < 1e-6
        assert m["rmse"] < 1e-6


class TestSplitting:
    def test_random_split_sizes(self):
        df = generate_demo_data(n_samples=100, seed=0)
        splits = random_split(df, test_size=0.2, val_size=0.15, seed=42)
        total = len(splits["train"]) + len(splits["val"]) + len(splits["test"])
        assert total == 100
