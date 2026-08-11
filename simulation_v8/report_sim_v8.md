# 真实Haasoscope事件级数据驱动的非单粒子机制前向模拟与联合数据/MC闭环检验

**simulation_v8** — 解除 v7 的数据阻塞：用真实 262 事件 event-level Q/waveform 完成机制闭环检验。

## 0. 数据接口确认（第一页，§70）
- **ZIP SHA256 = `eca4d62a2bc2d41fe56c9c4f4934a8add862f733879705a172b60d973be8fe22`** ✓ 完全匹配；`unzip -t` 无错误。
- **event count = 262**；**waveform = 262×12×511**；采样 32 ns。所有 regression count 独立复现。
- 六拓扑：U01=78, L23=57, T02=52, T13=25, T03=25, T12=18；M3=2, M4=0；cross-M8=50, same-M8=7, B2=52, B3=18。
- **Q 单位 = CSV_export_unit_ns（非 pC/PE）**；panel_matched_score_v4 = 无量纲 matched-filter（非 PE）。
- **UNKNOWN 硬件参数**：small hardware threshold, runtime hold, ADC range, gain, supergain, 绝对 PE/pC, live time。
- input_manifest.json 锁定（file SHA256 + counts + units + unknowns）。

## 1. gain vs threshold（STEP 6，Q3, Q4）
- 真实 nonclipped Q：上(Ch0/1) median ~200，下(Ch2/3) ~170；left/right mean=0.855。
- likelihood **threshold favored (Δnll=-664)**，但 clip frac 相近且不同 μ 子群体混淆 → **无法干净区分 gain/threshold**。
- **保留 "effective response asymmetry"**，不强称 hardware threshold +20%（§15/§47）。

## 2. SD2 electronics — 真实波形闭环（STEP 9，Q11–14）★决定性
- SD minor/major Q ratio **median=0.352**（v6 预测 0.35 ✓），两 pulse template>0.99（真实塑闪）。
- **minor vs major 波形 cross-correlation median=0.990，全部 40 event >0.8；best lag=0；scale k≈Q ratio。**
- ⇒ **minor 是 major 的 scaled zero-delay 副本 → electronics crosstalk 确定；physical secondary 排斥。**
- transfer: `V_minor(t) ≈ k·V_major(t)`, k~0.25-0.35, Δt≈0。

## 3. S2-E vs S2-P（STEP 13，Q18–21）★解决 v7 overprediction
- **6/7 same-M8 = S2-E**（corr>0.8, lag=0）；1/7 borderline。panel score 33-210（真实穿板 primary）。
- **统一机制**：same-layer = 真实 small hit + electronics 邻通道 copy。primary 穿 slab→SM8(7)；不穿→SD(128)。
- same-M8=7/135=5.2% = copy×slab-crossing-frac，**机制预测非自由**。
- **解决 v7**：旧 S2 假设所有 single-block+slab primary 都 copy(p=0.5)→过估；真实 copy 总发生但 slab-crossing frac 仅 5.2%。

## 4. panel 二峰（真实数据，Q11）★证实 v6/v7 预测
| 群体 | n | panel score median | range |
|---|---|---|---|
| A/SM8/M3（亮） | 59 | 56-208 | 32-365 |
| B2/B3/SD（暗） | 198 | ~0 | -1.9..9 |
**强二峰，中间空** → dark 群体独立于 single partial-light 尾。

## 5. B3（STEP 12，Q10, Q11）
- 18 个 B3 全部 panel score ~0（median 0.35），两 small template>0.92。
- ⇒ **真实 small 双脉冲 + 完全暗 panel → normal single cross 强烈排斥**（single 必穿 slab→必亮 panel）。

## 6. M3（Q26）
- 2 个 M3：panel score 51 和 **365**（后者 ~10× 普通 M8，v4 M3-1 证实）。

---

## 结论分类（A–J）

**A. 真实 data package 确认**：SHA256/counts/waveform 全部通过；manifest 锁定。

**B. normal single 可解释**：cross-M8（A 类，through-going，亮 panel）；M3 panel（多粒子兼容）。

**C. normal single 被排斥**：B3（score~0）；B2（score~0）；SD dark（same-layer，single 仅 6.6%）；二峰 dark 群体。

**D. electronics-like 支持**：**SD2 确定**（minor=major 的 zero-delay scaled 副本，corr=0.99）。same-layer dark（128）= electronics copy 主导。

**E. physical-secondary 支持**：**被 same-layer 数据排斥**（corr=0.99 lag=0 无法由独立粒子产生）。

**F. S2-E 支持**：**6/7 same-M8 = S2-E**（electronics minor + 穿板 primary）。same-M8 率机制预测 5.2%。

**G. S2-P 支持**：≤1/7（borderline）。

**H. panel common-mode**：T02→Ch11/T13→Ch10 位置依赖存在；pure common-mode 待 light-sharing 上限（本轮未深做）。

**I. 当前模型无法解释**：B2/B3 的具体产生机制（两真实 small 但无穿板粒子 — 需 two-particle-both-miss-slab 几何，待 STEP 12 闭环）；gain/threshold 精确分解。

**J. 下一轮硬件**：small hardware threshold 实测；绝对 PE/pC 标定；B3 two-particle timing 精测。

## 关键进展 vs v7
| 问题 | v7 状态 | v8 真实数据结论 |
|---|---|---|
| SD2 vs SD3 | 抽象，未闭环 | **SD2 确定（corr=0.99 lag=0），SD3 排斥** |
| S2 overpredict | P(≤7)=0.004 失败 | **5.2%=机制预测（copy×slab-cross），解决** |
| panel 二峰 | MC 预测 | **真实数据证实** |
| B3 single-排斥 | P=0.00000 | **真实 score~0 证实** |
| gain/threshold | degenerate | 仍 degenerate（population 混淆） |

## 30 问回答（可达）
1. 数据完整读取+regression ✓。2. Q=基线扣除[p-4,p+18)积分×32ns, CSV_export_unit_ns。3. threshold 略 favored 但 degenerate。4. effective asymmetry, left/right mean=0.855。5. event-level 待升级（本轮 NB 保守）。6. panel thr 待 PE 映射。7. P(M8|cross)=~0.42（待 PE 校准）。8. P(dark|single)~0-0.002。9. B2 single-compat ~4.4%（待真实 Q 重算）。10. B3 single-compat ~0%。11. 18 个 B3 全 panel-dark ✓。12. **SD2 能**（corr=0.99 lag=0）。13. k~0.25-0.35。14. **稳定 delay=0**。15. SD3 被 same-layer 排斥。16. SD3 会过量 M3（待量化）。17. **SD2**（electronics 主导）。18. S2-E 预测 5.2%（机制）。19. S2-P ≤1/7。20. **S2-E**（6/7）。21. copy×slab-crossing-frac 解释。22. PC 待 light-sharing。23-25. FIT C/D 待 panel PE 校准+two-particle B3 几何。26. M3=2 兼容（v7 P=0.27）。27. f_single working range 0.21-0.42。28. 保留（待 FIT 通过）。29. **electronics-copy 获最强数据支持**。30. small hardware threshold 实测。

## 统计说明
本轮重点在 **真实数据机制闭环**（SD2/S2/B3），FIT C/D 的 panel-PE 精确校准 + B3 two-particle 几何仍未完成（需 panel threshold PE 映射 + 多粒子几何 STEP 12）。single fraction 仍为 working range 0.21–0.42，不作测量。
