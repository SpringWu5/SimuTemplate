# simulation_v8 — real-data mechanism findings (STEP 6, 9, 13)

## 数据接口确认（STEP 0-3）
- ZIP SHA256 = eca4d62a... ✓ 完全匹配；unzip -t 无错误。
- 262 events, 262×12×511 waveforms, 32 ns sampling。所有 regression count 独立复现。
- input_manifest.json 锁定（SHA256/counts/units/unknowns）。
- Q 单位 = CSV_export_unit_ns（非 pC/PE）；panel_matched_score_v4 = 无量纲 matched-filter（非 PE）。

## STEP 6: gain vs threshold（真实 Q，Q3）
- nonclipped Q median: Ch0=199,Ch1=201(上), Ch2=174,Ch3=167(下)。left/right mean=0.855。
- likelihood: **threshold favored over gain (Δnll=-664)**, 但 clip frac 相近(0.23/0.20)且 population 混淆。
- **结论：真实左右 response asymmetry 存在，但 gain/threshold 无法从 Q 形状干净区分**（不同 μ 子群体击中不同通道）。保留 "effective response asymmetry"，不强称 threshold +20%（§15/§47）。

## STEP 9: SD2 electronics — 真实波形闭环（Q11,Q12,Q13,Q14）
**决定性证据：electronics copy 成立，physical secondary 被排斥。**
- SD minor/major Q ratio **median=0.352**（v6 预测 0.35 ✓）；两 pulse template>0.99（真实塑闪脉冲）。
- **minor vs major 波形 cross-correlation median=0.990，全部 40 event >0.8**。
- **best lag=0 samples (std=0)**（零延迟）；best scale k≈Q ratio。
- ⇒ minor 是 major 的 **scaled, zero-delay 副本** → electronics crosstalk **确定**；physical secondary（独立 timing/shape）**被排斥**。
- transfer: V_minor(t) ≈ k·V_major(t), k~0.25-0.35, Δt≈0。

## STEP 13: S2-E vs S2-P（7 same-M8，Q18,Q19,Q20,Q21）
- **6/7 same-M8 = S2-E**（corr>0.8, lag=0, scale≈Qratio）；1/7 borderline (F041, corr=0.774)。
- panel score 33-210（亮）= 真实穿板 primary。
- **统一机制**：same-layer 事件 = 真实 small hit + electronics 邻通道 copy。
  - primary 穿 slab → SM8（7）；不穿 → SD dark（128）。
  - same-M8 率 7/135=5.2% = copy(prob)×slab-crossing-frac，**非自由设置**。
- **解决 v7 overprediction**：旧 S2 假设所有 single-block+slab primary 都 copy(p=0.5)→过估；真实是 copy 总发生但 slab-crossing frac 仅 5.2%。

## panel 二峰确认（真实数据，Q11）
| category | n | panel_score median | range |
|---|---|---|---|
| A (cross-M8) | 50 | 56 | 32-171 |
| SM8 | 7 | 57 | 33-210 |
| M3 | 2 | 208 | 51-365 |
| B2 | 52 | -0.02 | -1.9..4 |
| B3 | 18 | 0.35 | -1.7..1.5 |
| SD | 128 | -0.15 | -1.9..9 |
⇒ **亮(A/SM8/M3, 30-365) vs 暗(B2/B3/SD, ~0) 强二峰，中间空** → dark 群体独立（v6/v7 预测被真实数据证实）。

## B3（Q10,Q11）
- 18 个 B3 全部 panel score ~0（median 0.35），两 small template>0.92（真实塑闪）。
- ⇒ B3 = 真实 small 双脉冲 + 完全暗 panel → **normal single cross 强烈排斥**（single 一定穿 slab → 一定亮 panel）。

## M3（Q26）
- 2 个 M3：panel score 51 和 365。后者 ~10× 普通 M8（v4 M3-1 观测证实）。
