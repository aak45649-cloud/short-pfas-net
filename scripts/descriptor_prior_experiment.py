"""描述符先验能否修复纯 GNN 的小样本失效？

背景：descriptor_baseline.py 显示，在同短链测试集上：
  - 纯 GNN            R²=-1.79  RMSE=14.07
  - 描述符+梯度提升树   R²=+0.40  RMSE=6.61
说明"化学先验知识"比"纯图结构学习"更能补偿小样本。

本实验验证核心改进方向：把 RDKit 描述符先验注入 GNN（ShortPFASNet 的
descriptor_dim 分支），看"图表征 + 描述符先验 + 工艺条件"三重融合能否
改善纯 GNN。在同一短链测试集（同样 5 个种子、同样 25% 留出划分）上对比：

  1. mean_baseline     —— 常数基线
  2. gnn               —— 纯图结构学习（无先验）
  3. descriptor_gb     —— 梯度提升树 + RDKit 描述符（先验上界参考）
  4. gnn_descriptor    —— GNN + 描述符先验注入（本实验主角）

运行：
    python scripts/descriptor_prior_experiment.py
"""

from __future__ import annotations

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

from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.ensemble import GradientBoostingRegressor

from shortpfas.data import PFASDataset, collate_graphs  # noqa: E402
from shortpfas.data.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    DESCRIPTOR_FEATURES,
    TARGET_REMOVAL,
)
from shortpfas.models import ShortPFASNet  # noqa: E402
from shortpfas.utils import compute_regression_metrics  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "nature_membrane.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "runs" / "transfer"

SEEDS = [42, 123, 2024, 7, 999]
NODE_FEAT_DIM, EDGE_FEAT_DIM = 31, 6
EPOCHS = 60
BATCH_SIZE = 32
LR = 1e-3


def cond_dim() -> int:
    return len(CONTINUOUS_FEATURES) + sum(len(v) for v in CATEGORICAL_FEATURES.values())


def build_loader(df, target, batch_size, shuffle):
    ds = PFASDataset(df, target=target)
    return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_graphs)


def model_predict(model, loader, device, use_desc):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for b in loader:
            b = {k: v.to(device) for k, v in b.items() if isinstance(v, torch.Tensor)}
            desc = b["descriptors"] if use_desc else None
            pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                         b["batch"], b["conditions"], desc)
            y_pred.append(pred[:, 0].cpu().numpy())
            y_true.append(b["target"].cpu().numpy())
    return np.concatenate(y_true), np.concatenate(y_pred)


def model_fit(model, loader, device, lr, use_desc):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for _ in range(EPOCHS):
        for b in loader:
            b = {k: v.to(device) for k, v in b.items() if isinstance(v, torch.Tensor)}
            desc = b["descriptors"] if use_desc else None
            pred = model(b["node_features"], b["edge_index"], b["edge_features"],
                         b["batch"], b["conditions"], desc)
            loss = nn.functional.mse_loss(pred, b["target"].unsqueeze(-1))
            opt.zero_grad(); loss.backward(); opt.step()
    return model


