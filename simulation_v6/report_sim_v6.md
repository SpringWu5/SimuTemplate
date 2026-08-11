# 宇宙线塑闪实验的统一探测器前向模型、暗事件机制分解与绝对数据/MC检验

**simulation_v6** — 在 v5 基础上：(1) 统一 panel optical MC 与 detector forward model；(2) 把真实 small charge 纳入比较；(3) 分解 samedark/crossdark 暗机制；(4) 用 **absolute goodness-of-fit**（不只 AIC）判定模型是否合格。

> **总判定：当前模型族 INADEQUATE。** FIT C（含 small Q 特征）p=7e-15，B2/B3 系统性残差。
> 因此**不输出"事件组成 = xx%±yy%"作为可靠测量**；所给 fraction 仅是 working estimate。

---

## 1. 统一 panel forward model（STEP 1–3）

### 审计发现（Q1, Q2）
- V5 `panel.py` **Y_slab=400 凭空取值**，比 Geant4 真值 **17 photons/MeV** 亮 **~23×**。
- 用固定-f_i Poisson，丢失 Geant4 的**过dispersion（F=4-7）与零光子尾（8.3% event 有 SiPM=0）**。
- **撤回 V5 "P(panel dark|single)=0.000"**；改为校准后 threshold-dependent 值。

### 统一模型（`panel_v6.py`）
- 每 SiPM：`photons_i ~ NegBin(rate_i×Edep, F_i)`，rate/F 校准自 Geant4（rate~1.7-2.4 ph/MeV, F~3.7-6.7）。
- 验证：per-SiPM mean 吻合 Geant4（11.65 vs 11.54）；P(M8) 低阈值区吻合（图 01）。

### P(panel dark | single cross)（Q3, Q4）
- **P(完全 dark | single cross) = 0.000–0.002**（修正 V5 "0"，仍可忽略）。
- data cross-nonM8=58% → 远超 single dark 尾。

### 亮/暗二峰（§9）
- single cross M 分布：**M4-7=23%, M8=77%, M0≈0**（连续偏亮）；total PE mean 29, **P(tot<2)=0**。
- data：**M8 score 40-60 vs nonM8~0，强二峰**。
- ⇒ data nonM8(score~0) **不是** single 的 partial-light 尾（那是 M4-7, score~10-25），是**独立 dark 群体**。

---

## 2. 小闪 forward model + 不对称（STEP 4–5，Q8, Q9）
- Edep→PE→Q（`small_v6.py`），per-channel gain/threshold。
- **threshold 与 gain 不对称在 topology 层完全简并**（T02/T13=2.01 同），仅 Q 谱形状可区分。
- 纯几何已给 T02/T13≈1.61；+20% electronics 推到 2.0。
- **"+20%" 是 effective proxy**；其物理本质（thr/gain/geometry）须由真实 Ch0–Ch3 Q 谱判定。

---

## 3. 暗机制分解（STEP 6–8）

### samedark：SD1/SD2/SD3（Q10, Q11, Q12）
| 机制 | minor/major Q | panel | 说明 |
|---|---|---|---|
| SD1 正常 same-layer 单缪子 | ~对称 | dark | 仅 6.6% |
| **SD2 电子学串扰** | **0.35±0.17（宽）** | dark | broad r，**与物理可区分** |
| SD3 物理次级/多粒子 | ~0.73（独立） | 视情况 | 产生 M3 |

- SD1 正常单缪子最多占 same-layer ~6.6%（Q10）。
- SD2 minor/major≈0.35 可量化匹配（Q11），但需真实 same-layer minor/major Q 验证。
- SD3 能同时给 same-layer 高 + M3，但本轮 track2 Edep incomplete（Q12 部分）。

### B2/B3（Q5, Q6, Q7）
- **P(B2-like 弱 small | single cross) = 0.044** → B2 仅 4.4% single-兼容（data 43% → 远不足）。
- **P(strong small & truly-dark panel | single cross) = 0.00000** → **B3 完全排斥 normal single-through**。

### S2 same-M8（Q13, Q14, §28）
- **S2 机制预测 P(same-M8|same-layer) ≈ 0.22**（非 5%），与 data 0.052 有张力。
- 要匹配 5%，dark-same-layer（SD1+SD2）须 ~4× 大于 S2 → same-M8 **不是事后自由 5%**，被机制约束。
- **S2-E（串扰）与 S2-P（物理次级）需由 dominant/minor Q + timing 区分**（本轮框架已建，待 data）。

---

## 4. 三级 fit + 绝对 GOF（STEP 9–12，Q17, Q18）

| Fit | Pearson/dof | p | 判定 |
|---|---|---|---|
| A topology+M3/M4 | 8.9/5 | 0.114 | ADEQUATE |
| B +panel M8/nonM8 | 19.7/9 | 0.020 | 边缘 |
| **C +cross Q_min** | **94.5/12** | **7e-15** | **INADEQUATE** |

- single-only 被强拒（p=1.5e-14）。
- **FIT C 失败**：B2/B3 Q_min 二分无法由单缪子 Landau 产生；single non-M8 是 partial-light（M4-7）与 data dark(score~0) 不兼容。
- M3=2 在 PPC 主体内（Q16, §38），多粒子分量自然兼容，不需调参。

