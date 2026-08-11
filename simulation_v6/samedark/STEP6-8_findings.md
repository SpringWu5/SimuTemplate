# simulation_v6 — STEP 6–8 机制分解

## SD 分解（samedark）
| 机制 | minor/major Q | panel-dark | 说明 |
|---|---|---|---|
| SD1 正常 same-layer 单缪子 | (单 track, ~对称) | 1.000 | 仅 6.6%，不穿 slab，纯 dark |
| **SD2 电子学串扰复制** | **0.35±0.17（宽）** | 0.81 | broad r 分布，与物理机制可区分 |
| SD3 物理次级/多粒子 | ~0.73（独立） | — | 需 track2 Edep（本轮 incomplete） |

**SD2 vs SD3 判别量**：minor/major Q ratio。SD2≈0.35（copy），SD3≈0.73（独立）。**可由真实 same-layer minor/major Q 分布区分**（图 03）。

## B2/B3（crossdark）条件概率（回答 Q5,Q6,Q7）
- **P(B2-like 弱 Q_min | single cross) = 0.044** → B2 仅 4.4% 可由单缪子 Landau 尾解释（data B2≈43% of cross → 远不足）。
- **P(strong small & truly-dark panel | single cross) = 0.00000** → **B3 完全排斥 normal single-through**（§22 最强矛盾）。
- 注意：single cross 的 not-M8 尾是 M4-7 partial-light（tot PE ~10-25），不是 data 的 score~0 dark。

## S2 same-M8 rate（回答 Q14，§28）
S2-E（穿板 primary + 串扰 copy）直接计数：
- single-block + slab-crossing primary 占 38%；copy 后成 same-layer M2，其中 M8 ~23%。
- **predicted P(same-M8 | same-layer) ≈ 0.22（p_copy 0.1-0.5 几乎不变）**。
- **data = 0.052**。
- ⇒ **S2 机制预测 ~22%，不是 5%。** 要匹配 5%，dark-same-layer（SD1+SD2-dark）必须 ~4× 大于 S2。
- 即 same-M8 rate **不是**事后自由设置的 5%，而是被机制约束到 ~22%——除非 dark-same-layer 主导（需自身解释）。**这是真实张力**。

## 结论
- B3 = 0.00000（single 排斥）✓ 强化 v5 结论。
- B2 仅 4.4% single-兼容。
- SD2/SD3 可由 minor/major Q 区分（待 data 验证）。
- S2 overpredicts same-M8（22% vs 5%）→ same-layer 主体必须是 dark 机制。
