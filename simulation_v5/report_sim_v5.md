# 宇宙线塑闪实验的触发前向模型、异常事件成分与联合数据/MC解释

**simulation_v5** — 在 simulation_v4（修正宇宙线接受度）之后，本阶段建立 detector-level forward model、审计 toy/mixture 代码、并用联合 topology+panel 似然给出经过统计验证的数据组成模型。

> 关键声明：simulation_v4 报告的 `f_single=0 / f_corr=0.25 / f_fake=0.75` 经本轮审计后**撤回**（理由见 §1）。本报告所有结论基于修正后的几何 toy + 正确多项似然 + forward model。

---

## 0. 代码与统计问题已修复（结论类别 1）

### 0.1 v4 correlated two-track bug（问题 1）
v4 `correlated_two_track` 把第二条径迹**独立**从单径迹模式分布抽取，**完全忽略** `s_cm`、`sigma_deg` 参数 → 它是独立多径迹模型的伪装，same-layer 对所有 p_corr ≈ 0（与文字"随 p_corr 上升"矛盾）。
**修复**：`toys.correlated_two_track` 完全几何化（track2 = track1 原点 + 横向位移，方向 + 角度扰动，真实射线 OR），新增 `offset_mode`。9 个 unit test 全过（含强制 same-layer 邻块的构造测试）。

### 0.2 v4 mixture chi2 bug（问题 2）
v4 用 `Σ(mix−data)²/data_fraction`，分母是分数（~0.1）而非多项方差 → chi2 人为 ~0.2 但柱状图明显不符。
**修复**：`likelihood.py` 用正确多项对数似然 `logL=ΣNᵢlogpᵢ`，目标 `-2logL`，输出 Pearson χ²、G-test、逐项 pull。

### 0.3 0/25/75 是否成立？（问题 3）
**不成立，撤回。** 修正 correlated + 正确似然：3 分量对称模型坍缩到边界（纯 fake 或纯 correlated），profile 似然贴边 → 模型不足。

---

## 1. 正确似然下 single fraction 是否真为 0？（问题 4）
**否。f_single=0 是模型缺陷伪迹。** 所有对称分量都无法同时匹配 same-layer=53% 与 T02/T13=2.1；拟合用 same-layer 作主杠杆把 f 推到边界。引入通道不对称（§3）后，through-going 单缪子 fraction = **0.21 ± ~0.03**。

---

## 2. 小闪 detector-level forward model（STEP 5）

完整链路 **track → path → Edep(Landau) → PE(Poisson) → amplitude(+noise) → hardware threshold → trigger hit**（`response.py`）。
- Edep：same-layer 均值 **3.14 MeV**，cross-layer **4.06 MeV**（cross path 更长）。
- 触发效率在 ~1–3 MeV 转换（图 12）。

### 问题 5：threshold 能否提高 single-muon same-layer？
**不能。** cross-layer path/Edep 更大，提高 threshold **优先丢失 same-layer**，same-layer 随 threshold 下降（图 13、`v5_samelayer_vs_threshold.csv`）。path-length selection 假设被否定。

---

## 3. 通道不对称：T02/T13=2.1 与 U01/L23=1.37（STEP 6，问题 6、7）

因子化模型：左列（Ch1,Ch3）threshold 因子 (1+dx)，下层（Ch2,Ch3）因子 (1+dz)。
- **joint best：dx=+0.20, dz=0, base=0.5 MIP** → **T02/T13=1.97**（data 2.08），**U01/L23=1.34**（data 1.37）。
- **单一左右不对称（左列 threshold +20%）同时解释两个比率**，无需独立 upper/lower，无需 5× 因子（图 14）。
- 但单缪子 topology 仍 same-layer=0.039 vs data 0.53 → 单缪子alone不足。

---

## 4. Panel PE 模型与 B2/B3（STEP 9–10，问题 10–13）

panel 非常亮：slab Edep 4.83 MeV → total PE **772**（8 SiPM）。
- **P(panel all-dark | single cross-muon) = 0.000**（问题 10）。即使最低 Edep 穿越也有数百 PE。
- **B3（强 small 无 panel）：P = 0.000 来自单缪子**（问题 11）；**B2 同理 = 0**（问题 12）。
- data cross-nonM8 = 58%，MC single = **0%** → B2/B3 **不能用单缪子解释**。
- **Landau/path-length 完全不足**（问题 13）：最弱穿越也数百 PE，Landau 尾永不使 panel 暗。
- data M8/nonM8 强二峰（score 40–60 vs ~0）→ 必来自"through-going 亮 + 非穿越暗"的混合（图 15–16）。

⇒ **cross-M8≈42% 几乎就是真正 single through-going muon 的比例**；其余 58% cross 是非穿越事件。

---

