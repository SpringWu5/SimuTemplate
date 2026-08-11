# 宇宙线塑闪实验非单粒子暗事件机制、联合波形前向模型与数据/MC闭环检验

**simulation_v7** — 在 v6 基础上：(1) 审计并修复统计/PPC 内部不一致；(2) 验证 panel 8 通道联合统计；(3) 审计左右几何；(4) 尝试读取真实 data feature。

> **总判定：MODEL INADEQUATE。** same-M8 PPC P(N≤7)=0.004（< 0.01）；FIT C/D 因真实数据未提供而无法完成。**不报告事件组成 fraction 作测量。**

---

## 1. 统计审计（STEP 1，Q1, Q2）

### V6 FIT A 不一致 — 已解决
V6 正文 "8.9/5 p=0.114" vs 图 "9/3 p=0.03"。**根因：同一 Pearson，退化多余 component 改变 dof。** 审计后 stats_v7（`dof = K_eff − 1 − (C−1)`，6 unit-test 全过，p-value 在 truth 下 ~Uniform(0,1)）：

| 模型 | Pearson | dof | p | AIC |
|---|---|---|---|---|
| 1-comp single | 75.8 | 4 | 0.0000 | 9668 |
| **2-comp (AIC best)** | **10.4** | **5** | **0.065** | **884** |
| 4-comp | 10.4 | 3 | 0.016 | 888 |

- **Q1**: FIT A 真 p = 0.065（2-comp, AIC-best），topology 边缘 adequate。
- **Q2**: 不一致来自退化 component 的 dof；图用 4-comp(dof=3)，正文用 2-comp(dof=5)。
- unit test 验证：错误模型 >80% 被拒；grid_fit 恢复 input fraction；PPC 覆盖 truth。

## 2. PPC 量化（STEP 1，Q3, Q4）

**M3 PPC**（`figures/01_stats_audit.png`）：
- median=2，68%=(1,3)，95%=(0,5)，**P(N=2)=0.271**，P(N≥2)=0.61。
- data M3=2 **在 95% 区间内**。
- **Q3**: V6 "M3 自然兼容"**正确**。

**same-M8 PPC**：
- median=17，68%=(13,21)，95%=(10,25)，**P(N≤7)=0.004**。
- data same-M8=7 **超出 95% 区间**（0.4% 尾）。
- **Q4**: 当前模型 **overpredict same-M8**（预测 ~17 vs data 7）→ S2 rate 张力量化为 P=0.004。**该 observable 失败（< 0.01）。**

## 3. panel 联合统计（STEP 2，Q5, Q6）
独立 NB vs Geant4 8-channel（`panel_joint/STEP2-4_findings.md`）：
- per-channel mean 吻合；**NB 过估 zero-frac（0.039 vs 0.008）和 min-P(0)（0.19 vs 0.08）**。
- ⇒ NB 对 "panel dark" 是**保守上界**。B2/B3 结论（single essentially never dark）**稳健**。
- **Q5**: 独立 NB **不完全**复现 joint（过估零尾、略低 P(M8)=0.59 vs 0.68）。
- **Q6**: 升级方向 = Geant4 event-level resampling；本轮 NB 足够支撑 B2/B3，不用于精确 M8 率。

## 4. 左右几何审计（STEP 4，Q21, Q22）
detector 坐标严格镜像对称（Ch0 x=+6, Ch1 x=−6, slab 居中）。高统计 mirror test（30M）：
- **T02/T13 = 1.014 ± 0.020**（z=0.5σ）。**Q22: mirror geometry 恢复 T02/T13≈1**。
- **Q21**: V6 "pure geometry 1.61" **是低统计伪影**。
- ⇒ **data 左右不对称（2.08）完全是 electronics，非几何。** 统一称 "left/right effective response asymmetry"（§47）。

## 5. real data feature — BLOCKED（STEP 3）
repo 中**无** analysis_v4/ 或 event_features CSV。**真实 Q_min/Q_balance/minor-major/timing/template-score 未提供。**
⇒ data feature book（§18）、SD2/SD3/B2/B3/S2 的**真实 Q/timing 比较**、FIT C/D 的 Q-特征 likelihood **均无法完成**。
这是本轮**硬阻塞**；以下机制结论继承 v6 并标注 "forward-model only, 未与真实 waveform 闭环"。

---