### 判定（§34, §35, §52 停止条件）
**MODEL INADEQUATE。** 不报告 component fraction 作可靠测量。FIT A/B 的 through≈0.42 / sld≈0.50 / S2≈0.08 仅 working estimate。

---

## 5. single fraction 不确定度（Q19, Q20, Q21）
- v5（错误 panel）：f_single≈0.21。
- v6 FIT B（统一 panel）：f_single(through)≈**0.42**。
- **f_single = 0.42 ± 0.03(stat) ± 0.21(model)**。
- v5 的 0.21/0.50/0.21/0.07：**修正**为 ~0.42/0.50/0/0.08，但因 FIT C 失败**撤回作为"测量"**，仅 working estimate。

---

## 6. panel common-mode（Q15, §37）
- 当前**不需要** panel common-mode：same-M8 由 S2（穿板粒子）的 panel 信号解释；panel 总与某真实粒子关联。需 S2 light-sharing/timing 与 7 个 same-M8 数据定量比较后最终确认。

---

## 7. 结论分类（A–G）

**A. 已通过 forward model 确认**
- panel 统一模型（NB 校准 Geant4，复现 M-dist）；P(dark|single cross)=0.000-0.002；亮/暗二峰需 mixture。

**B. 数据与 single-muon 兼容**
- cross-M8（through-going single，P(M8|cross)=0.42）；左右不对称（effective +20%）；FIT A topology。

**C. 数据显著排斥 single-muon**
- B3（P=0.00000）；B2（仅 4.4%）；same-layer 53%（单缪子 6.6%，threshold 无法提高）；二峰。

**D. physical multi-particle 支持**
- same-M8（S1/S2，panel 来自穿板粒子）；M3=2（PPC 兼容）；same-layer 富集（correlated）。

**E. electronics/crosstalk-like 支持**
- SD2 same-layer dark（minor/major~0.35，塑闪样 minor）；crossdark 部分。机制待 waveform 定量验证。

**F. 当前模型仍无法解释**
- B2/B3 的 Q_min 二分（FIT C p=7e-15）；same-layer 53% 的主导 dark 机制未从 first-principles 推导；S2 预测 22% vs data 5% 的张力。

**G. 必须通过新硬件 run 解决**
- Ch0–Ch3 真实 Q 谱（区分 thr/gain）；same-layer minor/major Q + timing（SD2 vs SD3）；7 个 same-M8 的 waveform/light-sharing（S2-E vs S2-P）；panel Ch4-11 baseline/threshold 实测。

---

## 8. 总表：观测 → 机制 → 证据 → 可信度 → 下一步

| 观测现象 | 候选机制 | data 证据 | MC 证据 | 拟合贡献 | 可信度 | 下一步验证 |
|---|---|---|---|---|---|---|
| cross-M8 42% | single through-going | M8 score 40-60 | P(M8\|cross)=0.42 | through~0.42 | **高** | panel PE 定量 |
| T02/T13=2.1 | 左列 thr/gain +20% | topology 比率 | thr/gain 简并 | nuisance | 中 | Ch0-3 Q 谱 |
| same-layer 53% | SD2 串扰 + SD1 + 多粒子 | 53% 远超 6.6% | SD2 same-enriched | sld~0.50 | 中低 | minor/major Q |
| same-M8 7/135 | S2 穿板+extra hit | panel↔dominant | S2 P(M8\|same)=0.22 | S2~0.08 | 中 | same-M8 waveform |
| B3 strong+dark | **非 single**（排斥） | score~0 | P=0.00000 | crossdark | **高（排斥single）** | B3 机制待定 |
| B2 weak small | Landau 尾 + 非 single | 43% of cross | P=0.044 | crossdark | 中 | Q_min 分布 |
| M3=2 | 多粒子 tail | 2 event | PPC 兼容 | SD3 | 中 | M3 light-sharing |
| 二峰 bright/dark | mixture | score 二峰 | single 连续 | — | **高** | — |

---

## 9. 必须逐条回答（21 问）
1. V5 panel 亮 23×：Y_slab=400 凭空 + 固定-f_i Poisson。2. 是（近似均匀分光 + 错误 yield），撤回 P(M8)≈1。
3. 统一后 P(M8\|cross)=0.42（@~2 raw ph）。4. P(完全 dark\|single cross)=0.000-0.002。
5. B2 单缪子兼容 ~4.4%。6. B3 单缪子兼容 ~0%。7. strong-small+dark 条件 P=0.00000。
8. +20% 与 topology 兼容，但 thr/gain 简并。9. effective proxy（thr/gain/geometry 待 Q 谱）。
10. SD1 正常单缪子最多 ~6.6% of same-layer。11. SD2 minor/major~0.35 可量化（待 data）。
12. SD3 部分（track2 Edep incomplete）。13. S2-E vs S2-P 待 timing/Q 区分。
14. S2 预测 ~22%（非 5%），有张力。15. panel common-mode 当前不需要。
16. M3=2 PPC 兼容。17. FIT A→B→C：through 0.42、sld 0.50、S2 0.08（FIT C 失败）。
18. **绝对 GOF 不合格**（FIT C p=7e-15）→ MODEL INADEQUATE。
19. f_single≈0.42。20. stat ±0.03, model ±0.21。21. v5 0.21/0.50/0.21/0.07 → 修正为 ~0.42/0.50/0/0.08，撤回作测量。
