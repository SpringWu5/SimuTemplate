# simulation_v5 — STEP 5–7 forward model + channel asymmetry 结论

## STEP 5: small detector forward model
- Edep: same-layer mean **3.14 MeV**, cross-layer mean **4.06 MeV**（cross 更长 path）。
- 触发效率 vs Edep：在 ~1–3 MeV 处转换（取决于 threshold）。
- 完整链路 track→path→Edep(Landau)→PE(Poisson)→amp(+noise)→threshold 已建立。

## STEP 7 (Q5): threshold 能否提高 single-muon same-layer？
**不能。** cross-layer 的 path/Edep 更大（4.06 vs 3.14 MeV），所以提高 threshold 会
**优先丢失 same-layer 事件**，same-layer fraction 随 threshold **下降或持平**，永远到不了
data 的 0.53。同一 threshold 下 T02/T13≈1（对称通道）。
⇒ **path-length selection 假设被否定**：detector-level threshold 无法把 single-muon
same-layer 从 ~6% 提到 53%。

## STEP 6 (Q6, Q7): channel threshold/gain 不对称能否解释 T02/T13=2.1 和 U01/L23=1.37？
**能，且只需 ~20%。** 在 base threshold=0.5 MIP（效率转换区）：
- **joint best: dx=+0.20（左列 Ch1,Ch3 threshold +20%）, dz=0.00**
- → **T02/T13=1.97**（data 2.08），**U01/L23=1.34**（data 1.37）✓
- 同一组左右不对称同时解释两个比率，**无需独立调 upper/lower**。
- 20% 是合理电子学差异，**不是 5×**。

## 但 single-muon 仍无法解释整体拓扑
带最佳不对称的 single-muon topology：
| | 01 | 23 | 02 | 13 | 03 | 12 | same-layer |
|---|---|---|---|---|---|---|---|
| MC(不对称) | .022 | .017 | .519 | .264 | .074 | .105 | **.039** |
| data | .306 | .224 | .204 | .098 | .098 | .071 | **.53** |

⇒ 不对称修正了比率（T02/T13, U01/L23），但 single-muon 仍严重缺 same-layer、cross-layer 严重过量。
**same-layer 53% 必须来自多粒子/fake 分量**，与 STEP 4 结论一致。

## 关键数值（tables/）
- v5_samelayer_vs_threshold.csv: same-layer 随 threshold 下降
- v5_channel_asymmetry.csv: dx=+0.20, base=0.5 MIP