## 6. 继承的机制结论（v6，标注可信度）
- **B3**：P(strong small & truly-dark | single cross) = 0.00000 → **single 被排斥**（高可信，NB-conservative）。
- **B2**：P(weak | single cross) = 0.044 → 仅 4.4% single-兼容。
- **SD2 electronics**：minor/major≈0.35（forward-model 预测；**未与真实 waveform 闭环** → §22/§23 要求的脉冲形状验证未完成）。
- **S2**：预测 same-M8 ≈ 22%（**与 data 5% 有 4× 张力，PPC P≤7=0.004 证实**）。
- **same-layer dark 53%**：SD1 normal single 仅 6.6%；主导机制仍未从 first-principles 推导。

## 7. 结论分类（A–I）

**A. 已通过代码审计确认**：FIT dof/p 公式（unit-tested）；M3 PPC 兼容（P=0.27）；panel NB 对 dark 保守；几何左右镜像对称。

**B. normal single 可解释**：cross-M8（through-going）；M3=2（PPC 主体）。

**C. normal single 被排斥**：B3（P=0.00000）；B2（4.4%）；same-layer 53%（6.6%）。

**D. electronics-like 支持/不支持**：SD2 minor/major 0.35（topology 层支持；**waveform 闭环未完成 → 未定论**）。

**E. physical-secondary 支持/不支持**：SD3 framework 建立，track2 Edep 仍 incomplete；**未达 forward-model 闭环**。

**F. S2 支持**：same-M8 机制存在，但 **rate overpredict（22% vs 5%，PPC=0.004）→ 当前 S2 模型不足**。

**G. panel common-mode 限制**：data cross-M8 有 T02→Ch11/T13→Ch10 位置依赖，pure common-mode 难产生；上限待真实 light-sharing 量化。

**H. 当前模型无法解释**：same-M8 率（PPC 失败）；same-layer dark 主导机制；SD2/SD3/B2/B3 的真实 Q/timing（data 缺失）。

**I. 下一轮硬件实验判别**：(1) 提供 Ch0–Ch3 真实 Q 谱（区分 thr/gain，§48）；(2) same-layer minor/major Q + waveform（SD2 vs SD3，§22）；(3) 7 个 same-M8 waveform（S2-E vs S2-P）；(4) panel Ch4–11 baseline/threshold（panel threshold 映射，§13–16）。

---

## 8. 28 问回答（可达部分）
1. FIT A 真 p=0.065（2-comp）。2. 退化 component dof。3. M3 P(N=2)=0.27 兼容。4. same-M8 P(N≤7)=0.004 失败。
5. NB 不完全复现 joint（过估零尾）。6. 升级=event-level resampling。7. P(dark|single)≈0–0.002（NB 保守上界）。
8. panel threshold 范围待真实数据（BLOCKED）。9. B2 single 兼容 4.4%。10. B3 single 兼容 ~0%。11–19. SD2/SD3/B2/B3/S2 forward-model 建立（v6）但**真实 Q/timing 闭环 BLOCKED**。
20. PC 上限待真实 light-sharing。21. 纯几何不给 1.61（噪声）。22. mirror 恢复 ~1。23. thr/gain 在 topology 简并（待 Q 谱）。
24. FIT C/D 未达（data BLOCKED + same-M8 PPC 失败）。25. 失败 observable：same-M8（PPC=0.004）；FIT C/D 待 data。
26. f_single working range 0.21–0.42。27. stat ±0.03；detector/model 待 data。28. v6 0.42 working estimate：**修正为 range 0.21–0.42，不作测量**。

## 9. 严格停止条件（§65）
same-M8 PPC = 0.004 < 0.01 ⇒ **MODEL INADEQUATE**。
**不输出 "事件组成 = xx%±yy%"。** 只给 working range（f_single 0.21–0.42）+ 未解释 population（same-M8 rate）+ 下一步实验判别方案（§I）。

## 10. 总表
| 观测 | 候选机制 | data 特征 | MC 预测 | PPC/likelihood | 可信度 | 最有判别力的实验 |
|---|---|---|---|---|---|---|
| cross-M8 42% | single through | score 40-60 | P(M8\|cross)=0.42 | FIT B p=0.04 | 高 | panel PE 定量 |
| T02/T13=2.1 | electronics asym | topology | geometry=1.01✓ | — | 高(electronic) | Ch0-3 Q 谱 |
| M3=2 | multi-particle | 2 event | P(N=2)=0.27 | 在 95% 内 | 高 | M3 light-share |
| same-M8=7 | S2 | panel↔dominant | 预测~17 | **P≤7=0.004 失败** | 低(overpredict) | same-M8 waveform |
| B3 strong+dark | 非 single | score~0 | P=0.00000 | — | 高(排斥) | B3 timing+Q |
| same-layer 53% | SD2/SD3 | 53% | 6.6% single | — | 中低 | minor/major Q |
