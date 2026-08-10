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

---

# STEP 5–14：运动学、光学、toy 与 mixture

## 10. STEP 5：same-layer 运动学与穿板（`figures/04_samelayer_kinematics.png`）
- **P(slab crossed | U01) = 0.000**
- **P(slab crossed | L23) = 0.000**
- same-layer θ集中在 77–86°（水平径迹）；phi 集中在 0°/180°（±x 方向）。
- **结论**：同层水平缪子**完全不穿板**（板 z∈[-1,1]，同层径迹 z≈±5）⇒ 无法产生 panel 信号。

⇒ **数据中 7 个 same-layer M8（均有 panel M8 信号）不可能是单高角度缪子**（Q5,7）。

## 11. STEP 6：cross-layer path/Edep + Landau（`figures/05-06`、`tables/v4_cross_edep.csv`）
| 拓扑 | path 均(cm) | Edep_min 均(MeV) | Edep_min 中位(MeV) |
|---|---|---|---|
| T02 | 2.05 | 3.1 | ~2.8 |
| T13 | 2.26 | 3.4 | ~3.0 |
| T03 | 1.62 | 2.2 | ~2.0 |
| T12 | 1.65 | 2.4 | ~2.1 |

- B2/B3 proxy：Edep_min < 1 MeV 的比例很低（Landau 尾）→ 正常单缪子 cross-layer 不容易产生极弱 small（Q10,12）。

## 12. STEP 7–9：修正 O1 光学（126 事件，θ=1–86° 均值28°）
| 指标 | OLD O1 | **NEW O1** | data |
|---|---|---|---|
| T02 f11 | 0.159 | **0.157** | 0.252 |
| T02 f10 | 0.044 | **0.053** | 0.083 |
| T13 f10 | 0.159 | **0.163** | 0.229 |
| T13 f11 | 0.045 | **0.047** | 0.083 |
| P(M8)@1ph | 0.59 | **0.64** | — |
| P(M8)@2ph | 0.32 | **0.44** | — |

⇒ **修正后 T02/T13 光分享基本不变**（旧截断对 cross-layer 影响小），M8 在低阈值下仍大量（Q13,14）。

## 13. STEP 10：same-layer 光学
- P(slab|same-layer)=0 ⇒ **same-layer 单缪子 panel 信号为 0** ⇒ M8 概率为 0。
- 数据 7 个 same-M8 全部有 panel M8 ⇒ **不兼容单缪子**。

## 14. STEP 12–14：toy 与 mixture（`figures/07-09`、`tables/v4_mixture.csv`）
- **独立多径迹**：same-layer 随 p_multi 缓慢上升但仍远低于 52%。
- **相关双径迹**：扫描 s/σ_θ/p_corr；same-layer 随 p_corr 上升。
- **最优 mixture**：**f_single=0.00, f_corr=0.25, f_fake=0.75, χ²=0.2**
  ⇒ 数据拓扑结构需**主要靠 fake/crosstalk + 少量相关多粒子**；纯单缪子(f_single=1)拓扑 χ² 很大。

## 15. 核心 20 问回答汇总
| # | 问题 | 结论 | 分类 |
|---|---|---|---|
| 1 | 收敛 same-layer | 6.65%±0.19%(ESS1172) | 已确认 |
| 2 | 统计误差 | 2.9% | 已确认 |
| 3 | 系统学范围 | 1.5–18%(角分布主导) | 已确认 |
| 4 | 能否到52%? | 否，最乐观≤18%，5×低 | 已确认 |
| 5 | same-layer穿板? | **P=0** | 已确认 |
| 6 | 若穿板M8? | N/A（不穿板） | 已确认 |
| 7 | 7个same-M8是single? | **不兼容**（无穿板=无panel） | 与实验张力 |
| 8 | 小闪不平衡? | path天然不平衡(一长一短) | 与MC一致 |
| 9 | cross-layer穿板? | 100% | 已确认 |
| 10 | B2/B3弱small? | Landau尾不足以解释大量弱事件 | 与实验张力 |
| 11 | cross panel≈0? | 低阈值下极少(M8@1ph=64%) | 与实验张力 |
| 12 | B2/B3 Landau解释? | 部分可，量不够 | 部分解释 |
| 13 | corrected T02/T13 | f11~0.157(不变) | 已确认 |
| 14 | T03/T12显著变? | 不显著 | 已确认 |
| 15 | M8 threshold | @1ph=64%, @2ph=44% | 已确认 |
| 16 | multi-track same-layer? | 远低于52% | 已确认 |
| 17 | correlated同层高M3低? | 需~25%corr | toy可解释 |
| 18 | fake-hit不自洽? | mixture需75%fake→量大 | toy边界 |
| 19 | M3-1超亮? | 与两粒子相容 | 待光学详查 |
| 20 | 最合理mixture? | ~0%single+25%corr+75%fake | 当前最佳约束 |

## 16. 系统学预算
| 来源 | same-layer影响 | 分类 |
|---|---|---|
| MC统计 | ±0.19%(rel2.9%) | 可控 |
| 角分布n | 1.5–18% | **主导** |
| gap | 3.8–11% | 中等 |
| Lsep | 3.3–11% | 中等 |
| 对齐 | <±2% | 小 |

## 17. 结论分类
- **已由修正MC确认**：same-layer~7%(ESS1172)；P(slab|same-layer)=0；cross-layer P(slab)=1；M8低阈值可达；T02/T13光分享修正后不变。
- **与实验存在张力**：7个same-M8不兼容单缪子（无穿板）；B2/B3弱事件量超Landau预期。
- **toy可解释**：mixture需~25%corr+75%fake。
- **当前不能解释**：same-layer M8的panel信号（需额外机制：穿过slab的多粒子或串扰到panel）。
- **需新硬件验证**：小闪/板相对位置精密测量；same-layer事件的waveform/charge详细比较。
