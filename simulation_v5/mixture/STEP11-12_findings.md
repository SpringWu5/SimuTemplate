# simulation_v5 — STEP 11–12 joint mixture + posterior predictive 结论

## 联合似然（12 bin = 6 拓扑 × {M8, nonM8}），4 个有明确物理定义的分量

| 分量 | 物理定义 | 拓扑 | panel | best-fit frac |
|---|---|---|---|---|
| C_through | 单个 through-going μ子（穿 slab） | cross 主 | **bright** | **0.21** |
| C_samedark | same-layer 小 hit，无 slab 穿越（串扰/fake/多粒子） | same 主 | dark | **0.50** |
| C_crossdark | cross-layer 小 hit，无 slab 穿越（B2/B3 型） | cross | dark | **0.21** |
| C_S2 | 一个穿板粒子 + 额外 same-layer hit | same | bright | **0.07** |

## 模型比较（AIC/BIC，lower=better）
| 模型 | -2logL | AIC | 结论 |
|---|---|---|---|
| M1 single only | 11475 | 11475 | **强烈拒绝** |
| M2 +samedark | 1516 | 1518 | same-dark 必需 |
| M3 +crossdark | 1403 | 1407 | cross-dark 必需 |
| **M4 +S2** | **1099** | **1105** | **最佳**，S2 显著（ΔAIC~300） |

best fit Pearson χ²=33.6 (dof=7)，pulls 多数 |<3|（残余张力在 T03/T12 对角 + S2 略过预测 same-M8）。

## 核心结论：数据组成
- **~21% 是干净的 single through-going muon**（cross + panel M8）—— 这是唯一能被纯单缪子模型解释的部分。
- **~78%（samedark 50% + crossdark 21% + S2 7%）是非 through-going 事件**：有真实小塑闪 hit 但无（或部分无）panel 信号。
  - samedark 50% 是最大异常群：same-layer 小 hit 但完全不穿 slab → 需串扰/fake/多粒子机制。
  - crossdark 21% = B2/B3：cross-layer 小 hit 但无 panel → 非单缪子。
- panel M8 是最强判别量：**cross-M8≈42% 几乎就是真正 single through-going 的比例**。

## 对 v4 的 0/25/75 的最终裁定
**撤回。** v4 的 f_single=0/f_corr=0.25/f_fake=0.75 来自 (a) buggy correlated toy（几何参数未用）+
(b) 错误 chi2（分母用分数而非多项方差）。修正后：
- 单缪子（through-going）fraction = **0.21 ± ~0.03**（非 0）。
- "fake/dark" 类合计 ~0.71，但这是**多个不同物理机制**（samedark 串扰 + crossdark 非穿越 + S2）的总和，**不是单一 "fake" 分量**。
- 不能把 toy fraction 直接当真实物理比例，除非各分量已被 forward model + 数据特征验证（samedark/crossdark 仍需硬件控制实验确认机制）。
