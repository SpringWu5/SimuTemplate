# simulation_v6 — STEP 4–5 small Q model + asymmetry nature

## Q8: +20% 左列 threshold 是否与 Q spectra 兼容？
**Topology 层面兼容，但 threshold 与 gain 完全简并：**
| kind | T02/T13 | U01/L23 | trig_rate Ch0/1/2/3 |
|---|---|---|---|
| threshold +20% | 2.01 | 1.24 | .523/.448/.523/.498 |
| gain -20% | 2.01 | 1.24 | .523/.448/.523/.498 |
| none (纯几何) | 1.61 | 1.12 | .523/.531/.523/.581 |

threshold 和 gain 给出**完全相同**的 topology 比率与触发率 → **topology 无法区分二者**。

## Q9: 它更像 threshold、gain 还是 geometry？
- **纯几何**已给出 T02/T13≈1.61（生成平面/几何残余左右差异），+20% electronics 推到 2.0。
- 区分 threshold vs gain 的**唯一可观测**：**Q 谱形状**。
  - threshold asymmetry：左列 Q 谱**形状不变**，仅低 Q 事件被切（surviving mean Q 左=右）。
  - gain asymmetry：左列 Q **整体下移** 1/(1+dx)（mean Q 左<右）。
- mean-Q-per-channel 是判别量（`figures/02` 下排左图）。
- **结论**："+20%" 目前是 **effective proxy**；其物理本质（threshold / gain / 部分 geometry）必须由真实 Ch0–Ch3 Q 谱形状判定。本轮无法从 topology 单独确定。

## small forward model（`small_v6.py`）
path→Edep(Landau)→PE(Poisson,Y=12/MeV)→Q=g×PE→amp+noise→threshold→fired。
per-channel gain g_i + threshold thr_i，支持 thr/gain/none 三种 asymmetry kind。
