# simulation_v6 — STEP 1–3 统一 panel forward model

## STEP 1 审计结论（见 panel_audit/STEP1_audit.md）
- V5 `panel.py` Y_slab=400 **凭空取值**，比 Geant4 真值（**17 photons/MeV**）亮 **~23×**。
- 用固定-f_i Poisson，丢失 Geant4 的 **过dispersion（F=4-7）和零光子尾（8.3% event 有 SiPM=0）**。
- **撤回** V5 "P(panel dark|single)=0.000" → 改为校准后的 threshold-dependent 值。

## STEP 2 统一 model（`panel_v6.py`）
- 每 SiPM：`photons_i ~ NegBin(mean=rate_i×Edep, F=F_i)`，rate/F 校准自 Geant4（rate~1.7-2.4 ph/MeV, F~3.7-6.7）。
- `PE_i ~ Poisson(photons_i×PDE)`，叠加 gain/noise，定义 M=Σfired, M8=all 8。

## STEP 3 验证（`figures/01_panel_model_vs_geant4.png`）
- 每 SiPM mean photons：model 与 Geant4 吻合（11.65 vs 11.54 等）。
- P(M8) vs raw threshold：低阈值区吻合（thr=1: 0.586 vs 0.675；thr=2: 0.408 vs 0.467）；高阈值 model 略低（channel 间相关未完全捕获，次要）。

## 重新计算 P(panel dark | single cross)（回答 Q3, Q4）
| pde | raw thr | P(M0) | P(no ch>thr) | P(M8) |
|---|---|---|---|---|
| 0.40 | 0.5(≥1ph) | 0.0000 | 0.0000 | 0.30 |
| 0.40 | 1.0(≥2ph) | 0.0000 | 0.0000 | 0.16 |
| 0.40 | 2.0(≥3ph) | 0.0022 | 0.0022 | 0.04 |

**P(panel 完全 dark | single cross) = 0.000–0.002**（修正 V5 的 "0.000"，但仍可忽略）。
data cross-nonM8 = 58% → **远超 single-muon dark 尾部**。

## 关键：亮/暗二峰（§9, 回答 data bimodality）
在 data-M8≈42% 对应的工作点（~2 raw ph/SiPM）：
- single cross-muon M 分布：**M4-7=23%, M8=77%, M0≈0**（连续、偏亮，无 dark 峰）。
- single cross total PE：mean 29, **P(tot<2)=0.0000**（几乎无真正 dark）。
- data：**M8 score 40-60 vs nonM8 ~0，强二峰，中间空**。

⇒ **single-muon 是连续分布，data 是二峰** → data nonM8（score~0）**不是** single 的 partial-light 尾（那是 M4-7, score~10-25），而是**独立 dark 群体**。
**这强化（而非推翻）V5 的 B2/B3 结论**，但把"P=0"修正为校准后的"P~0.000-0.002"，并明确二峰是 mixture 证据。

## data-M8 校准点
cross-M8=42% ↔ ~2 raw photons/SiPM（~0.8 PE/SiPM @ PDE 0.4）。此点 single cross 的 non-M8 尾是 M=4-7（亮），与 data nonM8(score~0) 不兼容。
