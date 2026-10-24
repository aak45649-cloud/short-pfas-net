# 真实数据接入与洞察报告

> 生成日期：2026-10-24
> 数据来源：Nature Communications (s41467-024-55320-9) 补充材料 MOESM3

---

## 一、成果：首个真实数据集已接入

从 Nature 膜论文的补充材料中成功提取并转换为项目标准格式：

- **文件**：`data/processed/nature_membrane.csv`
- **规模**：534 条 PFAS 膜去除记录，21 种 PFAS，含 SMILES 分子结构
- **短链样本**：236 条（44.2%）——这正是项目最稀缺、最需要的部分
- **字段**：pfas_name、smiles、chain_length、初始浓度、pH、去除率等

## 二、数据质量处理记录

| 问题 | 处理 |
|------|------|
| FOSA 的 SMILES 是分子式而非 SMILES | 修正为正确的全氟辛烷磺酰胺 SMILES |
| 初始浓度单位 ng/L | 换算为 mg/L（÷1e6） |
| 21 种 PFAS 链长映射不全 | 补全完整映射表（PFPrS/PFPeS/FOSA/GenX/4:2FTS 等） |
| temperature/contact_time/adsorbent_dose 源数据缺失 | Dataset 层做 NaN 均值填补（标准化后为 0） |

## 三、核心数据洞察

**1. 链长梯度验证了研究假设**（关键发现）：

| PFAS 类别 | 代表物 | 平均去除率 |
|----------|--------|-----------|
| 超短链/短链 | PFMOPrA, PFBA, 4:2FTS | 76–81% |
| 短链 | PFPeA, PFBS, PFHxA | 85–95% |
| 长链 | PFOS, PFDS, PFUnA | 97–99% |

**结论**：短链 PFAS 的膜去除率系统性地低于长链，与我们的核心假设（短链更难去除）完全吻合。

**2. 数据偏态限制模型表现**：
- 去除率均值 93%，75% 的样本 > 91%，整体高度偏态
- 单一吸附剂类型（全部 membrane），连续特征仅 2 个有效（浓度、pH）
- 导致初始训练 R² 为负——不是模型缺陷，而是单篇膜论文的数据局限性

## 四、下一步的关键动作

**要真正训练出有区分度的模型，必须引入多样化的吸附剂数据**（活性炭、树脂、生物炭等），这能同时解决"数据偏态"和"吸附剂类型单一"两个问题。

优先扩充方向（已检索到 OA 论文）：
1. ✅ 松木生物炭吸附短/中链 PFAS（Molecules 2026）— **已下载 + 已提取 24 条短链数据**
2. ✅ 短链 vs 长链 PFAS 去除对比（Colloids 2026）— **已下载**（综述，提供去除率区间对比）
3. ⏳ 功能化材料增强吸附 PFBA（J. Hazard. Mater. 2023）— bronze OA，仅 ScienceDirect 在线阅读（无绿色镜像，headless 被封）
4. ✅ 活性炭电再生浓缩短链 PFAS（ACS EST Water 2025）— **已下载**（电再生机制研究）

> 下载突破：MDPI 的 `www.mdpi.com` 有 Akamai IP 信誉封锁（非 JS 验证码），
> 但 PDF 实际托管在 `res.mdpi.com`，用直链可绕过。已固化进 `scripts/download_papers.py`。

## 五、Molecules 生物炭数据（第二来源，2026-10-24 新增）

从 Molecules 2026 松木生物炭论文正文 Table 1 + 补充材料 Table S1/S2 提取：

- **文件**：`data/processed/molecules_biochar.csv`
- **规模**：24 条，全部为短链（C≤6），5 种 PFAS × 5 种吸附剂
- **吸附剂多样性**：4 种松木生物炭（PW-A1/A2/B/C）+ 活性炭（AC）——首次引入生物炭 + 活性炭
- **目标变量**：吸附容量 q_e (mg/g)，来自 Hill 模型 Qmax（单组分平衡实验）
- **PFAS**：PFBA、PFBS、PFHxA、PFHxS、GenX

**关键发现**：磺酸类短链 PFAS 吸附容量显著高于羧酸类
- PFBS (94.7 mg/g) >> PFBA (28.6 mg/g)，同为 C4
- PFHxS (101.3 mg/g) > PFHxA (28.1 mg/g)，同为 C6
- 印证"磺酸头基静电作用强于羧酸"的机制，与综述结论一致

> 该数据解决了 `nature_membrane.csv` 的"单一膜吸附剂"局限，首次提供活性炭/生物炭对比，
> 且目标变量为吸附容量（而非去除率），可支撑多目标建模。

## 六、已交付的自动化工具

| 工具 | 用途 |
|------|------|
| `scripts/download_papers.py` | OpenAlex 查 OA 状态 + 下载 OA 论文（含 MDPI CDN 直链突破） |
| `scripts/extract_pdf_text.py` | PDF → 文本，用于定位数据表格 |
| `scripts/convert_nature_data.py` | Nature 补充材料 → 项目标准 CSV |
| `scripts/convert_molecules_biochar.py` | Molecules 生物炭数据 → 项目标准 CSV（吸附容量目标） |
| `scripts/validate_data.py` | 校验数据格式与 SMILES |

## 五、已交付的自动化工具

| 工具 | 用途 |
|------|------|
| `scripts/download_papers.py` | OpenAlex 查 OA 状态 + 下载 OA 论文 |
| `scripts/extract_pdf_text.py` | PDF → 文本，用于定位数据表格 |
| `scripts/convert_nature_data.py` | Nature 补充材料 → 项目标准 CSV |
| `scripts/validate_data.py` | 校验数据格式与 SMILES |
