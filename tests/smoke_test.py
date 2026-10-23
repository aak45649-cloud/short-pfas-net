"""Standalone smoke test (no pytest dependency) — verifies the full pipeline.

Run: python tests/smoke_test.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import torch

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


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    return cond


results = []

# 1. demo data
df = generate_demo_data(n_samples=200, seed=0)
results.append(check("demo data has expected columns", "smiles" in df and "removal_efficiency" in df))
short = df[df["is_short_chain"]]["removal_efficiency"].mean()
long_ = df[~df["is_short_chain"]]["removal_efficiency"].mean()
results.append(check("short-chain removal < long-chain removal", short < long_))

# 2. molecular graph
node_f, edge_idx, edge_f, adj = smiles_to_graph("C(F)(F)(F)C(=O)O")
results.append(check("smiles -> graph node/edge dims", node_f.shape[1] == 31 and edge_idx.shape[1] > 0))

# 3. dataset + collate
ds = PFASDataset(df, target=TARGET_REMOVAL)
loader = torch.utils.data.DataLoader(ds, batch_size=16, shuffle=False, collate_fn=collate_graphs)
batch = next(iter(loader))
results.append(check("collate produces batched tensors", batch["node_features"].ndim == 3))

# 4. model forward
cond_dim = batch["conditions"].shape[1]
model = ShortPFASNet(node_feat_dim=31, edge_feat_dim=6, cond_dim=cond_dim)
out = model(batch["node_features"], batch["edge_index"], batch["edge_features"],
            batch["batch"], batch["conditions"])
results.append(check("model forward shape (B, 1)", out.shape == (16, 1)))

# 5. uncertainty
result = model.predict_with_uncertainty(
    batch["node_features"], batch["edge_index"], batch["edge_features"],
    batch["batch"], batch["conditions"], n_samples=5,
)
results.append(check("uncertainty returns mean & std", result["mean"].shape == (16, 1)))

# 6. one training step (backward)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss = torch.nn.functional.mse_loss(out, batch["target"].unsqueeze(-1))
optimizer.zero_grad()
loss.backward()
optimizer.step()
results.append(check("backward pass works", True))

# 7. metrics
m = compute_regression_metrics(np.array([1., 2., 3.]), np.array([1., 2., 3.]))
results.append(check("perfect prediction r2=1", abs(m["r2"] - 1.0) < 1e-6))

# 8. splitting
splits = random_split(df, seed=42)
total = len(splits["train"]) + len(splits["val"]) + len(splits["test"])
results.append(check("random split covers all rows", total == 200))

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
