# ShortPFAS-Net

**多模态深度学习模型：面向短链 PFAS（全氟/多氟烷基物质）去除的预测框架**

ShortPFAS-Net 是一个用于预测水中 PFAS 去除效率（去除率 R% 与吸附容量 q_e）的多模态深度学习框架。它融合 **PFAS 分子图（图神经网络 GNN）** 与 **工艺/水质/吸附剂条件（多层感知机 MLP）** 两路信息，并针对**短链 PFAS 数据稀缺**这一公认难点，提供**迁移学习**与**不确定性估计**能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

---

## 为什么做这个项目

- **短链 PFAS 是治理难点**：相比长链 PFAS（PFOS/PFOA），短链 PFAS（如 PFBS、PFHxA）疏水/静电作用弱、吸附亲和力差，传统方法难以有效去除。
- **现有 ML 模型忽略分子结构**：已有工作（如 XGBoost/RF/ANN 预测去除率）大多只使用工艺条件作为输入，未把 PFAS 分子本身的图结构纳入建模。
- **短链数据稀缺**：文献中短链 PFAS 的吸附数据远少于长链，导致常规模型对短链样本泛化能力差。

ShortPFAS-Net 的差异化贡献：

1. **分子图 + 条件多模态融合**：GNN 编码 SMILES 分子图，MLP 编码工艺条件，注意力加权融合。
2. **迁移学习策略**：用长链/文献数据预训练，短链实验数据微调，缓解小样本问题。
3. **不确定性估计**：MC Dropout 给出预测置信区间，支撑实际工程决策。

## 模型架构

```
SMILES ──▶ 分子图构建(RDKit) ──▶ GNN 编码器 ──┐
                                              ├──▶ 注意力融合 ──▶ 预测头 ──▶ 去除率 / 吸附容量
工艺·水质·吸附剂条件 ──▶ 标准化/编码 ──▶ MLP 编码器 ──┘                    └──▶ 不确定性(MC Dropout)
```

## 目录结构

```
short-pfas-net/
├── configs/            # YAML 配置
├── data/
│   ├── raw/            # 原始实验/文献数据（不入库，需自行下载）
│   └── processed/      # 清洗后的数据
├── src/shortpfas/
│   ├── data/           # 数据 schema、分子图构建、Dataset、划分策略
│   ├── models/         # GNN 编码器、MLP 编码器、多模态融合
│   └── utils/          # 评估指标
├── scripts/            # 训练/评估脚本
├── notebooks/          # 演示与可解释性分析
├── tests/              # 单元测试
├── pyproject.toml
└── requirements.txt
```

## 快速开始

### 1. 安装

```bash
git clone <your-repo-url>
cd short-pfas-net
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

> 注意：`rdkit` 用于 SMILES→分子图转换，是核心依赖。若安装失败，请参考 [RDKit 官方安装说明](https://www.rdkit.org/docs/Install.html)。

### 2. 跑通端到端（使用演示数据）

无真实数据时，用内置合成演示数据验证全流程：

```bash
python scripts/train.py --mode single        # 随机划分训练
python scripts/train.py --mode transfer      # 迁移学习（预训练+微调）
```

### 3. 使用你自己的数据

将数据整理为 CSV，至少包含以下列：

| 列名 | 含义 | 类型 |
|------|------|------|
| `smiles` | PFAS 分子 SMILES | string |
| `pfas_name` | PFAS 名称（如 PFBS） | string |
| `chain_length` | 全氟碳链长度 | int |
| `initial_concentration` | 初始浓度 (mg/L) | float |
| `ph` | pH | float |
| `temperature` | 温度 (°C) | float |
| `contact_time` | 接触时间 (min) | float |
| `adsorbent_dose` | 吸附剂投加量 (g/L) | float |
| `adsorbent_type` | 吸附剂类型 | category |
| `water_matrix` | 水质背景 | category |
| `removal_efficiency` | 去除率 (%) | float（目标之一） |
| `adsorption_capacity` | 吸附容量 (mg/g) | float（目标之一） |

> 每行至少需要 `removal_efficiency` 或 `adsorption_capacity` 之一作为目标。

然后：

```bash
# 预测去除率（默认）
python scripts/train.py --data /path/to/your.csv --mode transfer

