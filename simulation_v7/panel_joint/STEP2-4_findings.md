# simulation_v7 — STEP 2 & STEP 4 findings

## STEP 2: panel joint 8-channel audit（Q5, Q6, Q12）
独立 NB vs Geant4 truth（同一 Edep 输入）：

| 统计量 | Geant4 | NB model |
|---|---|---|
| per-channel mean | 11.54 | 11.65 ✓ |
| per-channel var | 77.4 | 97.0（偏高） |
| zero-frac (Ch4) | 0.008 | 0.039（偏高） |
| min-channel mean | 3.61 | 2.67（偏低） |
| min P(=0) | 0.083 | 0.192（偏高） |
| mean off-diag corr | 0.200 | 0.225 ✓ |
| P(M8) @thr=1 | 0.675 | 0.589（略低） |

- **NB 过估 zero-frac 和 min-P(0)** → 对 "panel dark" 概率是**保守上界**（高估 dark）。
- 因此 B2/B3 结论（single essentially never dark，P~0.000-0.002）**稳健**：即便 NB（偏 dark），single dark 仍 ~0；Geant4 truth 更低。
- NB 略低 P(M8)（0.59 vs 0.68），因过估零通道尾。**精确 M-dist 需 event-level Geant4 resampling**（120 event 太少）。
- **Q6**: 升级方向 = Geant4 event-level empirical resampling（层次化：event total brightness B + sharing f_i）；本轮 NB 作保守近似足够支撑 B2/B3，但不用于精确 panel M8 率。

## STEP 4: 左右 geometry audit（Q21, Q22, §45, §46）
detector 坐标确认**严格左右镜像对称**：Ch0 x=+6, Ch1 x=−6（slab 居中 x=0）。

高统计 unbiased mirror test（30M, HW=30）：
- **T02/T13 = 1.014 ± 0.020**（z=0.50σ，与 1.0 兼容）。
- T03/T12 = 1.049（也 ~1）。
- **V6 的 "pure geometry 1.61" 是低统计伪影**（few-event IS resampling 噪声）。

⇒ **Q21**: 纯几何**不**给 T02/T13≈1.61；那是噪声。**Q22**: mirror geometry **恢复 T02/T13≈1**。
⇒ **data 的左右不对称（T02/T13=2.08）完全是 electronics（effective response asymmetry），非几何。**
- U01/L23 在 MC 有 generation-plane 偏置（z=10 平面 → 近水平 μ 子偏上层），这是 generator artifact，非物理；data 的 U01/L23 需真实宇宙线方向分布。

## STEP 3: real data features — BLOCKED
repo 中**无** analysis_v4/ 或 event_features CSV（仅 build log）。**真实 Q_min/Q_balance/minor-major/timing/template-score 未上传到模拟环境。**
⇒ STEP 3（data feature book）与 FIT C/D 的 Q-特征比较**无法完成**，除非提供实验数据。这是本轮硬阻塞。
