#!/usr/bin/env python3
"""run_step6_8_mechanisms.py -- samedark/crossdark/S2 mechanism decomposition (STEP 6-8)."""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, geometry as G, toys as T
from simulation_v5.response import landau_edep
from simulation_v6 import small_v6 as SM, panel_v6 as PV

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
DATA_SAME_M8 = 7 / 135.0

print("== STEP 6-8: mechanism decomposition ==")
iss = GEN.sample_single(8000000, n=2.0, rng=np.random.default_rng(201))
s = GEN.resample_triggered(iss, 500000, np.random.default_rng(202), Mmin=1)
rng = np.random.default_rng(5)
edep, npe = SM.small_edep_pe(s["paths"], rng)
Hg = s["H"]; Ng = Hg.shape[0]; pslab = s["pslab"]; M0 = s["M"]
gain, thr = SM.asym_params(kind="thr", dx=0.20, base_thr_mip=0.20)
fired0, Q0, _ = SM.fire_and_Q(npe, np.random.default_rng(7), gain, thr, geom_H=Hg)
edep_slab = np.where(pslab > 0, np.array([landau_edep(float(p), np.random.default_rng(9)) for p in pslab]), 0.0)
pr = PV.panel_response(edep_slab, np.random.default_rng(11), pde=0.40, noise_pe=0.5, thr_pe=np.full(8, 0.8))
panel_M8 = pr["M8"]; tot_pe = pr["pe"].sum(1)
# "truly dark" = total panel PE below a near-zero cut (data nonM8 score ~0)
DARK_CUT = 3.0   # PE: data nonM8 coherent score ~0; M4-7 single tail is ~10-25 PE
truly_dark = tot_pe < DARK_CUT

def same_layer_mask(F):
    sl_pair = (F[:, 0] & F[:, 1]) | (F[:, 2] & F[:, 3])
    return sl_pair & (F.sum(1) == 2)

def cross_mask(F):
    sl_pair = (F[:, 0] & F[:, 1]) | (F[:, 2] & F[:, 3])
    return (~sl_pair) & (F.sum(1) == 2)

def qmin_qbal(F, Q, mask):
    f = F[mask]; q = Q[mask]
    qs = np.sort(np.where(f & (q > 0), q, -1), axis=1)[:, ::-1]
    qhi = qs[:, 0]; qlo = np.where(qs[:, 1] >= 0, qs[:, 1], qs[:, 0])
    return qhi, qlo

# ---- SD1: normal same-layer single ----
sd1 = same_layer_mask(fired0)
qhi1, qlo1 = qmin_qbal(fired0, Q0, sd1)
print(f"  SD1 normal same-layer: n={sd1.sum()}, Q_min={np.mean(qlo1):.1f}, panel-dark={np.mean(~panel_M8[sd1]):.3f}")

# ---- SD2: electronics copy (track copied events specifically) ----
Hsd2 = fired0.copy(); Qsd2 = Q0.copy()
copied = np.zeros(Ng, bool)
ratios_sd2 = []
rng2 = np.random.default_rng(12)
single_block = fired0.sum(1) == 1
for j in np.where(single_block)[0]:
    if rng2.random() < 0.5:
        for ch, neigh in T.SAME_LAYER_NEIGH.items():
            ci = G.ALLCH.index(ch); ni = G.ALLCH.index(neigh)
            if fired0[j, ci]:
                r = float(np.clip(rng2.normal(0.35, 0.18), 0.05, 0.9))
                Hsd2[j, ni] = True; Qsd2[j, ni] = r * Q0[j, ci]
                copied[j] = True; ratios_sd2.append(r); break
sd2_sl = same_layer_mask(Hsd2) & copied
qhi2, qlo2 = qmin_qbal(Hsd2, Qsd2, sd2_sl)
ratio_sd2 = np.array(ratios_sd2)
print(f"  SD2 elec copy: copied same-layer n={sd2_sl.sum()}, minor/major={np.mean(ratio_sd2):.2f}±{np.std(ratio_sd2):.2f}, "
      f"panel-dark={np.mean(~panel_M8[sd2_sl]):.3f}")

# ---- SD3: physical secondary (correlated) ----
Hc, _, _ = T.correlated_two_track(s, p_corr=0.5, s_cm=12.0, sigma_deg=5.0,
                                  rng=np.random.default_rng(15), offset_mode="det_x")
f3, Q3, _ = SM.fire_and_Q(npe, np.random.default_rng(16), gain, thr, geom_H=Hc)
sd3_sl = same_layer_mask(f3)
qhi3, qlo3 = qmin_qbal(f3, Q3, sd3_sl)
ratio_sd3 = qlo3 / np.maximum(qhi3, 1e-6)
m3_rate = np.mean(f3.sum(1) == 3); m4_rate = np.mean(f3.sum(1) == 4)
print(f"  SD3 physical: same-layer n={sd3_sl.sum()}, M3={m3_rate:.4f} M4={m4_rate:.4f}, "
      f"minor/major={np.nanmean(ratio_sd3):.2f}")

