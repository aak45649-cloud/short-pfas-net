"""SHAP 可解释性分析：解释 PFAS 去除率的驱动因素。

对标文献方法（Karbassiyazdi et al. 2022 用 XGBoost + SHAP 解释 PFAS 去除），
在真实数据上训练 XGBoost 回归模型，用 TreeExplainer 计算 SHAP 值，输出：

1. summary bar    —— 特征全局重要性排名
2. summary beeswarm —— 每个样本的 SHAP 值分布（红=高值，蓝=低值）
3. dependence     —— 关键特征对去除率的方向性影响
4. 官能团/链长分组对比 —— 短链 vs 长链的行为差异

特征工程：从 SMILES 提取分子描述符（分子量、氟原子数、碳链长、官能团类别），
叠加工艺条件（pH、初始浓度），构成表格特征矩阵。

运行：
    python scripts/shap_analysis.py
输出：
    runs/shap/ 目录下的 PNG 图
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无显示环境也能出图
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rdkit import Chem
from rdkit.Chem import Descriptors

# 中文字体（matplotlib 默认不含中文，这里用英文标签避免乱码）
plt.rcParams["font.size"] = 11
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

OUT_DIR = Path(__file__).resolve().parent.parent / "runs" / "shap"
DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "nature_membrane.csv"

FEATURE_LABELS = {
    "chain_length": "Chain length (perfluorinated C)",
    "molecular_weight": "Molecular weight (g/mol)",
    "logp": "logP (hydrophobicity)",
    "n_fluorine": "Fluorine atom count",
    "ph": "pH",
    "log_conc": "log10 initial conc. (mg/L)",
    "is_sulfonic": "Sulfonic head group",
    "is_ether": "Ether-acid (GenX etc.)",
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """从 SMILES + 条件列构建数值特征矩阵。"""
    feats = pd.DataFrame(index=df.index)

    # --- 分子描述符（RDKit） ---
    mols = [Chem.MolFromSmiles(s) for s in df["smiles"]]
    feats["molecular_weight"] = [Descriptors.MolWt(m) for m in mols]
    feats["logp"] = [Descriptors.MolLogP(m) for m in mols]
    feats["n_fluorine"] = [
        sum(1 for a in m.GetAtoms() if a.GetSymbol() == "F") for m in mols
    ]

    # --- 分子身份 ---
    feats["chain_length"] = df["chain_length"].astype(float)
    # 官能团类别：磺酸/磺酰胺 vs 羧酸 vs 醚酸
    name = df["pfas_name"]
    feats["is_sulfonic"] = (
        name.str.contains("S", regex=False) & ~name.str.contains("FOSA", regex=False)
    ).astype(float)
    feats["is_ether"] = name.isin(["GenX", "PFMOBA", "PFMOPrA", "4:2FTS", "6:2FTS"]).astype(float)

    # --- 工艺条件 ---
    feats["ph"] = df["ph"].astype(float)
    # 初始浓度取对数（跨度 1e-6 ~ 1e3，直接取对数更合理）
    feats["log_conc"] = np.log10(df["initial_concentration"].astype(float).clip(lower=1e-9))

    return feats


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA)
    X = build_features(df)
    y = df["removal_efficiency"].astype(float)

    print(f"特征矩阵: {X.shape}")
    print(f"目标去除率: mean={y.mean():.1f}%  std={y.std():.1f}%")

    # --- 训练梯度提升树（对标文献的 XGBoost；用 sklearn 实现避免 OpenMP 依赖） ---
    from sklearn.ensemble import GradientBoostingRegressor

    model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        random_state=42,
    )
    model.fit(X, y)
    r2 = model.score(X, y)
    print(f"GradientBoosting 训练 R² = {r2:.3f}")

    # --- SHAP TreeExplainer ---
    import shap

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)  # (n_samples, n_features)
    print(f"SHAP 值形状: {shap_values.shape}")

    # ================= 图 1: 全局重要性 bar =================
    fig, ax = plt.subplots(figsize=(8, 5))
    shap.summary_plot(
        shap_values, X, feature_names=[FEATURE_LABELS.get(c, c) for c in X.columns],
        plot_type="bar", show=False, max_display=10,
    )
    plt.title("Global feature importance (SHAP)", fontsize=13, pad=12)
    plt.tight_layout()
    p1 = OUT_DIR / "shap_importance_bar.png"
    plt.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p1}")

    # ================= 图 2: beeswarm 分布 =================
    fig, ax = plt.subplots(figsize=(8, 5))
    shap.summary_plot(
        shap_values, X, feature_names=[FEATURE_LABELS.get(c, c) for c in X.columns],
        show=False, max_display=10,
    )
    plt.title("SHAP value distribution (red=high, blue=low)", fontsize=13, pad=12)
    plt.tight_layout()
    p2 = OUT_DIR / "shap_beeswarm.png"
    plt.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p2}")

    # ================= 图 3: 关键特征 dependence =================
    # 找重要性前 3 的连续特征
    imp_order = np.argsort(np.abs(shap_values).mean(axis=0))[::-1]
    top3 = [X.columns[i] for i in imp_order[:3]]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for ax, col in zip(axes, top3):
        shap.dependence_plot(
            col, shap_values, X, show=False, ax=ax,
        )
        ax.set_xlabel(FEATURE_LABELS.get(col, col), fontsize=11)
        ax.set_title(FEATURE_LABELS.get(col, col), fontsize=12)
    fig.suptitle("Top-3 feature dependence on removal efficiency", fontsize=13, y=1.02)
    plt.tight_layout()
    p3 = OUT_DIR / "shap_dependence.png"
    plt.savefig(p3, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p3}")

    # ================= 图 4: 短链 vs 长链 分组对比 =================
    df_short = df[df["is_short_chain"]]
    df_long = df[~df["is_short_chain"]]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # 左：去除率分布
    axes[0].hist(df_short["removal_efficiency"], bins=25, alpha=0.6, label=f"Short-chain (n={len(df_short)})", color="#d62728")
    axes[0].hist(df_long["removal_efficiency"], bins=25, alpha=0.6, label=f"Long-chain (n={len(df_long)})", color="#1f77b4")
    axes[0].set_xlabel("Removal efficiency (%)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Removal distribution: short vs long chain")
    axes[0].legend()

    # 右：链长 vs 去除率（带官能团颜色）
    sc = axes[1].scatter(
        df["chain_length"], df["removal_efficiency"],
        c=df["is_short_chain"].map({True: "#d62728", False: "#1f77b4"}),
        alpha=0.35, s=12,
    )
    axes[1].set_xlabel("Perfluorinated chain length")
    axes[1].set_ylabel("Removal efficiency (%)")
    axes[1].set_title("Chain length vs removal (red=short, blue=long)")
    # 趋势线
    for label, sub in [("Short", df_short), ("Long", df_long)]:
        if len(sub) > 2:
            z = np.polyfit(sub["chain_length"], sub["removal_efficiency"], 1)
            xs = np.linspace(sub["chain_length"].min(), sub["chain_length"].max(), 50)
            axes[1].plot(xs, np.polyval(z, xs), "--", alpha=0.7)
    plt.tight_layout()
    p4 = OUT_DIR / "short_vs_long.png"
    plt.savefig(p4, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p4}")

    # ================= 图 5: 官能团 + pH 的去除率 =================
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    # 左：官能团
    fg_map = {"is_sulfonic": "Sulfonic", "is_ether": "Ether-acid"}
    df["fg_label"] = "Carboxylic"
    df.loc[df["pfas_name"].str.contains("S", regex=False) & ~df["pfas_name"].str.contains("FOSA"), "fg_label"] = "Sulfonic"
    df.loc[df["pfas_name"].isin(["GenX", "PFMOBA", "PFMOPrA", "4:2FTS", "6:2FTS"]), "fg_label"] = "Ether-acid"
    df.loc[df["pfas_name"] == "FOSA", "fg_label"] = "Sulfonamide"
    order = df.groupby("fg_label")["removal_efficiency"].mean().sort_values(ascending=False).index
    df.boxplot(column="removal_efficiency", by="fg_label", ax=axes[0], grid=False)
    axes[0].set_title("Removal by functional group")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Removal efficiency (%)")
    # 右：pH vs 去除率
    axes[1].scatter(df["ph"], df["removal_efficiency"], c=df["is_short_chain"].map({True: "#d62728", False: "#1f77b4"}), alpha=0.35, s=12)
    axes[1].set_xlabel("pH")
    axes[1].set_ylabel("Removal efficiency (%)")
    axes[1].set_title("pH vs removal (red=short, blue=long)")
    fig.suptitle("")
    plt.tight_layout()
    p5 = OUT_DIR / "functional_group_ph.png"
    plt.savefig(p5, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p5}")

    # ================= 图 6: 部分依赖图 PDP + ICE =================
    # 标准 sklearn 风格：灰色细线是每个样本的 ICE（个体条件期望），
    # 加粗的蓝色实线是 PDP 平均曲线，底部 rug 是数据分布刻度。
    # kind="both" 同时画 ICE + 平均线，是论文/官方文档的经典样式。
    from sklearn.inspection import PartialDependenceDisplay

    pdp_features = ["ph", "log_conc", "logp", "chain_length"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    PartialDependenceDisplay.from_estimator(
        model, X, pdp_features,
        kind="both",
        ax=axes,
        grid_resolution=50,
        centered=False,
        subsample=200,            # 限制 ICE 线数量，避免过密
        random_state=42,
        pd_line_kw={"color": "#1f77b4", "linewidth": 2.5},   # 平均线：蓝色加粗
        ice_lines_kw={"color": "#9ecae1", "linewidth": 0.5, "alpha": 0.4},  # ICE：浅蓝细线
    )
    for ax, col in zip(axes.ravel(), pdp_features):
        ax.set_xlabel(FEATURE_LABELS.get(col, col), fontsize=11)
        ax.set_ylabel("Predicted removal (%)", fontsize=11)
        ax.set_ylim(40, 105)      # 统一 y 轴，便于跨子图对比
        ax.grid(alpha=0.25)
    fig.suptitle("Partial Dependence Plots (ICE + PDP)", fontsize=14, y=0.99)
    plt.tight_layout()
    p6 = OUT_DIR / "pdp_top_features.png"
    plt.savefig(p6, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"已保存: {p6}")

    # ================= 打印文字结论 =================
    print("\n========== SHAP 分析结论 ==========")
    mean_abs = np.abs(shap_values).mean(axis=0)
    for i in imp_order:
        col = X.columns[i]
        print(f"  {FEATURE_LABELS.get(col, col):<40s} |SHAP|={mean_abs[i]:.3f}")

    # 官能团对比
    print("\n官能团去除率:")
    print(df.groupby("fg_label")["removal_efficiency"].agg(["mean", "count"]).round(1))

    # 短链 vs 长链
    print(f"\n短链去除率: {df_short['removal_efficiency'].mean():.1f}% (n={len(df_short)})")
    print(f"长链去除率: {df_long['removal_efficiency'].mean():.1f}% (n={len(df_long)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
