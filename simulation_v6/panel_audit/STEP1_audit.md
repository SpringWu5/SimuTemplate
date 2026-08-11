# simulation_v6 — STEP 1 panel audit：V5 panel PE model vs V4 Geant4 optical MC

## 核心矛盾
V5 `panel.py` 给出 single cross-muon panel **~772 PE 总量（~96 PE/SiPM）** →
P(panel dark|single)=0.000。但 V4 corrected optical MC 给出 threshold-dependent
P(M8)：~64%@1 raw photon，~44%@2 raw photons。两者差 **~1-2 个量级**。

## 逐行审计 panel.py（§3 八问）
1. **8 SiPM PE 如何产生？** `ngam=Poisson(Y_slab×Edep)`，`pe_i=Poisson(ngam×pde×f_i)`。
2. **总 PE 是否均匀除以 8？** 否——用 sharing 向量 f_i（~0.12），但 f_i 是**固定**的。
3. **是否用真实 optical sharing？** 仅用平均 f_i，**丢失 event-by-event 位置依赖**。
4. **是否根据 track intersection 决定每 SiPM 光量？** **否**——完全忽略穿过位置。
5. **是否保留 f4..f11 event-by-event 涨落？** **否**——f_i 固定，仅 Poisson 涨落。
6. **真实每通道低光尾？** **无**——Poisson(96) 的 P(0)≈10⁻⁴²，无零光子尾。
7. **PDE/gain/noise？** 有 PDE(0.40) + Gaussian noise，但 build on 错误的高 yield。
8. **M8 定义？** all 8 SiPM > thr_pe（定义本身 OK，问题在 PE 量级）。

## 根因：Y_slab=400 是凭空取值，未校准到 Geant4
Geant4 optical 真值（output_stacked_v4.root, 120 slab-crossed events）：
- **yield = 17 photons/MeV**（81.5 photons / 4.82 MeV），不是 400。
- 每 SiPM raw photons：mean ~10-12，**var/mean (F) = 4.6-6.7（严重过dispersed）**。
- Poisson(10) 预测 P(0)=4.5e-5，但 Geant4 实测 **P(0)=0.8-3.3%**（有真实零光子尾）。
- **8.3% 的 event 至少有一个 SiPM 收到 0 光子**。
- M-distribution：P(M8)@1ph=0.675, @2ph=0.467, @5ph=0.258。

V5 `Y_slab=400` → 96 PE/SiPM，比 Geant4 真值（~10 raw ≈ 4 PE）亮 **~23×**。
固定-f_i Poisson 无法产生过dispersion（F=1）和零光子尾。

## 结论（回答 Q1, Q2）
- **Q1**: V5 panel 比旧 optical MC 亮 ~23×，因为 Y_slab=400 凭空取值（应为 17）且用固定-f_i
  Poisson（丢失位置依赖的过dispersion 和零光子尾）。
- **Q2**: **存在"近似均匀分光 + 错误 yield"问题。** 不是字面均匀除以 8（用了 f_i），但 f_i 固定
  且 yield 错误，效果近似——P(M8)≈1 的结论**必须撤回**，改为校准到 Geant4 的 threshold-dependent 值。

## 修正方向
建立唯一 panel forward model，校准到 Geant4 optical library：
- yield = 17 photons/MeV；
- 每 SiPM 用 **Negative Binomial**（过dispersion F≈6，匹配 Geant4 var/mean）；
- 保留 event-by-event sharing 涨落（位置依赖）；
- PDE + gain + noise 叠加；
- 必须复现 Geant4 M-distribution（P(M8)@threshold）才算合格。
