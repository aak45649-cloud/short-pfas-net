"""Training script for ShortPFAS-Net.

Supports two modes:
- ``single``: train on one dataset with a random split.
- ``transfer``: pre-train on literature data, then fine-tune on experiment
  (short-chain) data — the core transfer-learning workflow.

Training upgrades (validated in ``scripts/model_improvement_experiment.py``):
- early stopping on a held-out validation split (patience-based)
- cosine annealing LR schedule + weight decay
- optional descriptor prior injection (RDKit descriptors fused into the GNN)
- selectable graph encoder (GIN or GAT)
- best-checkpoint saving

Run:
    python scripts/train.py --config configs/default.yaml --mode single
    python scripts/train.py --data data/processed/all_literature.csv --mode single \
        --gnn gat --descriptors --early-stopping
"""

from __future__ import annotations

import argparse
import copy
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
from shortpfas.data.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    DESCRIPTOR_FEATURES,
    TARGET_CAPACITY,
    TARGET_REMOVAL,
)
from shortpfas.models import ShortPFASNet  # noqa: E402
from shortpfas.utils import compute_regression_metrics  # noqa: E402

RUN_DIR = os.path.join(os.path.dirname(__file__), "..", "runs", "train")


def build_dataloader(df: pd.DataFrame, target: str, batch_size: int, shuffle: bool):
    ds = PFASDataset(df, target=target)
    return torch.utils.data.DataLoader(
        ds, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_graphs
    )


def _forward(model, batch, use_desc: bool):
    desc = batch["descriptors"] if use_desc else None
    return model(
        batch["node_features"], batch["edge_index"], batch["edge_features"],
        batch["batch"], batch["conditions"], desc,
    )


def train_epoch(model, loader, optimizer, device, use_desc: bool = False):
    model.train()
    total_loss, n = 0.0, 0
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        pred = _forward(model, batch, use_desc)
        target = batch["target"].unsqueeze(-1)
        loss = nn.functional.mse_loss(pred, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * target.shape[0]
        n += target.shape[0]
    return total_loss / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, device, use_desc: bool = False):
    model.eval()
    y_true, y_pred = [], []
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        pred = _forward(model, batch, use_desc)
        y_pred.append(pred[:, 0].cpu().numpy())
        y_true.append(batch["target"].cpu().numpy())
    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)
    return compute_regression_metrics(y_true, y_pred)


