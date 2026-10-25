"""Transfer-learning benchmark on real data.

验证 ShortPFAS-Net 的核心主张：迁移学习（长链数据预训练 + 短链数据微调）
是否真的能缓解短链 PFAS 数据稀缺。

在 nature_membrane.csv（534 条膜去除记录）上，对比三种方法在**同一短链
测试集**上的表现（多随机种子取均值 ± 标准差）：

  1. mean_baseline   —— 常数基线：直接用训练集均值预测（判断模型是否真的学到东西）
  2. direct          —— 只用短链小样本直接训练（无迁移）
  3. transfer        —— 长链数据预训练，短链数据微调（迁移学习）

运行：
    python scripts/transfer_experiment.py
输出：
    终端表格 + runs/transfer/transfer_comparison.png

注意：短链去除率高度偏态（均值 91.4%），R² 对测试集方差敏感，因此
同时报告 RMSE/MAE，并给出与"预测均值"基线的相对改进率。
"""

from __future__ import annotations

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

from shortpfas.data import (  # noqa: E402
    PFASDataset,
    collate_graphs,
)
from shortpfas.data.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_REMOVAL,
)
from shortpfas.models import ShortPFASNet  # noqa: E402
from shortpfas.utils import compute_regression_metrics  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "nature_membrane.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "runs" / "transfer"

SEEDS = [42, 123, 2024, 7, 999]
NODE_FEAT_DIM, EDGE_FEAT_DIM = 31, 6
EPOCHS_PRETRAIN = 60
EPOCHS_FINETUNE = 60
BATCH_SIZE = 32
LR = 1e-3


def cond_dim() -> int:
    return len(CONTINUOUS_FEATURES) + sum(len(v) for v in CATEGORICAL_FEATURES.values())


def build_loader(df: pd.DataFrame, target: str, batch_size: int, shuffle: bool):
    ds = PFASDataset(df, target=target)
    return torch.utils.data.DataLoader(
        ds, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_graphs
    )


