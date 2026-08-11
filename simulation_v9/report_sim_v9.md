# Haasoscope小闪电子耦合、双粒子暗事件与底层生成式数据/MC闭环模型

**simulation_v9** — 用正控制（positive control）和耦合矩阵检验 v8 的 "electronics crosstalk 确定" 结论，并建立 B3 双粒子 both-miss-slab 几何。

> **核心结论：v8 的 "electronics crosstalk 确定" 撤回。** 正控制（cross-M8 真实双塑闪）也呈相同 copy signature；coupling 非局部化。dark 群体最一致的解释是**真实多粒子事件**，非 electronics。

## 1. 正控制：cross-M8 波形 copy（STEP 1-2，Q1–5）★修正 v8

v8 仅用 same-dark corr=0.99/lag=0 称 electronics 确定。**缺正控制。** v9 测量 cross-M8（确定是两个真实独立塑闪脉冲）：

| 群体 | n | r | lag | k | **scaled resid** |
|---|---|---|---|---|---|
| same-dark (E) | 128 | 0.990 | 0 | 0.352 | **0.016** |
| **cross-M8 (T 正控制)** | 50 | **0.977** | **0** | 0.783 | **0.024** |
| same-M8 (S) | 7 | 0.928 | 0 | 0.196 | 0.042 |
| B2 | 52 | 0.986 | 0 | 0.423 | 0.019 |
| B3 | 18 | 0.995 | 0 | 0.583 | 0.011 |

- **cross-M8（真实双塑闪）也呈 r=0.977, lag=0, resid=0.024** —— 与 same-dark(0.016) 几乎相同。
- same-dark resid 略低（Mann-Whitney p=0.0035），但 **Cliff's delta=-0.26（small effect）**。
- **k 分布宽**（same-dark IQR=[0.20,0.56], std=0.25；cross-M8 std=0.32）—— 非固定耦合常数。
- k 与 Q_major 弱相关（-0.16 / 0.25）。

⇒ **Q1-Q5**：高 r / 低 resid / lag=0 主要来自 **塑闪脉冲本征模板相似**（正控制证实）。electronics copy **一致但不被波形形状证明**；physical secondary **未被排斥**。**"确定" → "electronics-like signature"。**

## 2. 4×4 耦合矩阵（STEP 3，Q6–10）★颠覆性

| major\minor | Ch0 | Ch1 | Ch2 | Ch3 |
|---|---|---|---|---|
| Ch0 | – | 0.44 | 0.60 | 0.38 |
| Ch1 | 0.29 | – | 0.56 | 0.82 |
| Ch2 | 0.37 | 0.57 | – | 0.32 |
| Ch3 | 0.48 | 0.48 | 0.37 | – |

- **same-layer neighbour (0↔1,2↔3) k median = 0.346**
- **cross-layer k median = 0.510（更高）**
- 方向非对称（Ch0→1=0.44 vs Ch1→0=0.29）。

⇒ **coupling 不集中在物理邻近通道**（跨层同样强甚至更强）。若是 PCB/邻道 electronics，应 same-layer >> cross-layer。**"coupling" 只是真实多 hit 事件的自然幅度比**（两粒子独立 Q）。**electronics crosstalk 无 convincing 证据。**

## 3. B3 双粒子 both-miss-slab（STEP 6，Q14, Q15, Q16）

两条独立宇宙线 μ 子：一个击 upper small，一个击 lower small（形成 cross topology），但**都不穿 slab**：
- **P(both-miss-slab | cross two-particle) = 0.348**（几何上 35% 的 cross 双粒子事件两粒子都 miss slab）。
- 这些事件：真实塑闪脉冲（强）+ panel dark = **定性符合 B3**。
- 绝对率 R_acc = 2·R_up·R_lo·Δt（singles rate + live time 未知 → 参数化，§22）。
- B3 波形：k=0.583（接近 cross-M8 0.78，比 same-dark 0.35 强）→ 两粒子幅度可比，**支持 two-particle**。

## 4. 修正后的机制图景

