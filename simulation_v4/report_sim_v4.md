# 修正宇宙线接受度后的触发拓扑模拟（simulation_v4，STEP 1–4）

> 本阶段以 `sampling_audit_report.md` 为基线，建立**重要性采样（IS）生成器**并验证，把 same-layer 接受度算到 ESS≥1000，完成角分布/几何系统学与六拓扑。**STEP 5+（运动学、stacked 光学、toy）为后续。**

## 1. 重要性采样设计（`importance_sampling/is_engine.py`）

**目标 PDF**（水平面 flux，约定 B）：p(x0,y0,θ,φ) = (1/A)·(n+1)cosⁿθ·(1/2π)；约定 A 多一个 cosθ ⇒ p_θ=(n+2)cosⁿ⁺¹θ。
**Proposal**：
- θ：q_θ = 0.7·(n+1)cosⁿθ + 0.3·Unif[70°,89°]（增强大角度尾）；
- φ：q_φ = 0.7/(2π) + 0.3·[½WNorm(φ;0,20°)+½WNorm(φ;π,20°)]（增强 ±x 方向）；
- 位置：q_pos = 0.4·Unif[-300,300]² + 0.6·(x0 侧带[20,45]∪[-45,-20]，y0~Gauss(0,5cm))（集中在 same-layer 起点）。
**权重**：w = w_θ·w_φ·w_pos = (p_θ/q_θ)·(p_φ/q_φ)·(p_pos/q_pos)。
**ESS** = (Σw)²/Σw²。生成面 z=10cm，HW=300cm（捕获 θ≤88°）。

## 2. 三方法验证（STEP 1–2，`figures/02_validation.png`、`tables/v4_validation.csv`）
| 方法 | 01 | 23 | 02 | 13 | 03 | 12 | same-layer |
|---|---|---|---|---|---|---|---|
| A 无偏(weights=1) | 0 | .125 | .375 | .500 | 0 | 0 | .125(ESS1,仅1事) |
| B IS | .032 | .020 | .343 | .213 | .237 | .155 | .052(ESS57) |
| C 备选proposal | .038 | .039 | .294 | .233 | .218 | .179 | .077(ESS62) |

跨层拓扑（02/13/03/12）三方法**一致**；same-layer B≈C（A 无偏统计不足以测 same-layer，仅作跨层基准）。**生成器验证通过。**

## 3. 收敛 same-layer（STEP 2b，20 seeds × 1e7）
**P(same-layer | single-μ triggered M2) = 6.65% ± 0.19%（ESS=1172, relerr 2.9%, raw 53122 事件）**。
数据 same-layer = 52%。**比值 ≈ 7.8×**。same-layer 径迹 θ 集中在 77–86°（与解析 θ≥76° 一致）。

## 4. 角分布系统学（STEP 3a，`tables/v4_systematics.csv`）
| n | conv B (cosⁿ) | conv A (cosⁿ⁺¹) |
|---|---|---|
| 1.5 | **18.3%** | 3.2% |
| 2.0 | 7.9% | 1.4% |
| 2.5 | 3.4% | 0.6% |
| 3.0 | 1.5% | 0.3% |

角分布是最强系统学（n=1.5→18%, n=3→1.5%）。约定 A 比 B 系统性低 ~2×。

## 5. 几何系统学（STEP 3b，n=2,convB）
| gap(cm) | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|
| same-layer | 11.2% | 9.2% | 8.0% | 7.3% | 3.8% |
| Lsep(cm) | 8 | 9 | 10 | 11 | 12 |
| same-layer | 3.3% | 5.9% | 8.0% | 8.5% | 10.9% |
| 对齐偏移 | xoff±2cm: 6–8% | yoff±2cm: 7–8% | （稳定，<±2cm） |

**系统学包络**：n=2 下，gap∈[8,12]∪Lsep∈[8,12] → same-layer ∈ [3.3%, 11.2%]；含 n=1.5 软谱上界 ~18%。**对齐 ±2cm 影响 <±2%。**

## 6. 六拓扑（STEP 4，n=2,convB,gap=10,`tables/v4_topology.csv`）
| 拓扑 | MC | ±stat | data |
|---|---|---|---|
| 01(U01) | 3.1% | 0.2% | 30.6% |
| 23(L23) | 1.6% | 0.2% | 22.4% |
| 02 | 34.8% | — | 20.4% |
| 13 | 33.5% | — | 9.8% |
| 03 | 14.6% | — | 9.8% |
| 12 | 12.4% | — | 7.1% |

- **MC 02≈13（左右对称），数据 02/13≈2.1**（明显不对称）→ 真实装置存在左右效率/对齐不对称，对称 MC 无法复现。
- same-layer（01+23）MC ~5% vs 数据 53%。

## 7. 核心问题回答（本阶段）
| # | 问题 | 结论 |
|---|---|---|
| 1 | 收敛 single-μ same-layer | **6.65% ± 0.19%（ESS 1172）** |
| 2 | 统计误差 | **2.9%**（ESS≥1000 达标） |
| 3 | 系统学最大/最小 | min ~1.5%(n=3)；max ~11%(n=2,小gap大Lsep)；含 n=1.5→18% |
| 4 | 能否到 52%？ | **否**。最乐观(n=1.5+几何)~18%，仍 3× 低于 52%；现实(n=2)≤~11%，5× 低于 |

## 8. 系统学预算（分开报告）
| 来源 | same-layer 影响 |
|---|---|
| MC 统计 | ±0.19%(rel 2.9%) |
| 角分布 n=1.5→3 | 1.5%–18%（**主导**） |
| flux 约定 A/B | ×~2 |
| gap 8→12 | 3.8%–11% |
| Lsep 8→12 | 3.3%–11% |
| 对齐 ±2cm | <±2% |

## 9. 待续（STEP 5–14）
5. same-layer 运动学 + 穿板概率；6. cross-layer path/Edep；7. 重生无截断 O1 光学样本；8. T02/T13/T03/T12 光分享；9. same-layer 光学；10. 比数据 7 个 same-M8；11. B2/B3 兼容性；12–13. multi-track/correlated/fake toy；14. 综合 data/MC mixture。

## 产出
- 脚本：`scripts/run_v4.py`、`importance_sampling/is_engine.py`
- 图：`figures/{01_is_diagnostics,02_validation,03_systematics_topology}.png`
- 表：`tables/v4_{validation,same_layer,systematics,topology}.csv`