def predict(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
            pred = model(
                batch["node_features"], batch["edge_index"], batch["edge_features"],
                batch["batch"], batch["conditions"],
            )
            y_pred.append(pred[:, 0].cpu().numpy())
            y_true.append(batch["target"].cpu().numpy())
    return np.concatenate(y_true), np.concatenate(y_pred)


def train_epoch(model, loader, optimizer, device):
    model.train()
    total, n = 0.0, 0
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        pred = model(
            batch["node_features"], batch["edge_index"], batch["edge_features"],
            batch["batch"], batch["conditions"],
        )
        loss = nn.functional.mse_loss(pred, batch["target"].unsqueeze(-1))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total += loss.item() * batch["target"].shape[0]
        n += batch["target"].shape[0]
    return total / max(n, 1)


def fit(model, loader, epochs, device, lr):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(epochs):
        train_epoch(model, loader, optimizer, device)
    return model


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}")

    df = pd.read_csv(DATA)
    short = df[df["is_short_chain"]].reset_index(drop=True)
    long = df[~df["is_short_chain"]].reset_index(drop=True)
    print(f"短链: {len(short)} 条 | 长链: {len(long)} 条")

    results = {"mean_baseline": [], "direct": [], "transfer": []}

    for seed in SEEDS:
        # 固定短链测试集（每个种子重新划分，保证公平）
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(short))
        n_test = max(1, int(0.25 * len(short)))
        test_idx = idx[:n_test]
        train_idx = idx[n_test:]

        short_train = short.iloc[train_idx].reset_index(drop=True)
        short_test = short.iloc[test_idx].reset_index(drop=True)

        y_test = short_test[TARGET_REMOVAL].astype(float).to_numpy()

        # --- 1. 常数基线：训练集均值 ---
        mean_pred = np.full_like(y_test, short_train[TARGET_REMOVAL].mean())
        results["mean_baseline"].append(compute_regression_metrics(y_test, mean_pred))

        # --- 2. 直接训练（无迁移） ---
        torch.manual_seed(seed)
        m_direct = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64).to(device)
        fit(m_direct, build_loader(short_train, TARGET_REMOVAL, BATCH_SIZE, True),
            EPOCHS_FINETUNE, device, LR)
        y_true, y_pred = predict(m_direct, build_loader(short_test, TARGET_REMOVAL, BATCH_SIZE, False), device)
        results["direct"].append(compute_regression_metrics(y_true, y_pred))

        # --- 3. 迁移学习：长链预训练 + 短链微调 ---
        torch.manual_seed(seed)
        m_transfer = ShortPFASNet(NODE_FEAT_DIM, EDGE_FEAT_DIM, cond_dim(), hidden_dim=64).to(device)
        # 预训练（长链数据）
        fit(m_transfer, build_loader(long, TARGET_REMOVAL, BATCH_SIZE, True),
            EPOCHS_PRETRAIN, device, LR)
        # 微调（短链训练集，更小学习率）
        fit(m_transfer, build_loader(short_train, TARGET_REMOVAL, BATCH_SIZE, True),
            EPOCHS_FINETUNE, device, LR * 0.1)
        y_true, y_pred = predict(m_transfer, build_loader(short_test, TARGET_REMOVAL, BATCH_SIZE, False), device)
        results["transfer"].append(compute_regression_metrics(y_true, y_pred))

        print(f"seed={seed:4d} | baseline RMSE={results['mean_baseline'][-1]['rmse']:.2f} | "
              f"direct RMSE={results['direct'][-1]['rmse']:.2f} | "
              f"transfer RMSE={results['transfer'][-1]['rmse']:.2f}")

    # --- 汇总统计 ---
    print("\n========== 迁移学习对比结果（均值 ± 标准差） ==========")
    summary = {}
    for method in ["mean_baseline", "direct", "transfer"]:
        r2s = [r["r2"] for r in results[method]]
        rmses = [r["rmse"] for r in results[method]]
        maes = [r["mae"] for r in results[method]]
        summary[method] = {
            "r2": (np.mean(r2s), np.std(r2s)),
            "rmse": (np.mean(rmses), np.std(rmses)),
            "mae": (np.mean(maes), np.std(maes)),
        }
        print(f"{method:14s} R²={np.mean(r2s):+.3f}±{np.std(r2s):.3f}  "
              f"RMSE={np.mean(rmses):.2f}±{np.std(rmses):.2f}  "
              f"MAE={np.mean(maes):.2f}±{np.std(maes):.2f}")

    # 相对改进（RMSE 越低越好）
    base_rmse = summary["mean_baseline"]["rmse"][0]
    print("\n相对改进（vs 常数基线）:")
    for method in ["direct", "transfer"]:
        imp = (base_rmse - summary[method]["rmse"][0]) / base_rmse * 100
        print(f"  {method:10s} RMSE 降低 {imp:+.1f}%")

    # --- 绘图 ---
    labels = ["Mean baseline", "Direct (no transfer)", "Transfer learning"]
    rmses = [summary[m]["rmse"][0] for m in ["mean_baseline", "direct", "transfer"]]
    rmse_err = [summary[m]["rmse"][1] for m in ["mean_baseline", "direct", "transfer"]]
    r2s = [summary[m]["r2"][0] for m in ["mean_baseline", "direct", "transfer"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ["#999999", "#d62728", "#2ca02c"]
    ax1.bar(labels, rmses, yerr=rmse_err, color=colors, alpha=0.85, capsize=5)
    ax1.set_ylabel("RMSE (%)")
    ax1.set_title("Short-chain test RMSE (lower is better)")
    ax1.set_ylim(0, max(rmses) * 1.25)

    ax2.bar(labels, r2s, color=colors, alpha=0.85)
    ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax2.set_ylabel("R² (higher is better)")
    ax2.set_title("Short-chain test R²")
    fig.suptitle("Transfer learning on short-chain PFAS (real membrane data)", fontsize=13, y=1.02)
    plt.tight_layout()
    p = OUT_DIR / "transfer_comparison.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n已保存: {p}")

    # 保存 JSON 结果
    import json
    out_json = OUT_DIR / "transfer_results.json"
    out_json.write_text(json.dumps({
        m: {k: {"mean": v[0], "std": v[1]} for k, v in summary[m].items()}
        for m in summary
    }, indent=2), encoding="utf-8")
    print(f"已保存: {out_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
