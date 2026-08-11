# simulation_v7 — STEP 1 statistics audit

## Q1, Q2: V6 FIT A dof/p 不一致 — 已解决
V6 正文写 "8.9/5 p=0.114"，图标 "9/3 p=0.03"。**根因：同一 Pearson，不同 dof（来自退化的多余 component）。** 用审计后的 stats_v7（dof = K_eff - 1 - (C-1)，K_eff=有 model expectation 的 bin 数，unit-tested）重算：

| 模型 | Pearson | dof | p_pearson | 判定 |
|---|---|---|---|---|
| 1-comp single | 75.8 | 4 | 0.0000 | INADEQUATE |
| **2-comp (AIC best)** | **10.4** | **5** | **0.065** | ADEQUATE（边缘） |
| 3-comp | 10.4 | 4 | 0.034 | 边缘 |
| 4-comp | 10.4 | 3 | 0.016 | 边缘（>0.01） |

- AIC 选 2-comp（883.8）；多余 component 在 topology 层退化（不改善 Pearson，只降 dof）。
- **诚实 FIT-A GOF：p=0.065（2-comp, AIC-best），topology 边缘 adequate。**
- unit test 验证：dof 公式正确；p-value 在 truth 下 ~Uniform(0,1)（mean 0.5, Type-I 5%）；错误模型 >80% 被拒；grid_fit 恢复 input fraction。

## Q3: M3=2 的 PPC 概率
- median=2，68%=(1,3)，95%=(0,5)，**P(N=2)=0.271**，P(N≥2)=0.61。
- data M3=2 **在 95% 区间内**，P(N=2)=0.27（相当 likely）。
- ⇒ **V6 "M3 自然兼容" 结论正确**（图中 M3 集中在低值但 2 在主体内）。

## Q4: same-M8=7 的 PPC 概率
- median=17，68%=(13,21)，95%=(10,25)，**P(N≤7)=0.004**。
- data same-M8=7 **超出 95% 区间**，P(N≤7)=0.4%。
- ⇒ **当前模型 overpredict same-M8（预测 ~17 vs data 7），S2 rate 张力量化为 P=0.004。**
- 按 §42/§65 停止条件：same-M8 PPC < 0.01 → 该 observable **失败**。

## FIT B（审计后）
- 4-comp f=[0.429, 0.50, 0, 0.071]，Pearson=17.5/9，**p=0.042**（>0.01 adequate），max|pull|=1.95。
- 但 same-M8 PPC 失败 → 整体仍不充分。

## 结论
- 统计模块已审计 + unit-tested（6 test 全过）。
- FIT A 真正 p=0.065（2-comp）；FIT B p=0.042；M3 兼容；**same-M8 overpredicted（P≤7=0.004）是当前模型的关键失败点**，须在 STEP 9（S2 rate）解决。
