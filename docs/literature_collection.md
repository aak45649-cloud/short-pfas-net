# 文献数据采集清单（Literature Data Collection List）

> 用途：从以下论文的**补充材料（Supplementary Information）**中摘录 PFAS 吸附/去除数据，
> 填入 `data/literature_template.csv`。数据以吸附容量 q_e (mg/g) 或去除率 R (%) 为目标变量。

## 字段说明

摘录时需记录：PFAS 名称、SMILES、链长、初始浓度 C0 (mg/L)、pH、温度 (°C)、
接触时间 (min)、吸附剂剂量 (g/L)、吸附剂类型、水质背景、去除率 (%)、吸附容量 (mg/g)、来源 DOI。

## 优先级说明

- ★★★ = 明确含**短链** PFAS（C≤6）数据，最优先
- ★★ = 含多种 PFAS（含部分短链），次优先
- ★ = 主要为长链，可用于迁移学习预训练

---

## 第一优先级：短链 PFAS 数据（★★★）

| # | 论文 | 期刊/年份 | 关键内容 | 补充材料 |
|---|------|----------|---------|---------|
| 1 | Karbassiyazdi et al. "XGBoost model as an efficient machine learning approach for PFAS removal" | Environmental Research, 2022 | 234 条 PFAS 去除数据，含多种吸附剂 | DOI: 10.1016/j.envres.2022.114286 |
| 2 | Singh & Tiwari "Machine-Learning-Enabled Interpretation of PFAS Adsorption Mechanisms using KF" | ACS EST Engineering, 2026 | 238 条 harmonized 数据，含短链缺口分析 | DOI: 10.1021/acsestengg.6c00099 |
| 3 | "Cooperative Molecular Interaction-Based Highly Efficient Capturing of Ultrashort- and Short-Chain PFAS" | ERDC, 2025 | PFBS/PFHxS 等短链，纳米吸附剂，~100% 去除 | ERDC 出版物库 |

## 第二优先级：多 PFAS 混合数据（★★）

| # | 论文 | 期刊/年份 | 关键内容 | 补充材料 |
|---|------|----------|---------|---------|
| 4 | "Elucidating governing factors of PFAS removal by polyamide membranes using ML and molecular simulations" | Nature Communications, 2024 | 膜过滤去除，多 PFAS 化合物 | DOI: 10.1038/s41467-024-55320-9 |
| 5 | "Fluoropolymer sorbent for efficient and selective capturing of PFAS" | Nature Communications, 2024 | HFPO-DA 等短链替代物吸附 | DOI: 10.1038/s41467-024-52690-y |

## 第三优先级：长链为主（迁移学习预训练用）（★）

| # | 论文 | 期刊/年份 | 关键内容 |
|---|------|----------|---------|
| 6 | Biochar 吸附 PFAS 综述类（含 ANN/SVM/ANFIS 案例） | Wiley, 2024-2025 | 生物炭吸附数据汇编 |
| 7 | "Data-driven predictive estimation of PFAS" | J. Hazardous Materials Advances, 2025 | 数据驱动预测估算 |

## 补充：OpenAlex 检索到的更多开放获取论文（2026-10-24 新增）

以下论文均为开放获取（gold/green/hybrid），可用 `scripts/download_papers.py --doi <DOI>` 下载。按短链相关度排序：

| 优先 | 期刊/年份 | DOI | 关键内容 | 下载状态 |
|------|----------|-----|---------|---------|
| ★★★ | Colloids (MDPI), 2026 | 10.3390/colloids10050066 | 短链 vs 长链 PFAS 去除对比 | ✅ 已下载（综述，`colloids_short_vs_long.pdf`） |
| ★★★ | Molecules (MDPI), 2026 | 10.3390/molecules31071100 | 松木生物炭吸附短/中链 PFAS | ✅ 已下载 + 已提取 24 条数据（`molecules_pinewood_biochar.pdf`） |
| ★★★ | J. Hazard. Mater., 2023 | 10.1016/j.jhazmat.2023.131047 | 功能化材料增强吸附短链 PFBA | ⏳ bronze OA，无绿色镜像，需图书馆/ScienceDirect |
| ★★★ | ACS EST Water, 2025 | 10.1021/acsestwater.5c00819 | 活性炭电再生浓缩短链 PFAS | ✅ 已下载（`acs_estwater.pdf`，电再生机制） |
| ★★ | Water Research, 2019 | 10.1016/j.watres.2019.115381 | 吸附法去除 PFAS（经典） | ⏳ 机构镜像被 Cloudflare 拦截 |
| ★★ | J. Hazard. Mater., 2023 | 10.1016/j.jhazmat.2023.132522 | COF 去除典型 PFAS | ⏳ SSRN 预印本被 Cloudflare 拦截 |
| ★★ | Small (Wiley), 2025 | 10.1002/smll.202510000 | MOF 捕获短/长链 PFAS | ⏳ PMC reCAPTCHA 拦截 |
| ★★ | J. Mater. Chem. A, 2025 | 10.1039/d5ta07539d | MOF 孔功能化吸附 PFAS | ⏳ 无绿色镜像 |
| ★★ | ACS EST Water, 2025 | 10.1021/acsestwater.5c00343 | 温度对活性炭吸附 PFAS 的影响 | ✅ 已下载（`acsestwater_temp.pdf`，WUR 镜像；SI 需 ACS 官网） |
| ★ | Chemosphere, 2023 | 10.1016/j.chemosphere.2023.140600 | 水中 PFAS 吸附 | ⏳ closed OA，需图书馆 |