# 预测吸附容量
python scripts/train.py --data /path/to/your.csv --target adsorption_capacity --mode transfer
```

完整字段定义见 `src/shortpfas/data/schema.py`。

### 真实数据接入

本项目已从公开论文提取了三十一个真实数据集（因版权，CSV 不直接入库，用脚本复现）：

| 数据集 | 来源 | 规模 | 内容 | 复现脚本 |
|--------|------|------|------|---------|
| `data/processed/nature_membrane.csv` | Nature Comms 2024 (s41467-024-55320-9) | 534 条 / 21 种 PFAS | 膜去除率，236 条短链 | `scripts/convert_nature_data.py` |
| `data/processed/modified_zeolite.csv` | Clean Technol. 2026 (cleantechnol8010021) | 43 条 / PFBA+PFOA | 改性沸石 vs GAC 去除率，12 条短链 | `scripts/convert_modified_zeolite.py` |
| `data/processed/molecules_biochar.csv` | Molecules 2026 (molecules31071100) | 24 条 / 5 种短链 PFAS | 生物炭/活性炭吸附容量 | `scripts/convert_molecules_biochar.py` |
| `data/processed/graphene_pfhxa.csv` | Sustainability 2026 (su18147053) | 20 条 / PFHxA | 石墨烯吸附容量，20 条短链，4 种水基质 | `scripts/convert_graphene_pfhxa.py` |
| `data/processed/quaternized_chitosan.csv` | Gels 2026 (gels12010014) | 12 条 / PFOS+PFOA+PFBS+PFHxA | 季铵化壳聚糖水凝胶吸附容量+去除率，6 条短链 | `scripts/convert_quaternized_chitosan.py` |
| `data/processed/ix_resin_competitive.csv` | Water 2026 (w18151869) | 10 条 / 10 种 PFAS | IX 树脂竞争吸附容量，6 条短链 | `scripts/convert_ix_resin_competitive.py` |
| `data/processed/banana_peel_biochar.csv` | Toxics 2026 (toxics14030204) | 9 条 / PFBA+PFBS+PFHxA+GenX | 香蕉皮石墨化生物炭去除率，9 条短链 | `scripts/convert_banana_peel_biochar.py` |
| `data/processed/beta_cd_tripod.csv` | npj Clean Water 2025 (s41545-025-00519-6) | 8 条 / 5 种 PFAS | 环糊精聚合物容量+去除率，6 条短链 | `scripts/convert_beta_cd_tripod.py` |
| `data/processed/cu_hismox_mof.csv` | Small 2025 (smll e10000) | 7 条 / 5 种短链 PFAS | Cu-MOF 捕集容量+去除率，7 条短链 | `scripts/convert_cu_hismox_mof.py` |
| `data/processed/fluoropolymer_sorbent.csv` | Nat Commun 2024 (s41467-024-52690-y) | 6 条 / 6 种 PFAS | 氟聚合物树脂吸附容量，4 条短链 | `scripts/convert_fluoropolymer_sorbent.py` |
| `data/processed/reed_straw_biochar.csv` | Sci. Total Environ. 2024 (174223) | 6 条 / PFBA+PFPeA | Fe/Cu 改性芦苇秸秆生物炭容量，6 条短链 | `scripts/convert_reed_straw_biochar.py` |
| `data/processed/alginate_cafe_biochar.csv` | Environ. Res. 2025 (122395) | 3 条 / PFHxA+PFBS+PFBA | 海藻酸 Ca-Fe 生物炭微球容量+去除率，3 条短链 | `scripts/convert_alginate_cafe_biochar.py` |
| `data/processed/polyaniline_nanofiber_genx.csv` | Fibers 2025 (fib13040042) | 3 条 / GenX | PANI 纳米纤维吸附容量 1 条 + 去除率 2 条 | `scripts/convert_polyaniline_nanofiber.py` |
| `data/processed/subnanoporous_biochar_pfba.csv` | Tsinghua 2026 | 1 条 / PFBA | 亚纳米孔活性生物炭 Langmuir 容量 141.8 mg/g | `scripts/convert_subnanoporous_biochar.py` |
| `data/processed/nfbs_pei_magnetic.csv` | ACS Omega 2024 (acsomega.4c07159) | 7 条 / 7 种 PFAS | NFBS-PEI 磁性纳米吸附剂 Langmuir 容量，6 条短链 | `scripts/convert_nfbs_pei_magnetic.py` |
| `data/processed/pmos_pfba.csv` | J. Hazard. Mater. 2023 (131047) | 5 条 / PFBA | 功能化 PMO 介孔有机硅 Langmuir 容量，5 条短链 | `scripts/convert_pmos_pfba.py` |
| `data/processed/cs_pei_xerogel.csv` | Chem. Eng. J. 2023 | 1 条 / PFBS | CS/PEI 干凝胶吸附容量 305 mg/g | `scripts/convert_cs_pei_xerogel.py` |
| `data/processed/mof808_pfbs.csv` | ACS Omega 2025 (acsomega.5c05815) | 8 条 / PFBS | MOF-808 四种衍生物 Langmuir qmax 95–837 mg/g | `scripts/convert_mof808_pfbs.py` |
| `data/processed/pa_microplastics.csv` | Environ. Res. 2023 (114834) | 4 条 / PFBA+PFPeA+PFHxA | PA 微塑料 Langmuir qmax + 去除率 | `scripts/convert_pa_microplastics.py` |
| `data/processed/hydrophobic_pac.csv` | ACS EST Water 2025 (acsestwater.4c01222) | 7 条 / PFBS+PFBA | 疏水化 PAC 动力学容量 + polyDADMAC-GAC 容量 | `scripts/convert_hydrophobic_pac.py` |
| `data/processed/aptes_diatomite.csv` | Sci. Rep. 2026 (s41598-026-41388-4) | 3 条 / PFBS | APTES 硅藻土 Langmuir 容量 + 去除率 + GAC 容量 | `scripts/convert_aptes_diatomite.py` |
| `data/processed/bsa_pei_pfas.csv` | ACS Appl. Mater. Interfaces 2026 (acsami.5c13467) | 3 条 / PFBA+PFBS+GenX | BSA-PEI 蛋白吸附剂实测容量 | `scripts/convert_bsa_pei_pfas.py` |
| `data/processed/gac_f400_competitive.csv` | J. Hazard. Mater. 2023 (132378) | 3 条 / PFBS+4:2FTS+PFBA | GAC F400 单溶质平衡容量 | `scripts/convert_gac_f400_competitive.py` |
| `data/processed/cacbm_pfas.csv` | ACS EST Water 2025 (acsestwater.5c00641) | 4 条 / PFBA+PFBS | 球磨胶体活性炭 Langmuir + PSO 容量 | `scripts/convert_cacbm_pfas.py` |
| `data/processed/fsfac_pfbs.csv` | Chem. Eng. J. 2026 (176796) | 4 条 / PFBS | 氟化超细活性炭 PFBS 去除率 | `scripts/convert_fsfac_pfbs.py` |
| `data/processed/nf_mac_pfpea_pfhxa.csv` | J. Water Process Eng. 2024 (105585) | 10 条 / PFPeA+PFHxA | NF 膜去除率 + PAC/MAC Langmuir qm + PSO qe | `scripts/convert_nf_mac_pfpea_pfhxa.py` |
| `data/processed/sn_porous_carbon.csv` | J. Hazard. Mater. 2026 (141781) | 12 条 / PFBA+PFBS | S/N 功能化多孔碳 Langmuir-Freundlich qm 与 Qe | `scripts/convert_sn_porous_carbon.py` |
| `data/processed/magnetic_polymer_sorbent.csv` | Adv. Mater. 2026 (e02427) | 4 条 / PFBA+PFPeA+PFBS+PFHxS | 非 PFAS 磁性聚合物吸附剂渗滤液去除率 | `scripts/convert_magnetic_polymer_sorbent.py` |
| `data/processed/ppy_carbon_cloth.csv` | Adv. Sci. 2026 (advs.76133) | 3 条 / TFA+PFBA+GenX | PPy@P-CF 导电碳布 Langmuir qm 283–572 mg/g | `scripts/convert_ppy_carbon_cloth.py` |
| `data/processed/ppn6_fndmb.csv` | JACS 2025 (jacs.5c04689) | 2 条 / PFPeA+PFBS | 功能化多孔聚合物网络 PPN-6 平衡容量 607–1050 mg/g | `scripts/convert_ppn6_fndmb.py` |
| `data/processed/beta_cd_go_pfba.csv` | Chem. Eur. J. 2023 (chem.202301854) | 2 条 / PFBA | β-CD-GO 对 PFBA 去除率 65%（vs GAC 70%） | `scripts/convert_beta_cd_go_pfba.py` |

> 总计 768 条（去除率 628 + 吸附容量 155，短链 424 条），覆盖膜 / 生物炭 / 活性炭 / 离子交换树脂 / 纳米吸附剂 / 沸石 / MOF / 聚合物网络 / 蛋白基吸附剂 / 微塑料等吸附剂，以及 PFBA/PFBS/PFPeA/PFPeS/PFHxA/PFHxS/GenX/4:2FTS/TFA 等核心短链物质。

论文 PDF 下载（仅开放获取）：

```bash
python scripts/download_papers.py --doi 10.3390/molecules31071100   # MDPI 走 res.mdpi.com 直链
```

详见 `docs/data_insights.md`（数据洞察）与 `docs/literature_collection.md`（文献采集清单）。

## 迁移学习工作流

针对"短链数据稀缺"的核心设计：

1. **预训练**：在长链/文献 PFAS 数据上训练，让 GNN 学会通用的"分子结构→吸附亲和力"映射。
2. **微调**：在短链实验数据上用更小学习率微调，适配短链特有的弱相互作用。
3. **评估**：在留出的短链测试集上验证，并可用 `leave_one_pfas_out` 评估对**未见分子**的泛化能力。

## 评估指标

- R²（决定系数）、RMSE、MAE
- 短链 vs 长链分组对比
- 不确定性校准（预测区间覆盖率）

## 可解释性

- SHAP 分析工艺条件的特征重要性
- 注意力权重可视化（分子图注意力）
- 链长→去除率的热力图（识别数据缺口）

## 引用

如果你在研究中使用了本项目，请引用（BibTeX 待补充正式发表信息）：

```bibtex
@software{shortpfas_net,
  author = {Stephen},
  title = {ShortPFAS-Net: Multi-modal deep learning for short-chain PFAS removal prediction},
  year = {2026},
  url = {<your-repo-url>}
}
```

## 数据来源与许可

- 演示数据为**合成数据**，仅用于流程验证，不具科学精度，**发表前必须替换为真实数据**。
- 真实数据来自公开论文（Nature Communications、Molecules），由 `scripts/convert_*.py` 从论文补充材料提取；原始数据版权归原论文所有，引用请遵循原始论文许可。
- 代码采用 MIT 许可，详见 [LICENSE](LICENSE)。

## 致谢

本项目借鉴了以下工作的方法论：
- Karbassiyazdi et al. (2022), *Environmental Research* — XGBoost 预测 PFAS 去除
- Singh & Tiwari (2026), *ACS EST Engineering* — ML 解释 PFAS 吸附机制
- MolCLR (2022), *Nature Machine Intelligence* — 分子图对比学习表征
