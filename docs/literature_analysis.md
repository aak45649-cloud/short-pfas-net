# 文献数据分析报告

> 生成日期：2026-10-24
> 分析对象：已下载的 3 篇核心论文（PDF 全文已提取文本）

---

## 一、核心结论

1. **数据现实**：PFAS 吸附/去除的原始数据**没有统一公开数据集**，都散落在论文补充材料里；部分论文（如 Karbassiyazdi 2022）甚至要求签署材料转让协议才提供原始数据。这印证了短链 PFAS 数据稀缺是真实痛点，也正是本项目"小样本 + 迁移学习"定位的价值所在。
2. **方法论高度一致**：三篇论文（尤其 XGBoost 2022 和 Nature 膜 2024）用的输入特征与我们 schema **完全对齐**——PFAS 初始浓度、pH、温度、接触时间、吸附剂剂量。我们的字段设计方向正确。
3. **差异化机会确认**：现有 ML 工作（XGBoost/RF）只用**表格特征**，或用**手工分子描述符**（分子量、pKa、log Kow），**没有一篇**把 PFAS 分子图（GNN）纳入建模。这仍是我们可切入的空白。

---

## 二、逐篇分析

### 论文 1：Karbassiyazdi et al. (2022) — XGBoost 预测 PFAS 去除
- **期刊**：Environmental Research，DOI 10.1016/j.envres.2022.114286
- **数据规模**：64 篇论文 → 234 条 PFAS 记录（2008–2021）
- **输入特征**：吸附剂类型、吸附剂浓度、颗粒粒径、PFAS 类型、PFAS 初始浓度、pH、温度、平衡时间
- **目标变量**：吸附容量 qe (mg/g)、去除率 R (%)、平衡时间 te
- **方法**：XGBoost，用 SHAP 解释
- **关键发现**：pH 和颗粒粒径是去除率最重要的因素；吸附剂类型主导 qe；离子交换树脂和活性炭 qe 最高
- **数据可得性**：⚠️ **原始数据不公开**，需材料转让协议索取
- **对我们的价值**：
  - 特征定义可直接参考（我们的 schema 已对齐，但**缺少"颗粒粒径"字段**，可考虑补充）
  - 公式 (1)(2) 给出了去除率与吸附容量的换算关系，可用于补全缺漏数据

### 论文 2：Nature Communications (2024) — ML + 分子模拟解释膜去除 PFAS
- **DOI**：10.1038/s41467-024-55320-9（被引 97 次）
- **数据规模**：21 种 PFAS、16 种膜
- **方法**：ML（XGBoost 等）+ 分子动力学模拟；SHAP 解释
- **关键发现**：分子量、pKa、log Kow 等描述符主导；磺酰胺基团（如 PFHxS）因负电荷更高而更难去除
- **数据可得性**：✅ **提供 Source Data**（在 Nature 论文页面的 Supplementary 里，通常为 Excel/CSV）
- **对我们的价值**：这是**最值得深挖的一篇**——它的 21 种 PFAS 里含多个短链，且有分子描述符，可直接映射到我们的 schema；Source Data 可尝试直接下载。

### 论文 3：Nature Communications (2024) — 氟聚合物吸附剂捕获 PFAS
- **DOI**：10.1038/s41467-024-52690-y
- **关键内容**：HFPO-DA（GenX，短链替代物）吸附，对比 GAC/IEX
- **对我们的价值**：含 GenX 等新型短链 PFAS 数据，可补充短链样本多样性

---

## 三、对我们的模型设计的启示

| 启示 | 具体行动 |
|------|---------|
| 补充特征 | schema 增加 `particle_size`（吸附剂粒径，nm），XGBoost 论文证明它是关键变量 |
| 分子描述符可作为 GNN 的补充 | 在 GNN 编码之外，可并行加入分子量/pKa/log Kow 等描述符，与 Nature 方法对比 |
| 目标变量关系 | 利用 qe 与 R 的换算公式，当论文只给其中一个时自动补全另一个 |
| 可解释性对标 | 我们的 SHAP 分析可与这两篇的结论交叉验证（pH、吸附剂类型是否同样主导） |

---

## 四、下一步行动清单

1. **尝试下载 Nature 膜的 Source Data**：访问论文页面 https://www.nature.com/articles/s41467-024-55320-9 的 Supplementary Information，找 Source Data 文件（xlsx/csv），摘录 21 种 PFAS × 16 膜的去除数据。
2. **批量下载新检索的 OA 论文**（见 literature_collection.md 补充清单，尤其 4 篇 ★★★ 短链论文）。
3. **schema 补充 particle_size 字段**（需同步更新 schema.py、demo_data.py、dataset.py）。
4. **摘录数据**：优先从 Nature Source Data 和 ★★★ 短链论文的补充材料开始。

---

## 附：三篇论文的数据表格定位线索

- XGBoost 2022：Table 1（输入/输出参数统计）在第 13 页附近；原始数据不公开。
- Nature 膜 2024：Supplementary Table 2（分子描述符）、Supplementary Fig 2-10；Source Data 单独提供。
- Nature 氟聚合物 2024：正文含 GAC/IEX 对比数据，补充材料见论文页。