# ---- B2/B3 conditional on single cross ----
cr = cross_mask(fired0)
qhi_cr, qlo_cr = qmin_qbal(fired0, Q0, cr)
dark_cr = truly_dark[cr]            # truly dark (score~0), not merely "not M8"
notm8_cr = ~panel_M8[cr]
q05 = np.percentile(qlo_cr, 5); qmed = np.percentile(qlo_cr, 50)
P_b2 = np.mean(qlo_cr < q05)
P_dark_strong = np.mean((qlo_cr > qmed) & dark_cr)
P_notm8_strong = np.mean((qlo_cr > qmed) & notm8_cr)
print(f"\n  B2/B3 (single cross, n={cr.sum()}):")
print(f"    P(B2-like weak Q_min | single cross) = {P_b2:.4f}")
print(f"    P(strong small & TRULY-dark panel | single cross) = {P_dark_strong:.5f}")
print(f"    [ref: P(strong & not-M8 partial-light) = {P_notm8_strong:.3f} -- but partial-light != data dark]")

# ---- S2 predicted same-M8 rate (direct counting) ----
# S2-E: primary = single-block + slab-crossing; copy completes same-layer pair; panel bright
one_up_slab = (fired0.sum(1) == 1) & (fired0[:, 0] | fired0[:, 1]) & (pslab > 0)
# build the S2-E event: add neighbour copy to these primaries
Hs2 = fired0.copy()
rng_s2 = np.random.default_rng(77)
s2_done = np.zeros(Ng, bool)
for j in np.where(one_up_slab)[0]:
    if rng_s2.random() < 0.5:
        if Hs2[j, 0]: Hs2[j, 1] = True
        elif Hs2[j, 1]: Hs2[j, 0] = True
        elif Hs2[j, 2]: Hs2[j, 3] = True
        elif Hs2[j, 3]: Hs2[j, 2] = True
        s2_done[j] = True
s2_samelayer_m2 = same_layer_mask(Hs2) & s2_done
s2_samelayer_m8 = s2_samelayer_m2 & panel_M8
p_s2_m8 = np.mean(s2_samelayer_m8) / max(np.mean(same_layer_mask(fired0)), 1e-9)
print(f"\n  S2-E direct: same-layer-M2 from S2 = {s2_samelayer_m2.sum()}, of which M8 = {s2_samelayer_m8.sum()}")
# P(same-M8 | same-layer) = S2-M8 / (SD1-normal + S2). Report vs p_copy.
sd1_n = same_layer_mask(fired0).sum()
for pc in [0.1, 0.3, 0.5]:
    n_s2 = s2_samelayer_m2.sum() * (pc / 0.5)
    n_s2m8 = s2_samelayer_m8.sum() * (pc / 0.5)
    p = n_s2m8 / max(sd1_n + n_s2, 1)
    print(f"    p_copy={pc}: P(same-M8|same-layer) ~ {p:.3f}  (data {DATA_SAME_M8:.3f})")
p_s2_m8 = s2_samelayer_m8.sum() / max(sd1_n + s2_samelayer_m2.sum(), 1)

# ---- plots ----
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes[0, 0].hist(ratio_sd2, 40, alpha=0.5, label=f"SD2 elec ({np.mean(ratio_sd2):.2f})", density=True)
axes[0, 0].hist(ratio_sd3[~np.isnan(ratio_sd3)], 40, alpha=0.5, label=f"SD3 phys ({np.nanmean(ratio_sd3):.2f})", density=True)
axes[0, 0].set_xlabel("Q_minor/Q_major"); axes[0, 0].legend(fontsize=8); axes[0, 0].set_title("SD2 vs SD3")
axes[0, 1].bar(["SD1", "SD2", "SD3"], [np.mean(~panel_M8[sd1]), np.mean(~panel_M8[sd2_sl]), np.mean(~panel_M8[sd3_sl])])
axes[0, 1].set_ylabel("P(panel dark)"); axes[0, 1].set_title("same-layer panel-dark by mechanism")
tot_cr = tot_pe[cr]
axes[1, 0].scatter(qlo_cr, tot_cr, c=np.where(dark_cr, "r", "g"), s=4, alpha=0.3)
axes[1, 0].set_xlabel("Q_min (cross)"); axes[1, 0].set_ylabel("total panel PE"); axes[1, 0].set_title("B3: strong-small vs panel")
axes[1, 0].set_ylim(0, np.percentile(tot_cr, 99))
axes[1, 1].bar(["B2(weak)", "B3(strong+truly-dark)"], [P_b2, P_dark_strong])
axes[1, 1].set_ylabel("P(class | single cross)"); axes[1, 1].set_title("B2/B3 single compatibility")
plt.tight_layout(); plt.savefig(f"{FIG}/03_mechanism_decomposition.png", dpi=130); plt.close()

with open(f"{TBL}/v6_mechanisms.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["mechanism", "observable", "value"])
    for nm, v in [("SD1_n", int(sd1.sum())), ("SD1_Qmin", float(np.mean(qlo1))), ("SD1_panel_dark", float(np.mean(~panel_M8[sd1]))),
                  ("SD2_minor_major", float(np.mean(ratio_sd2))), ("SD2_panel_dark", float(np.mean(~panel_M8[sd2_sl]))),
                  ("SD3_M3", float(m3_rate)), ("SD3_M4", float(m4_rate)), ("SD3_minor_major", float(np.nanmean(ratio_sd3))),
                  ("B2_P_single", float(P_b2)), ("B3_P_strong_trulydark_single", float(P_dark_strong)),
                  ("S2_predicted_sameM8", float(p_s2_m8)), ("data_sameM8", float(DATA_SAME_M8))]:
        w.writerow([nm, "", round(v, 5)])
print("STEP 6-8 done.")
