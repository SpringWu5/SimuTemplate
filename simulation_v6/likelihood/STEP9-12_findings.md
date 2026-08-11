# simulation_v6 — STEP 9–12 三级 fit + 绝对 GOF + 判定

## 三级 fit 结果
| Fit | bins | best frac (through/sld/xd/S2) | Pearson | dof | p-value | 判定 |
|---|---|---|---|---|---|---|
| A (topology+M3/M4) | 8 | (.5/.5/-/-) | 8.9 | 5 | 0.114 | **ADEQUATE** |
| B (+panel M8/nonM8) | 14 | (.42/.50/0/.083) | 19.7 | 9 | 0.020 | 边缘 (p>0.01) |
| **C (+cross Q_min)** | 17 | (.5/.4/0/.1) | **94.5** | 12 | **7e-15** | **INADEQUATE** |

- single-only: Pearson=77/6 p=1.5e-14 → **强烈拒绝**。
- FIT B max|pull|=2.28（无 >3σ），但 FIT C 因 B2/B3 的 Q_min 结构系统性失败。

## 为何 FIT C 失败（§35, §52）
- B3（强 small + truly-dark panel）：P(single cross) = **0.00000**（STEP 7）。
- B2（弱 small）：P(single cross) = 0.044，但 data B2≈43% of cross。
- 单缪子 cross 的 Q_min 分布（Landau）无法产生 data 的 B2/B3 二分。
- panel non-M8 尾：single 是 M4-7 partial-light（score~10-25），data nonM8 是 score~0 → 二峰不兼容。

## 判定（§34, §35, §52 停止条件）
**当前模型族 INADEQUATE。**
- FIT C p<<0.01，B2/B3 Q 残差系统性。
- ⇒ **不报告"事件组成 = xx% ± yy%"作为可靠测量。**
- FIT A/B 的 through≈0.42 / sld≈0.50 / S2≈0.08 仅是 **working estimates**。

## single fraction 的统计/模型不确定度（§36, Q19, Q20, Q21）
- v5: f_single≈0.21（错误 panel 模型下）。
- v6 FIT B: f_single(through)≈**0.42**（统一 panel 模型，P(M8|cross)=0.42 内建）。
- **模型不确定度：0.21–0.42**（panel 阈值/threshold 定义/是否含纯 same-layer 单缪子）。
- 统计不确定度（profile/bootstrap）：±0.03。
- ⇒ **f_single = 0.42 ± 0.03(stat) ± 0.21(model)**。
- **v5 的 0.21/0.50/0.21/0.07：修正为 0.42/0.50/0/0.08（FIT B），但因 FIT C 失败，仅作 working estimate，撤回作为"测量"。**

## M3 PPC（§38, Q16）
- M3=2 位于 PPC 主体内（多粒子分量 SD3/correlated 自然产生 M3）。
- 不需专门调参即兼容（FIT A p=0.11 含 M3 bin）。
