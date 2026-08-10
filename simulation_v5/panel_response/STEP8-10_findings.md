# simulation_v5 — STEP 8–10 panel / B2-B3 / same-M8 结论

## STEP 9 (Q10): P(panel dark | true single cross-muon)
panel 非常亮：slab Edep mean=4.83 MeV，total PE mean=**772**（8 SiPM 和）。
在使 P(M8)=0.42（匹配 data cross-M8=42%）的阈值 thr=30 PE 下：
**P(panel all-dark | single cross-muon) = 0.000**。
即使最低 Edep 的 slab 穿越也产生数百 PE → **panel 永不暗**。

## STEP 10 (Q11,Q12,Q13): B2/B3 是否可由 single muon 解释？
- **P(panel dark | single cross-muon) = 0.000**，但 data cross-nonM8 = 70/120 = **58%**。
- B3（强 small 但无 panel）：P(strong small & panel dark | single cross) = **0.000**，data = 18/120=15%。
- B2+B3（无 panel）：data = 58%，MC single = **0%**。
- **Q13: Landau/path-length 完全不足** —— 即使最弱 slab 穿越也有数百 PE，Landau 尾永不使 panel 暗。

⇒ **B2 和 B3 都不能用 single cross-muon 解释。** cross-nonM8 的 58% 必须是非穿越事件
（真实 small hit 但无 slab 穿越粒子：多粒子/fake/secondary）。
**data 的 cross-M8=42% 很可能就是真正 single through-going muon 的比例。**

data 的 M8/nonM8 强二峰（score 40-60 vs ~0）也与"single 一直亮 + 非穿越一直暗"的混合一致，
而 single MC 给连续亮分布 → 二峰必须来自混合。

## STEP 8 (Q8,Q9): same-layer M8 机制 S1/S2
- **S2 primary（一个 upper block + 穿 slab，无 lower）：占 M>=1 single muon 的 38%**（几何上很多：
  击中一个上块后斜出，穿过 slab 但错过下块）。
- S2 → U01 + panel M8 概率 = **0.94**（因为 S2 primary 穿越 slab → 亮 panel）。
- S1（两条物理径迹，correlated det_x）：same-layer M2 中 **91% 有 slab 穿越** → panel M8。
- data same-M8 = 7/135 = **5.2%**。

⇒ **S1/S2 都能产生 same-layer M8（panel M8 概率 ~90%）**。要匹配 data 5.2%，只需
~5% 的 same-layer 事件含 slab-穿越粒子（S2 型），其余 95% 是纯 same-layer（无 panel）。
- **Q8: S2（一个真实穿板粒子 + 额外 same-layer hit）最有吸引力** —— panel 来自真实粒子，
  天然解释"panel timing 对应 dominant small"（Q9）。
- S2 primary 占比高（38%）说明该几何模式常见，少量混入 same-layer 即可解释 7 个 same-M8。

## 关键数值
| 量 | MC single | data |
|---|---|---|
| P(panel dark \| cross) | **0.000** | 0.58 |
| P(strong&dark, B3-like) | **0.000** | 0.15 |
| P(M8 \| same-layer, S2) | 0.94 | 0.052 |
| S2 primary frac | 0.38 | — |
