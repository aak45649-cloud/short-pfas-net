# 复现说明（Reproducibility Guide）

本文档说明如何从零复现 ShortPFAS-Net 的实验结果。

## 环境

- Python ≥ 3.10
- 依赖版本锁定见 `requirements.txt`（核心：PyTorch ≥ 2.1、RDKit ≥ 2023.09）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 数据准备

1. 将你的实验数据与收集到的文献数据整理为 CSV，字段见 README「使用你自己的数据」。
2. 放入 `data/raw/`，运行清洗脚本（如提供）生成 `data/processed/` 下的标准化数据。
3. **重要**：本仓库不提交任何真实数据；请勿将未公开实验数据推送到 GitHub。

## 训练

```bash
# 随机划分单阶段训练
python scripts/train.py --config configs/default.yaml --mode single --epochs 30

# 迁移学习：长链预训练 + 短链微调
python scripts/train.py --config configs/default.yaml --mode transfer --epochs 30
```

## 评估与可解释性

- 训练脚本会在每个 checkpoint 打印 val/test 的 R² 与 RMSE。
- 更细粒度的短链/长链分组对比、SHAP 分析，见 `notebooks/` 下的示例 notebook。

## 结果复现的注意点

1. **随机种子**：`configs/default.yaml` 中 `training.seed` 控制划分与初始化，复现时保持一致。
2. **小样本**：短链数据量小时，结果对划分敏感；建议多次运行取均值，或使用 `leave_one_pfas_out` 分组验证。
3. **不确定性**：MC Dropout 需要模型处于 `train()` 模式（`predict_with_uncertainty` 已内置处理）。

## 常见问题

- **RDKit 安装失败**：使用 `conda install -c conda-forge rdkit` 作为替代方案。
- **CUDA 不可用**：代码会自动回退到 CPU，仅训练速度变慢，结果一致。
