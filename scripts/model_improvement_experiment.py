"""Model improvement experiment: early stopping, cosine annealing, GAT, ensemble.

Motivation (from descriptor_vs_gnn_all.py):
  GNN + descriptor prior reaches R2 = 0.41 (short-chain) / 0.47 (full corpus),
  but is trained with a fixed 80 epochs and no validation-based stopping, so
  the GNN branch still shows large seed variance (R2 std ~ 0.22-0.37).

This script tests four training/architecture upgrades on the same 25% held-out
split and the same 5 seeds, isolating the effect of each change:

  1. gin_desc_fixed  -- baseline: GIN + descriptor, fixed 80 epochs (current)
  2. gin_desc_es     -- GIN + descriptor + early stopping + cosine annealing
                        + weight decay
  3. gat_desc_es     -- GAT + descriptor + early stopping (architecture swap)
  4. gin_desc_ens    -- GIN + descriptor + early stopping + 3-seed ensemble
                        (variance reduction by averaging)

Scenarios: short-chain + removal (primary), full corpus + removal (reference).

Run:
    python scripts/model_improvement_experiment.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shortpfas.data import PFASDataset, collate_graphs  # noqa: E402
from shortpfas.data.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    DESCRIPTOR_FEATURES,
    TARGET_REMOVAL,
)
from shortpfas.models import ShortPFASNet  # noqa: E402
from shortpfas.utils import compute_regression_metrics  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "all_literature.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "runs" / "transfer"

SEEDS = [42, 123, 2024, 7, 999]
NODE_FEAT_DIM, EDGE_FEAT_DIM = 31, 6
BATCH_SIZE = 32
LR = 1e-3
FIXED_EPOCHS = 80
MAX_EPOCHS = 250
PATIENCE = 20
VAL_FRAC = 0.15
WEIGHT_DECAY = 1e-4

SCENARIOS = {
    "short_chain": "Short-chain + removal",
    "full": "Full corpus + removal",
}


def cond_dim() -> int:
    return len(CONTINUOUS_FEATURES) + sum(len(v) for v in CATEGORICAL_FEATURES.values())


def build_loader(df, target, batch_size, shuffle):
    ds = PFASDataset(df, target=target)
    return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=shuffle,
                                       collate_fn=collate_graphs)


def _to_device(b, device):
    return {k: v.to(device) for k, v in b.items() if isinstance(v, torch.Tensor)}


def model_predict(model, loader, device, use_desc):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for b in loader:
            b = _to_device(b, device)
            desc = b["descriptors"] if use_desc else None
            pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                         b["batch"], b["conditions"], desc)
            y_pred.append(pred[:, 0].cpu().numpy())
            y_true.append(b["target"].cpu().numpy())
    return np.concatenate(y_true), np.concatenate(y_pred)


def model_fit_fixed(model, loader, device, use_desc):
    """Baseline: fixed number of epochs, no validation."""
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    model.train()
    for _ in range(FIXED_EPOCHS):
        for b in loader:
            b = _to_device(b, device)
            desc = b["descriptors"] if use_desc else None
            pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                         b["batch"], b["conditions"], desc)
            loss = nn.functional.mse_loss(pred, b["target"].unsqueeze(-1))
            opt.zero_grad(); loss.backward(); opt.step()
    return model, FIXED_EPOCHS


def model_fit_early_stopping(model, train_loader, val_loader, device, use_desc):
    """Early stopping + cosine annealing + weight decay."""
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=MAX_EPOCHS)
    best_val, best_state, best_epoch, wait = float("inf"), None, 0, 0

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        for b in train_loader:
            b = _to_device(b, device)
            desc = b["descriptors"] if use_desc else None
            pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                         b["batch"], b["conditions"], desc)
            loss = nn.functional.mse_loss(pred, b["target"].unsqueeze(-1))
            opt.zero_grad(); loss.backward(); opt.step()

        # validation loss
        model.eval()
        total, n = 0.0, 0
        with torch.no_grad():
            for b in val_loader:
                b = _to_device(b, device)
                desc = b["descriptors"] if use_desc else None
                pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                             b["batch"], b["conditions"], desc)
                total += nn.functional.mse_loss(pred, b["target"].unsqueeze(-1),
                                                reduction="sum").item()
                n += b["target"].numel()
        val_loss = total / max(n, 1)
        sched.step()

        if val_loss < best_val - 1e-6:
            best_val, best_epoch, wait = val_loss, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            wait += 1
            if wait >= PATIENCE:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_epoch


def make_model(gnn_type: str, use_desc: bool, seed: int, device):
    torch.manual_seed(seed)
    return ShortPFASNet(
        NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64,
        gnn_type=gnn_type,
        descriptor_dim=len(DESCRIPTOR_FEATURES) if use_desc else 0,
    ).to(device)


def split_train_val(train_df: pd.DataFrame, seed: int):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(train_df))
    n_val = max(1, int(VAL_FRAC * len(train_df)))
    val_idx, tr_idx = idx[:n_val], idx[n_val:]
    return (train_df.iloc[tr_idx].reset_index(drop=True),
            train_df.iloc[val_idx].reset_index(drop=True))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv(DATA)
    has_r = df[TARGET_REMOVAL].notna()
    scenarios = {
        "short_chain": df[df["is_short_chain"] & has_r].reset_index(drop=True),
        "full": df[has_r].reset_index(drop=True),
    }

    methods = ["gin_desc_fixed", "gin_desc_es", "gat_desc_es", "gin_desc_ens"]
    all_summary = {}
    best_epochs_log = {}

    for sname, sub in scenarios.items():
        print(f"\n========== {SCENARIOS[sname]} (n={len(sub)}) ==========")
        results = {m: [] for m in methods}
        epochs_log = {m: [] for m in methods}

        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            idx = rng.permutation(len(sub))
            n_test = max(1, int(0.25 * len(sub)))
            te = sub.iloc[idx[:n_test]].reset_index(drop=True)
            tr_all = sub.iloc[idx[n_test:]].reset_index(drop=True)
            tr, val = split_train_val(tr_all, seed)
            y_test = te[TARGET_REMOVAL].astype(float).to_numpy()

            te_loader = build_loader(te, TARGET_REMOVAL, BATCH_SIZE, False)

            # 1. baseline: GIN + desc, fixed epochs
            m1 = make_model("gin", True, seed, device)
            model_fit_fixed(m1, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True), device, True)
            _, yp1 = model_predict(m1, te_loader, device, True)
            results["gin_desc_fixed"].append(compute_regression_metrics(y_test, yp1))

            # 2. GIN + desc + early stopping
            m2 = make_model("gin", True, seed, device)
            _, ep2 = model_fit_early_stopping(
                m2, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True),
                build_loader(val, TARGET_REMOVAL, BATCH_SIZE, False), device, True)
            _, yp2 = model_predict(m2, te_loader, device, True)
            results["gin_desc_es"].append(compute_regression_metrics(y_test, yp2))
            epochs_log["gin_desc_es"].append(ep2)

            # 3. GAT + desc + early stopping
            m3 = make_model("gat", True, seed, device)
            _, ep3 = model_fit_early_stopping(
                m3, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True),
                build_loader(val, TARGET_REMOVAL, BATCH_SIZE, False), device, True)
            _, yp3 = model_predict(m3, te_loader, device, True)
            results["gat_desc_es"].append(compute_regression_metrics(y_test, yp3))
            epochs_log["gat_desc_es"].append(ep3)

            # 4. GIN + desc + ES + 3-seed ensemble
            preds = []
            for k in range(3):
                ens_seed = seed + 1000 * k
                mk = make_model("gin", True, ens_seed, device)
                model_fit_early_stopping(
                    mk, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True),
                    build_loader(val, TARGET_REMOVAL, BATCH_SIZE, False), device, True)
                _, ypk = model_predict(mk, te_loader, device, True)
                preds.append(ypk)
            results["gin_desc_ens"].append(
                compute_regression_metrics(y_test, np.mean(preds, axis=0)))

            print(f"seed={seed:4d} | fixed={results['gin_desc_fixed'][-1]['rmse']:.2f} | "
                  f"gin_es={results['gin_desc_es'][-1]['rmse']:.2f}(ep{ep2}) | "
                  f"gat_es={results['gat_desc_es'][-1]['rmse']:.2f}(ep{ep3}) | "
                  f"ens={results['gin_desc_ens'][-1]['rmse']:.2f}")

        summary = {}
        for method in methods:
            summary[method] = {
                "r2": (float(np.mean([r["r2"] for r in results[method]])),
                       float(np.std([r["r2"] for r in results[method]]))),
                "rmse": (float(np.mean([r["rmse"] for r in results[method]])),
                         float(np.std([r["rmse"] for r in results[method]]))),
                "mae": (float(np.mean([r["mae"] for r in results[method]])),
                        float(np.std([r["mae"] for r in results[method]]))),
            }
        all_summary[sname] = summary
        best_epochs_log[sname] = epochs_log

        print(f"\n--- {SCENARIOS[sname]} summary (mean ± std) ---")
        for method in methods:
            r2, rmse, mae = summary[method]["r2"], summary[method]["rmse"], summary[method]["mae"]
            print(f"  {method:15s} R²={r2[0]:+.3f}±{r2[1]:.3f}  "
                  f"RMSE={rmse[0]:.2f}±{rmse[1]:.2f}  MAE={mae[0]:.2f}±{mae[1]:.2f}")

    # ---- plot ----
    labels = ["GIN+desc\n(fixed 80ep)", "GIN+desc\n(+early stop)",
              "GAT+desc\n(+early stop)", "GIN+desc\n(+ES +ensemble)"]
    colors = ["#999999", "#1f77b4", "#ff7f0e", "#2ca02c"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for ax, sname in zip(axes, scenarios):
        s = all_summary[sname]
        rmses = [s[m]["rmse"][0] for m in methods]
        errs = [s[m]["rmse"][1] for m in methods]
        r2s = [s[m]["r2"][0] for m in methods]
        bars = ax.bar(labels, rmses, yerr=errs, color=colors, alpha=0.85, capsize=5)
        ax.set_ylabel("RMSE (%)")
        ax.set_title(f"{SCENARIOS[sname]} (n={len(scenarios[sname])})")
        ax.set_ylim(0, max(rmses) * 1.35)
        ax.tick_params(axis="x", labelsize=8)
        for bar, v, r2 in zip(bars, rmses, r2s):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.4, f"{v:.1f}",
                    ha="center", fontsize=9, fontweight="bold")
            ax.text(bar.get_x() + bar.get_width() / 2, v + 2.6, f"R²={r2:+.2f}",
                    ha="center", fontsize=8, color="#333333")
    fig.suptitle("Model improvements: early stopping / GAT / ensemble (lower RMSE is better)",
                 fontsize=11, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    png = OUT_DIR / "model_improvement.png"
    plt.savefig(png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n已保存图: {png}")

    out_json = OUT_DIR / "model_improvement.json"
    out_json.write_text(json.dumps(
        {"summary": {sn: {m: {k: {"mean": v[0], "std": v[1]} for k, v in s[m].items()}
                          for m in s} for sn, s in all_summary.items()},
         "best_epochs": best_epochs_log},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"已保存 JSON: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