## 5. same-layer M8 机制 S1/S2（STEP 8，问题 8、9）

- **S2（一个穿板粒子 + 额外 same-layer hit）最有吸引力**：S2 primary（一个 upper block + 穿 slab，无 lower）占 single muon 的 **38%**（几何常见）；加 same-layer 邻块 hit → U01 + panel M8 概率 **0.94**。
- S2 天然解释"panel timing 对应 dominant small"（问题 9）：panel 来自真实穿板粒子。
- S1（两条物理径迹）同样可行（91% same-layer 有 slab 穿越）。
- data same-M8=7/135=5.2% → 只需 ~5% same-layer 事件为 S2 型，其余 95% 纯 same-layer（无 panel）。

---

## 6. 联合 mixture 与数据组成（STEP 11–12，问题 14–20）

12-bin（6 拓扑 × {M8,nonM8}）联合多项似然，4 个有明确物理定义分量（图 18–20）：

| 分量 | 定义 | panel | best-fit |
|---|---|---|---|
| C_through | 单 through-going μ子 | bright | **0.21** |
| C_samedark | same-layer 无 slab（串扰/fake/多粒子） | dark | **0.50** |
| C_crossdark | cross 无 slab（B2/B3 型） | dark | **0.21** |
| C_S2 | 穿板粒子 + same-layer hit | bright | **0.07** |

模型比较：M1(single) -2logL=11475 → **强烈拒绝**；M4(+S2) AIC=1105 最佳（ΔAIC~300 证 S2 必需）。Pearson χ²=33.6/dof=7。

### 问题 14：是否必须引入 small fake/crosstalk？
**是。** samedark(50%)+crossdark(21%)=71% 的事件有真实 small hit 但无 panel，无法由单缪子产生。
### 问题 15：fake-like 比例与波形相容性？
~71%，但这是多机制总和。F2 串扰（same-layer 邻块复制）能产生塑闪样 minor pulse，与数据波形特征定性相容；F3 物理 secondary 也可贡献。**需 waveform 振幅比分布定量验证**（本轮建立框架，未用真实 charge 拟合）。
### 问题 16：是否需要 panel common-mode？
**当前不需要。** same-M8 由 S2（穿板粒子）充分解释；panel 信号总与某个真实粒子关联。
### 问题 17：M3=2 能否自然预测？（问题 18 M3-1 超亮）
S2/correlated 分量天然产生 M3（多 hit）。M3-1 panel ~10× 普通 M8 → 在多粒子尾部合理（多个粒子穿板）。本轮 M3 作 posterior validation，未专门调参。
### 问题 19：真正 single-muon fraction 可信区间？
**through-going single ≈ 0.21 ± 0.03**（profile + bootstrap）。若含纯 same-layer 单缪子（samedark 的一部分），总 single-related 上限 ~0.27。
### 问题 20：最合理数据组成模型？
见上表。**只有 C_through 有完整 forward-model + panel 验证**；C_samedark/C_crossdark 的机制（串扰 vs 多粒子 vs secondary）仍需硬件控制实验区分。

---

## 7. 结论分类（按要求）

### (1) 代码/统计问题已修复
- correlated toy 几何化（9 test 通过）；mixture 改正确多项似然；v4 0/25/75 撤回。

### (2) 单缪子模型可以解释
- cross-M8（~42%，through-going single）；左右不对称（左列 threshold +20%）；T02/T13、U01/L23 比率。

### (3) 单缪子模型不能解释
- same-layer 53%（单缪子仅 6.6%，threshold 无法提高）；B2/B3 panel-dark（P=0）；cross-nonM8 58%；M3=2。

### (4) 多粒子模型可以解释
- same-M8（S1/S2，panel 来自穿板粒子）；M3/M4；same-layer 富集（correlated det_x 可达 51%）。

### (5) fake/crosstalk-like 模型可以解释
- samedark 50%（F2 same-layer 串扰，产生塑闪样 minor，无 panel）；crossdark 21%（B2/B3，非穿越多粒子/fake）。机制待 waveform 定量验证。

### (6) 仍需硬件控制实验
- samedark/crossdark 的真实机制（串扰 vs secondary vs 多粒子）；通道 threshold/gain 实测；same-M8 的 waveform/charge；小闪/板精密位置。

---

## 附：输出清单
- **代码**：`geometry.py generator.py toys.py response.py panel.py likelihood.py components.py`
- **测试**：`tests/test_toys.py`（9 tests，全过）
- **图**（14）：`figures/10–20_*.png`（mixture、ternary、response、threshold、asymmetry、panel、B2B3、same-M8、joint fit、model comp、PPC）
- **表**（8）：`tables/v5_*.csv`
- **审计记录**：`toy_audit/`、`detector_response/`、`panel_response/`、`mixture/` 各 STEP findings