| 群体 | v8 解释 | v9 修正 |
|---|---|---|
| SD (same-dark 128) | electronics copy | **electronics 未证实**；最一致 = 真实多粒子（同层两粒子均 miss slab）或未定 |
| B2 (52) | 待定 | 真实多粒子 / single Landau 尾（待真实 Q 重算） |
| B3 (18) | single 排斥 | single 排斥（保留）；**two-particle both-miss-slab 几何可行(35%)** |
| same-M8 (7) | S2-E electronics | S2-E 未证实；可能是真实穿板 primary + 真实 secondary（S2-P） |
| cross-M8 (50) | single through | **保留**（唯一 robust single 解释） |

**关键转向**：dark 群体（SD/B2/B3 = 198/262 = 76%）最一致的解释从 "electronics" 转为 **真实多粒子事件**（粒子击中 small 但不穿 slab）。但绝对率依赖未知的 singles rate + live time，**本轮无法闭合 FIT C/D**。

## 5. 结论分类（A–J）

**A. 代码/数据确认**：v7 统计审计继承；v8 数据 loader 复用。

**B. normal single 可解释**：cross-M8（through-going，亮 panel）。

**C. normal single 被排斥**：B3（panel-dark + 真实脉冲）；B2；SD（single 6.6%）；二峰 dark 群体。

**D. electronics-like 支持/排斥**：**v8 的 "确定" 撤回**。正控制失败 + coupling 非局部化 → **electronics 未获证据**；保留 "electronics-like signature" 但不排除 physical。

**E. physical-secondary/multiparticle 支持**：**获得支持**。B3 two-particle both-miss-slab 几何可行(35%)；耦合矩阵 k 分布与真实多 hit 一致。绝对率待 singles+livetime。

**F/G. S2-E/S2-P**：v8 的 S2-E "确定" 降级；7 个 same-M8 的 minor 可能是真实 secondary（S2-P）或 electronics——本轮无法区分（copy metric 不判别）。

**H. panel common-mode**：耦合矩阵跨层均匀 → 不能排除 common-mode；待 light-sharing 上限。

**I. 当前模型无法解释**：SD/B2/B3 的**绝对率**（singles rate + live time 未知）；electronics vs physical 的**决定性区分**（copy metric 不足以判别）；FIT C/D（待 generative model + 绝对率）。

**J. 下一轮硬件**：(1) 测量 small singles rate + live time → 算 accidental 率；(2) 注入已知 calibration pulse 到 single channel → 测真实 electronics coupling（唯一决定性 electronics test）；(3) 屏蔽实验（盖住一块 small）→ 区分 single vs multi-particle。

## 6. 30 问回答（关键）
1. cross-M8 corr=0.977 resid=0.024。2. same-layer 0.99 **不**显著高于 cross-M8 0.977。3. scaled resid 差异 small（Cliff -0.26），**不**真正区分。4. **electronics 不可称"确定"。** 5. physical secondary **未被排斥。** 6. 耦合矩阵见上（0.3-0.8 均匀）。7. **否**（跨层更强）。8. 方向非对称（0→1=0.44 vs 1→0=0.29）。9. k 宽分布，弱 Q 依赖。10. electronics 级别未定（coupling 非局部 → 不像邻道 PCB）。14. B3 two-particle P(both-miss)=0.348。15. +24ns 需 singles rate。16. correlated 待建。17. B3 也呈 copy signature（正控制故不判别）。25-29. generative model + FIT C/D 待绝对率（singles+livetime 未知）。30. **最有判别力实验：注入 calibration pulse 测真实 electronics coupling + 屏蔽实验区分 single/multi-particle。**

## 7. 严格停止条件（§62）
本轮**未运行 FIT C/D**（dark 群体绝对率依赖未知 singles rate + live time；electronics vs physical 未决定性区分）。**MODEL INADEQUATE（率未闭合）**。不报告事件组成 fraction 作测量。

## 8. v6→v7→v8→v9 机制结论演化
| 版本 | dark 群体解释 | 状态 |
|---|---|---|
| v6 | samedark/crossdark 抽象 component | 撤回（无 forward model） |
| v7 | （data-blocked） | — |
| v8 | electronics crosstalk 确定 | **撤回**（正控制失败） |
| **v9** | **真实多粒子事件（electronics 未证实）** | 当前最佳；绝对率待 singles+livetime |