def fit(
    model,
    train_loader,
    val_loader,
    device,
    epochs: int,
    lr: float,
    use_desc: bool,
    early_stopping: bool = False,
    patience: int = 20,
    weight_decay: float = 1e-4,
    tag: str = "",
):
    """Train with optional early stopping + cosine annealing; return best model."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1))

    best_rmse, best_state, best_epoch, wait = float("inf"), None, 0, 0
    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, train_loader, optimizer, device, use_desc)
        if val_loader is not None:
            m = evaluate(model, val_loader, device, use_desc)
            scheduler.step()
            improved = m["rmse"] < best_rmse - 1e-6
            if improved:
                best_rmse, best_epoch, wait = m["rmse"], epoch, 0
                best_state = copy.deepcopy(model.state_dict())
            else:
                wait += 1
            if (epoch % 5 == 0) or epoch == 1:
                print(f"[{tag}] epoch {epoch}/{epochs} loss={loss:.4f} "
                      f"val_r2={m['r2']:.3f} val_rmse={m['rmse']:.3f}")
            if early_stopping and wait >= patience:
                print(f"[{tag}] early stop at epoch {epoch} (best {best_epoch}, "
                      f"val_rmse={best_rmse:.3f})")
                break
        else:
            scheduler.step()
            if (epoch % 5 == 0) or epoch == 1:
                print(f"[{tag}] epoch {epoch}/{epochs} loss={loss:.4f}")

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_epoch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--mode", choices=["single", "transfer"], default="single")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--data", default=None, help="path to CSV; uses demo data if omitted")
    parser.add_argument(
        "--target", choices=[TARGET_REMOVAL, TARGET_CAPACITY], default=TARGET_REMOVAL,
        help="target column to predict (removal %% or adsorption capacity)",
    )
    parser.add_argument("--gnn", choices=["gin", "gat"], default="gin",
                        help="graph encoder type (GAT performed best on short-chain subsets)")
    parser.add_argument("--descriptors", action="store_true",
                        help="inject RDKit descriptor priors into the GNN embedding")
    parser.add_argument("--early-stopping", action="store_true",
                        help="stop when validation RMSE stops improving")
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--save-model", action="store_true",
                        help="save the best checkpoint to runs/train/")
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
        # Drop rows without the selected target (literature tables often mix
        # removal-only and capacity-only records).
        if args.target in df.columns:
            before = len(df)
            df = df[df[args.target].notna()].reset_index(drop=True)
            if len(df) < before:
                print(f"Dropped {before - len(df)} rows with missing {args.target} "
                      f"({len(df)} remain)")
    else:
        print("No --data provided; using synthetic demo data.")
        df = generate_demo_data()

    cond_dim = len(CONTINUOUS_FEATURES) + sum(
        len(v) for v in CATEGORICAL_FEATURES.values()
    )
    node_feat_dim, edge_feat_dim = 31, 6
    descriptor_dim = len(DESCRIPTOR_FEATURES) if args.descriptors else 0

    def new_model():
        return ShortPFASNet(
            node_feat_dim, edge_feat_dim, cond_dim, hidden_dim=hidden_dim,
            gnn_type=args.gnn, descriptor_dim=descriptor_dim,
        ).to(device)

    def maybe_save(model, name):
        if args.save_model:
            os.makedirs(RUN_DIR, exist_ok=True)
            path = os.path.join(RUN_DIR, f"{name}.pt")
            torch.save(model.state_dict(), path)
            print(f"Saved checkpoint: {path}")

    if args.mode == "single":
        splits = random_split(df)
        loaders = {
            k: build_dataloader(v, args.target, batch_size, shuffle=(k == "train"))
            for k, v in splits.items()
        }
        model = new_model()
        model, best_ep = fit(
            model, loaders["train"], loaders["val"], device, epochs, lr,
            args.descriptors, args.early_stopping, args.patience, args.weight_decay,
            tag=f"single/{args.gnn}",
        )
        test_metrics = evaluate(model, loaders["test"], device, args.descriptors)
        print(f"Test metrics (best epoch {best_ep}):", test_metrics)
        maybe_save(model, f"single_{args.gnn}_{args.target}")

    else:  # transfer
        # split literature vs experiment by chain length for demonstration
        literature = df[~df["is_short_chain"]]
        experiment = df[df["is_short_chain"]]
        splits = pretrain_finetune_split(literature, experiment)
        model = new_model()

        pre_train_loader = build_dataloader(splits["pretrain_train"], args.target, batch_size, shuffle=True)
        pre_val_loader = build_dataloader(splits["pretrain_val"], args.target, batch_size, shuffle=False)

        print(f"== Pre-training on literature data ({len(splits['pretrain_train'])} samples) ==")
        model, _ = fit(
            model, pre_train_loader, pre_val_loader, device, epochs, lr,
            args.descriptors, args.early_stopping, args.patience, args.weight_decay,
            tag="pretrain",
        )

        ft_train_loader = build_dataloader(splits["finetune_train"], args.target, batch_size, shuffle=True)
        ft_val_loader = build_dataloader(splits["finetune_val"], args.target, batch_size, shuffle=False)
        ft_test_loader = build_dataloader(splits["finetune_test"], args.target, batch_size, shuffle=False)

        print(f"== Fine-tuning on short-chain data ({len(splits['finetune_train'])} samples) ==")
        ft_epochs = max(1, epochs // 2)
        model, _ = fit(
            model, ft_train_loader, ft_val_loader, device, ft_epochs, lr * 0.1,
            args.descriptors, args.early_stopping, args.patience, args.weight_decay,
            tag="finetune",
        )

        ft_metrics = evaluate(model, ft_test_loader, device, args.descriptors)
        print("Short-chain fine-tuned test metrics:", ft_metrics)
        maybe_save(model, f"transfer_{args.gnn}_{args.target}")


if __name__ == "__main__":
    main()
