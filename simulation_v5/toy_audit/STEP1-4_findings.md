# simulation_v5 — STEP 1–4 审计结论（toy/mixture）

## 问题 1：v4 correlated 图13为何与文字不一致？
**确认是 bug。** v4 `correlated_two_track` 把第二条径迹**独立**从单径迹模式分布中抽取，
完全忽略 `s_cm`（横向位移）和 `sigma_deg`（角度展宽）参数 —— 它只是独立多径迹模型
的伪装，所以 same-layer 对所有 p_corr 都≈0。文字"随 p_corr 上升"是错误的。

**修复**：v5 `toys.correlated_two_track` 完全几何化：track2 = track1 原点 + 横向位移，
方向 = track1 方向 + 角度扰动，两条都是真实射线，OR 后的 hit。新增 `offset_mode`
（transverse / det_x / mixed）。9 个 unit test 全部通过。

## 问题 2：旧 mixture chi2=0.2 为何视觉不吻合？
**确认是 bug（定义错误）。** v4 用 `sum((mix-data)^2 / data_fraction)` 作 chi2，分母是
**分数**（~0.1）而非多项分布方差，所以 chi2 人为地小（~0.2）但柱状图明显不符。

**修复**：v5 `likelihood.py` 用正确**多项分布对数似然** `logL = Σ N_i log p_i`，
目标函数 `-2logL`，并输出 Pearson χ²、G-test（deviance）、逐项 pull。

## 问题 3：修复后 0/25/75 是否仍成立？
**不成立，应撤回。** 用修正的几何 correlated + 正确多项似然：
- C1+C2(transverse)+F1 → 最佳 f=[0,0,1]（纯 fake），Pearson=65, G=65（dof=3，极差）。
- C1+C2(det_x)+F1 → 最佳 f=[0,1,0]（纯 correlated），Pearson=12.5, G=13.5（仍差）。
- profile 似然：f_fake=1.0[0.92,1.0] 或 f_corr=1.0，**两者都贴边界** → 3 分量对称模型不足。

## 问题 4：正确似然下 single fraction 是否真的可以为 0？
**f_single=0 是模型缺陷的伪迹，不是"实验无单缪子"的证据。** 所有对称分量都无法
同时解释：(a) data 的极端 same-layer=53%，(b) T02/T13≈2.1 左右不对称。拟合只能用
same-layer 作主杠杆，把 f 推到纯 correlated(det_x) 或纯 fake 边界。**T02/T13 pull
持续显示 T02 低估、T13 高估** → 必须先建模通道不对称（STEP 6）才能信任 mixture。

## 组件拓扑向量（resample 后无偏）
| 组件 | 01 | 23 | 02 | 13 | 03 | 12 | same-layer | M3 |
|---|---|---|---|---|---|---|---|---|
| C1 single | .03 | .03 | .28 | .35 | .18 | .13 | **.059** | 0 |
| C2 corr transverse | | | | | | | .193 | .005 |
| C2 corr det_x | | | | | | | **.511** | .026 |
| F1 fake uniform | 1/6 each | | | | | | .333 | — |
| **data** | .31 | .22 | .20 | .10 | .10 | .07 | **.53** | 2/257 |

**关键**：det_x correlated 能达到 same-layer≈0.51（接近 data 0.53），但 M3 预测≈2.6%
（data M3=2/257≈0.8%），且无法解释 T02/T13 不对称。
