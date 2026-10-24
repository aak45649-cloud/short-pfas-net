"""Training script for ShortPFAS-Net.

Supports two modes:
- ``single``: train on one dataset with a random split.
- ``transfer``: pre-train on literature data, then fine-tune on experiment
  (short-chain) data — the core transfer-learning workflow.

Run:
    python scripts/train.py --config configs/default.yaml --mode single
    python scripts/train.py --config configs/default.yaml --mode transfer
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from shortpfas.data import (  # noqa: E402
    PFASDataset,
    collate_graphs,
    generate_demo_data,
    pretrain_finetune_split,
    random_split,
)
from shortpfas.data.schema import CONTINUOUS_FEATURES, TARGET_CAPACITY, TARGET_REMOVAL  # noqa: E402
from shortpfas.models import ShortPFASNet  # noqa: E402
from shortpfas.utils import compute_regression_metrics  # noqa: E402


def build_dataloader(df: pd.DataFrame, target: str, batch_size: int, shuffle: bool):
    ds = PFASDataset(df, target=target)
    return torch.utils.data.DataLoader(
        ds, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_graphs
    )


def train_epoch(model, loader, optimizer, device, target_idx=0):
    model.train()
    total_loss, n = 0.0, 0
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        pred = model(
            batch["node_features"], batch["edge_index"], batch["edge_features"],
            batch["batch"], batch["conditions"],
        )
        target = batch["target"].unsqueeze(-1)
        loss = nn.functional.mse_loss(pred, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * target.shape[0]
        n += target.shape[0]
    return total_loss / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        pred = model(
            batch["node_features"], batch["edge_index"], batch["edge_features"],
            batch["batch"], batch["conditions"],
        )
        y_pred.append(pred[:, 0].cpu().numpy())
        y_true.append(batch["target"].cpu().numpy())
    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)
    return compute_regression_metrics(y_true, y_pred)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--mode", choices=["single", "transfer"], default="single")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--data", default=None, help="path to CSV; uses demo data if omitted")
    parser.add_argument(
        "--target", choices=[TARGET_REMOVAL, TARGET_CAPACITY], default=TARGET_REMOVAL,
        help="target column to predict (removal % or adsorption capacity)",
    )
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(args.config) as f:
        cfg = yaml.safe_load(f) or {}
    epochs = args.epochs or cfg.get("training", {}).get("epochs", 30)
    batch_size = cfg.get("training", {}).get("batch_size", 32)
    lr = cfg.get("training", {}).get("learning_rate", 1e-3)
    hidden_dim = cfg.get("model", {}).get("hidden_dim", 64)

    # Load data (demo fallback)
    if args.data:
        df = pd.read_csv(args.data)
    else:
        print("No --data provided; using synthetic demo data.")
        df = generate_demo_data()

    cond_dim = len(CONTINUOUS_FEATURES) + sum(
        len(v) for v in
        __import__("shortpfas.data.schema", fromlist=["CATEGORICAL_FEATURES"]).CATEGORICAL_FEATURES.values()
    )
    node_feat_dim, edge_feat_dim = 31, 6

    if args.mode == "single":
        splits = random_split(df)
        loaders = {
            k: build_dataloader(v, args.target, batch_size, shuffle=(k == "train"))
            for k, v in splits.items()
        }
        model = ShortPFASNet(node_feat_dim, edge_feat_dim, cond_dim, hidden_dim=hidden_dim).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        for epoch in range(epochs):
            loss = train_epoch(model, loaders["train"], optimizer, device)
            if (epoch + 1) % 5 == 0 or epoch == 0:
                m = evaluate(model, loaders["val"], device)
                print(f"[single] epoch {epoch+1}/{epochs} loss={loss:.4f} val_r2={m['r2']:.3f} val_rmse={m['rmse']:.3f}")
        test_metrics = evaluate(model, loaders["test"], device)
        print("Test metrics:", test_metrics)

    else:  # transfer
        # split literature vs experiment by chain length for demonstration
        literature = df[~df["is_short_chain"]]
        experiment = df[df["is_short_chain"]]
        splits = pretrain_finetune_split(literature, experiment)
        model = ShortPFASNet(node_feat_dim, edge_feat_dim, cond_dim, hidden_dim=hidden_dim).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        pre_train_loader = build_dataloader(splits["pretrain_train"], args.target, batch_size, shuffle=True)
        pre_val_loader = build_dataloader(splits["pretrain_val"], args.target, batch_size, shuffle=False)

        print(f"== Pre-training on literature data ({len(splits['pretrain_train'])} samples) ==")
        for epoch in range(epochs):
            loss = train_epoch(model, pre_train_loader, optimizer, device)
            if (epoch + 1) % 5 == 0 or epoch == 0:
                m = evaluate(model, pre_val_loader, device)
                print(f"[pretrain] epoch {epoch+1}/{epochs} loss={loss:.4f} val_r2={m['r2']:.3f}")

        ft_train_loader = build_dataloader(splits["finetune_train"], args.target, batch_size, shuffle=True)
        ft_test_loader = build_dataloader(splits["finetune_test"], args.target, batch_size, shuffle=False)

        print(f"== Fine-tuning on short-chain data ({len(splits['finetune_train'])} samples) ==")
        ft_epochs = max(1, epochs // 2)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr * 0.1)
        for epoch in range(ft_epochs):
            loss = train_epoch(model, ft_train_loader, optimizer, device)
            if (epoch + 1) % 5 == 0 or epoch == 0:
                m = evaluate(model, ft_test_loader, device)
                print(f"[finetune] epoch {epoch+1}/{ft_epochs} loss={loss:.4f} test_r2={m['r2']:.3f}")

        ft_metrics = evaluate(model, ft_test_loader, device)
        print("Short-chain fine-tuned test metrics:", ft_metrics)


if __name__ == "__main__":
    main()
