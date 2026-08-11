# simulation_v9 — STEP 1–4 copy positive-control + coupling matrix

## STEP 1-2: 正控制（cross-M8）— 修正 v8 ★最重要
v8 称 "electronics crosstalk 确定"（corr=0.99, lag=0）。**正控制测试否定该确定性：**

| group | n | r | lag | k | resid | resid_rise |
|---|---|---|---|---|---|---|
| same-dark (E) | 128 | 0.990 | 0 | 0.352 | **0.016** | 0.224 |
| **cross-M8 (T, 正控制)** | 50 | **0.977** | **0** | 0.783 | **0.024** | 0.265 |
| same-M8 (S) | 7 | 0.928 | 0 | 0.196 | 0.042 | 0.223 |
| B2 | 52 | 0.986 | 0 | 0.423 | 0.019 | 0.228 |
| B3 | 18 | 0.995 | 0 | 0.583 | 0.011 | 0.235 |

**关键（Q1, Q2, Q3, Q4）**：
- cross-M8（确定是两个真实独立塑闪脉冲，非 electronics）也呈现 **r=0.977, lag=0, resid=0.024** —— 与 same-dark（0.016）几乎相同的 copy signature。
- same-dark resid 略低于 cross-M8（Mann-Whitney p=0.0035），但 **Cliff's delta=-0.26（small effect）**，差异小。
- **k 分布宽**（same-dark IQR=[0.20,0.56], std=0.25；cross-M8 std=0.32）—— 非固定耦合常数。
- k 与 Q_major 弱相关（same-dark corr=-0.16, cross-M8=0.25）。

⇒ **"electronics crosstalk 确定" 撤回 → 改为 "electronics-like scaled-copy signature"。**
高 r / 低 resid / lag=0 主要来自 **塑闪脉冲本征模板相似**，正控制（真实双塑闪）也产生近乎相同的 signature。
electronics copy **一致** 但波形形状单独**不足以证明**；physical secondary **未被排斥**（同样产生该 signature）。

## STEP 3: 4×4 coupling matrix（Q6, Q7, Q8, Q9, Q10）★颠覆性
4×4 k_ij = Q_minor/Q_major（一强一弱事件）：

| major\minor | Ch0 | Ch1 | Ch2 | Ch3 |
|---|---|---|---|---|
| Ch0 | - | 0.44 | 0.60 | 0.38 |
| Ch1 | 0.29 | - | 0.56 | 0.82 |
| Ch2 | 0.37 | 0.57 | - | 0.32 |
| Ch3 | 0.48 | 0.48 | 0.37 | - |

- **same-layer neighbour coupling (0↔1,2↔3) median k = 0.346**
- **cross-layer coupling median k = 0.510（更高！）**
- 方向非对称：Ch0→Ch1=0.44 vs Ch1→Ch0=0.29。

**关键结论（Q6, Q7, Q10）**：
- coupling **不**集中在物理邻近同层通道——跨层同样强甚至更强。
- 若是 PCB/邻道 electronics，应 same-layer >> cross-layer；数据相反。
- **"coupling" 只是真实多 hit 事件的自然幅度比**（两粒子独立 Q），非 electronics 耦合常数。

## v6/v7/v8 "electronics crosstalk" 解释 — 撤回
综合 STEP 1-3：
1. 正控制（cross-M8 真实双塑闪）也呈 copy signature（resid 0.024）→ 高 r/低 resid 是塑闪本征。
2. k 分布宽（非固定耦合）。
3. coupling 非局部化（跨层更强）。
⇒ **无 convincing 证据支持 electronics crosstalk。** dark 群体（SD/B2/B3）最一致的解释是 **真实多粒子事件**（粒子击中 small 但不穿 slab）。下一目标：B3 two-particle both-miss-slab 几何（STEP 6-7）。

## 判别 electronics 的真正依据
波形 copy signature 不足以判别（正控制失败）。**真正判据需：**
1. coupling 是否仅限物理邻近通道（同层邻道 0↔1, 2↔3 大，跨层小）→ PCB/邻道 electronics。
2. coupling 方向非对称（0→1 ≠ 1→0）→ routing/impedance。
3. fixed-tight k → 线性 coupling（数据 k 宽 → 不支持简单固定耦合）。
4. baseline 共变 / pre-pulse 相关 → 确定发生在哪一级。
