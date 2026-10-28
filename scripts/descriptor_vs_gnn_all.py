"""全库 768 条样本上验证「描述符先验能否修复纯 GNN 的小样本失效」。

背景（承接 descriptor_prior_experiment.py）：
  在早期 nature_membrane.csv 的短链子集（几十条）上：
    - 纯 GNN            R²=-1.79  RMSE=14.07  （严重过拟合）
    - 描述符+梯度提升树   R²=+0.40  RMSE=6.61
  结论是「化学先验知识比纯图结构学习更能补偿小样本」。

本实验回答一个关键问题：**把文献样本扩充到全库 768 条之后，
纯 GNN 的过拟合是否缓解？描述符先验注入是否仍然必要？**

两个场景，各跑 4 方法 × 5 种子（25% 留出划分）：
  1. short_chain  —— 短链 + 去除率子集（292 条），与旧实验同口径、可对照
  2. full         —— 全库 + 去除率（628 条），上界参考

四方法：
  mean_baseline   常数基线
  gnn             纯图结构学习（无先验）
  descriptor_gb   梯度提升树 + RDKit 描述符（先验上界参考）
  gnn_descriptor  GNN + 描述符先验注入（主角）

运行：
    python scripts/descriptor_vs_gnn_all.py
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

DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "all_literature.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "runs" / "transfer"

SEEDS = [42, 123, 2024, 7, 999]
NODE_FEAT_DIM, EDGE_FEAT_DIM = 31, 6
EPOCHS = 80
BATCH_SIZE = 32
LR = 1e-3

SCENARIOS = {
    "short_chain": "Short-chain + removal (n=292)",
    "full": "Full corpus + removal (n=628)",
}


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
    """RDKit 描述符 + 少量连续条件特征（NaN 用中位数填充）。"""
    mols = [Chem.MolFromSmiles(s) for s in df["smiles"]]
    X = pd.DataFrame(index=df.index)
    X["molecular_weight"] = [Descriptors.MolWt(m) for m in mols]
    X["logp"] = [Descriptors.MolLogP(m) for m in mols]
    X["n_fluorine"] = [sum(1 for a in m.GetAtoms() if a.GetSymbol() == "F") for m in mols]
    X["chain_length"] = df["chain_length"].astype(float)
    ph = pd.to_numeric(df["ph"], errors="coerce")
    X["ph"] = ph.fillna(ph.median())
    X["log_conc"] = np.log10(df["initial_concentration"].astype(float).clip(lower=1e-9))
    return X


def run_scenario(name: str, df: pd.DataFrame, device) -> dict:
    """在单个场景上跑 4 方法 × 5 种子，返回 {method: {metric: (mean, std)}}。"""
    methods = ["mean_baseline", "gnn", "descriptor_gb", "gnn_descriptor"]
    results = {m: [] for m in methods}

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(df))
        n_test = max(1, int(0.25 * len(df)))
        test_idx, train_idx = idx[:n_test], idx[n_test:]
        tr = df.iloc[train_idx].reset_index(drop=True)
        te = df.iloc[test_idx].reset_index(drop=True)
        y_test = te[TARGET_REMOVAL].astype(float).to_numpy()

        # 1. 常数基线
        results["mean_baseline"].append(compute_regression_metrics(
            y_test, np.full_like(y_test, tr[TARGET_REMOVAL].mean())))

        # 2. 纯 GNN
        torch.manual_seed(seed)
        m = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64).to(device)
        model_fit(m, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True), device, LR, use_desc=False)
        yt, yp = model_predict(m, build_loader(te, TARGET_REMOVAL, BATCH_SIZE, False), device, use_desc=False)
        results["gnn"].append(compute_regression_metrics(yt, yp))

        # 3. 描述符 + 梯度提升树
        gb = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                                       subsample=0.9, random_state=seed)
        gb.fit(descriptor_features(tr), tr[TARGET_REMOVAL])
        results["descriptor_gb"].append(compute_regression_metrics(
            y_test, gb.predict(descriptor_features(te))))

        # 4. GNN + 描述符先验注入
        torch.manual_seed(seed)
        m2 = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64,
                          descriptor_dim=len(DESCRIPTOR_FEATURES)).to(device)
        model_fit(m2, build_loader(tr, TARGET_REMOVAL, BATCH_SIZE, True), device, LR, use_desc=True)
        yt2, yp2 = model_predict(m2, build_loader(te, TARGET_REMOVAL, BATCH_SIZE, False), device, use_desc=True)
        results["gnn_descriptor"].append(compute_regression_metrics(yt2, yp2))

        print(f"[{name}] seed={seed:4d} | base={results['mean_baseline'][-1]['rmse']:.2f} | "
              f"gnn={results['gnn'][-1]['rmse']:.2f} | "
              f"gb={results['descriptor_gb'][-1]['rmse']:.2f} | "
              f"gnn+desc={results['gnn_descriptor'][-1]['rmse']:.2f}")

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
    return summary


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv(DATA)
    has_r = df[TARGET_REMOVAL].notna()
    scenarios = {
        "short_chain": df[df["is_short_chain"] & has_r].reset_index(drop=True),
        "full": df[has_r].reset_index(drop=True),
    }

    all_summary = {}
    for name, sub in scenarios.items():
        print(f"\n========== Scenario: {SCENARIOS[name]} ({len(sub)} rows) ==========")
        s = run_scenario(name, sub, device)
        all_summary[name] = s
        base = s["mean_baseline"]["rmse"][0]
        print(f"\n--- {SCENARIOS[name]} Summary (mean ± std) ---")
        for method in ["mean_baseline", "gnn", "descriptor_gb", "gnn_descriptor"]:
            r2, rmse, mae = s[method]["r2"], s[method]["rmse"], s[method]["mae"]
            print(f"  {method:14s} R²={r2[0]:+.3f}±{r2[1]:.3f}  RMSE={rmse[0]:.2f}±{rmse[1]:.2f}  MAE={mae[0]:.2f}±{mae[1]:.2f}")
        print("  Relative improvement vs constant baseline (lower RMSE = better):")
        for method in ["gnn", "descriptor_gb", "gnn_descriptor"]:
            imp = (base - s[method]["rmse"][0]) / base * 100
            print(f"    {method:14s} {imp:+.1f}%")

    # ---- 绘图：两场景并列，RMSE + R² 双面板 ----
    methods = ["mean_baseline", "gnn", "descriptor_gb", "gnn_descriptor"]
    labels = ["Mean baseline", "GNN (graph)", "Descriptor + GB", "GNN + descriptor"]
    colors = ["#999999", "#d62728", "#2ca02c", "#1f77b4"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for ax, (name, sub) in zip(axes, scenarios.items()):
        s = all_summary[name]
        rmses = [s[m]["rmse"][0] for m in methods]
        errs = [s[m]["rmse"][1] for m in methods]
        bars = ax.bar(labels, rmses, yerr=errs, color=colors, alpha=0.85, capsize=5)
        ax.axhline(s["mean_baseline"]["rmse"][0], color="#999999", linewidth=1, linestyle="--", alpha=0.7)
        ax.set_ylabel("RMSE (%)")
        ax.set_title(f"{SCENARIOS[name]}  |  lower RMSE is better")
        ax.set_ylim(0, max(rmses) * 1.35)
        ax.tick_params(axis="x", rotation=20)
        for bar, v in zip(bars, rmses):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.4, f"{v:.1f}",
                    ha="center", fontsize=9, fontweight="bold")
        r2s = [s[m]["r2"][0] for m in methods]
        for bar, r2 in zip(bars, r2s):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2.6,
                    f"R²={r2:+.2f}", ha="center", fontsize=8, color="#333333")
    fig.suptitle("Does sample expansion fix pure-GNN overfitting? "
                 "Descriptor prior vs graph learning on full literature corpus",
                 fontsize=11, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    png = OUT_DIR / "descriptor_vs_gnn_all.png"
    plt.savefig(png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n已保存图: {png}")

    out_json = OUT_DIR / "descriptor_vs_gnn_all.json"
    out_json.write_text(json.dumps(
        {name: {m: {k: {"mean": v[0], "std": v[1]} for k, v in s[m].items()} for m in s}
         for name, s in all_summary.items()},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"已保存 JSON: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