def descriptor_features(df: pd.DataFrame) -> pd.DataFrame:
    mols = [Chem.MolFromSmiles(s) for s in df["smiles"]]
    X = pd.DataFrame(index=df.index)
    X["molecular_weight"] = [Descriptors.MolWt(m) for m in mols]
    X["logp"] = [Descriptors.MolLogP(m) for m in mols]
    X["n_fluorine"] = [sum(1 for a in m.GetAtoms() if a.GetSymbol() == "F") for m in mols]
    X["chain_length"] = df["chain_length"].astype(float)
    X["ph"] = df["ph"].astype(float)
    X["log_conc"] = np.log10(df["initial_concentration"].astype(float).clip(lower=1e-9))
    return X


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv(DATA)
    short = df[df["is_short_chain"]].reset_index(drop=True)

    methods = ["mean_baseline", "gnn", "descriptor_gb", "gnn_descriptor"]
    results = {m: [] for m in methods}

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(short))
        n_test = max(1, int(0.25 * len(short)))
        test_idx, train_idx = idx[:n_test], idx[n_test:]
        short_train = short.iloc[train_idx].reset_index(drop=True)
        short_test = short.iloc[test_idx].reset_index(drop=True)
        y_test = short_test[TARGET_REMOVAL].astype(float).to_numpy()

        # 1. 常数基线
        mean_pred = np.full_like(y_test, short_train[TARGET_REMOVAL].mean())
        results["mean_baseline"].append(compute_regression_metrics(y_test, mean_pred))

        # 2. 纯 GNN
        torch.manual_seed(seed)
        m = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64).to(device)
        model_fit(m, build_loader(short_train, TARGET_REMOVAL, BATCH_SIZE, True), device, LR, use_desc=False)
        yt, yp = model_predict(m, build_loader(short_test, TARGET_REMOVAL, BATCH_SIZE, False), device, use_desc=False)
        results["gnn"].append(compute_regression_metrics(yt, yp))

        # 3. 描述符 + 梯度提升树
        Xtr = descriptor_features(short_train)
        Xte = descriptor_features(short_test)
        gb = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                                       subsample=0.9, random_state=seed)
        gb.fit(Xtr, short_train[TARGET_REMOVAL])
        yp_gb = gb.predict(Xte)
        results["descriptor_gb"].append(compute_regression_metrics(y_test, yp_gb))

        # 4. GNN + 描述符先验注入
        torch.manual_seed(seed)
        m2 = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64,
                          descriptor_dim=len(DESCRIPTOR_FEATURES)).to(device)
        model_fit(m2, build_loader(short_train, TARGET_REMOVAL, BATCH_SIZE, True), device, LR, use_desc=True)
        yt2, yp2 = model_predict(m2, build_loader(short_test, TARGET_REMOVAL, BATCH_SIZE, False), device, use_desc=True)
        results["gnn_descriptor"].append(compute_regression_metrics(yt2, yp2))

        print(f"seed={seed:4d} | baseline={results['mean_baseline'][-1]['rmse']:.2f} | "
              f"gnn={results['gnn'][-1]['rmse']:.2f} | "
              f"desc_gb={results['descriptor_gb'][-1]['rmse']:.2f} | "
              f"gnn+desc={results['gnn_descriptor'][-1]['rmse']:.2f}")

    # 汇总
    print("\n===== 描述符先验能否修复 GNN（短链测试集，均值±标准差） =====")
    summary = {}
    for method in methods:
        r2s = [r["r2"] for r in results[method]]
        rmses = [r["rmse"] for r in results[method]]
        maes = [r["mae"] for r in results[method]]
        summary[method] = {"r2": (np.mean(r2s), np.std(r2s)),
                           "rmse": (np.mean(rmses), np.std(rmses)),
                           "mae": (np.mean(maes), np.std(maes))}
        print(f"{method:14s} R²={np.mean(r2s):+.3f}±{np.std(r2s):.3f}  "
              f"RMSE={np.mean(rmses):.2f}±{np.std(rmses):.2f}  MAE={np.mean(maes):.2f}±{np.std(maes):.2f}")

    base_rmse = summary["mean_baseline"]["rmse"][0]
    print("\n相对改进（vs 常数基线，RMSE 越低越好）:")
    for method in ["gnn", "descriptor_gb", "gnn_descriptor"]:
        imp = (base_rmse - summary[method]["rmse"][0]) / base_rmse * 100
        print(f"  {method:14s} {imp:+.1f}%")

    # 绘图
    labels = ["Mean baseline", "GNN (graph)", "Descriptor + GB", "GNN + descriptor"]
    rmses = [summary[m]["rmse"][0] for m in methods]
    errs = [summary[m]["rmse"][1] for m in methods]
    colors = ["#999999", "#d62728", "#2ca02c", "#1f77b4"]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(labels, rmses, yerr=errs, color=colors, alpha=0.85, capsize=5)
    ax.axhline(base_rmse, color="#999999", linewidth=1, linestyle="--", alpha=0.7)
    ax.set_ylabel("RMSE (%)")
    ax.set_title("Does descriptor prior fix small-sample GNN? (lower is better)")
    ax.set_ylim(0, max(rmses) * 1.3)
    for bar, v in zip(bars, rmses):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3, f"{v:.1f}",
                ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    p = OUT_DIR / "gnn_descriptor_prior.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n已保存: {p}")

    out_json = OUT_DIR / "gnn_descriptor_prior.json"
    out_json.write_text(json.dumps(
        {m: {k: {"mean": v[0], "std": v[1]} for k, v in summary[m].items()} for m in summary},
        indent=2), encoding="utf-8")
    print(f"已保存: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