## 第三批：MDPI 多吸附剂数据（2026-10-25 新增，全部已下载）

| 期刊/年份 | DOI | 关键内容 | 提取状态 |
|----------|-----|---------|---------|
| Nat Commun, 2024 | 10.1038/s41467-024-52690-y | 氟聚合物 PFPE-IEX+ 树脂吸附 11 种 PFAS（含短链） | ✅ 已提取 6 条（`fluoropolymer_sorbent.csv`） |
| Sustainability, 2026 | 10.3390/su18147053 | 石墨烯吸附 PFHxA（短链，4 种水基质） | ✅ 已提取 20 条（`graphene_pfhxa.csv`） |
| Water, 2026 | 10.3390/w18151869 | IRA900 树脂多组分竞争吸附 10 种 PFAS | ✅ 已提取 10 条（`ix_resin_competitive.csv`） |
| Materials, 2024 | 10.3390/ma17174169 | 松木/椰枣生物炭吸附 6 种 PFAS | ⏳ SI 仅 Freundlich KF（不可比单位），暂不提取 |
| Separations, 2026 | 10.3390/separations13100276 | 先进生物炭去短链 PFAS | ⏳ perspective 综述，无原始数据 |
| Fibers, 2025 | 10.3390/fib13040042 | PANI 纳米纤维吸附 GenX | ✅ 已提取 3 条（`polyaniline_nanofiber_genx.csv`） |
| Clean Technologies, 2026 | 10.3390/cleantechnol8010021 | 改性沸石吸附 PFAS | ✅ 已提取 43 条（`modified_zeolite.csv`，含 zeolite 新类别） |

> 完整 20 篇清单见检索记录；上表为高价值精选。

---

## 常见短链 PFAS 的 SMILES（可直接复制）

| 名称 | 缩写 | 链长 | SMILES |
|------|------|------|--------|
| Perfluorobutanoic acid | PFBA | 4 | `FC(F)(F)C(F)(F)C(=O)O` |
| Perfluorobutanesulfonic acid | PFBS | 4 | `FC(F)(F)C(F)(F)S(=O)(=O)O` |
| Perfluoropentanoic acid | PFPeA | 5 | `FC(F)(F)C(F)(F)C(F)(F)C(=O)O` |
| Perfluorohexanoic acid | PFHxA | 6 | `FC(F)(F)C(F)(F)C(F)(F)C(F)(F)C(=O)O` |
| Perfluorohexanesulfonic acid | PFHxS | 6 | `FC(F)(F)C(F)(F)C(F)(F)C(F)(F)S(=O)(=O)O` |
| HFPO-DA (GenX) | GenX | 3 | `OC(=O)C(F)(F)OC(F)(C(F)(F)F)C(F)(F)F` |

> 注：以上 SMILES 需用 RDKit 校验后再入库（`python scripts/validate_data.py` 会自动检查）。

## 采集建议

1. **优先摘录补充材料里的表格数据**，而非正文图（图难以准确读值）。
2. 每条数据记录完整的**工艺条件**（pH、C0、剂量、温度、时间），缺一不可——这是模型输入。
3. 同一篇论文若含多组实验条件，**每条条件单独一行**。
4. 摘录 50-100 条后，先跑一次 `python scripts/validate_data.py` 校验格式，再继续。

## 如何获取论文

- 通过**清华大学图书馆**的数据库入口（Web of Science / Elsevier / ACS / Nature），
  用你的校园账号登录后下载正文 + 补充材料。
- 注意遵守清华图书馆的使用条款：仅供个人研究，不得批量转存或再分发。
