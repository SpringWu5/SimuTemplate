#!/usr/bin/env python3
"""run_step8_10.py -- panel PE model, B2/B3, same-layer M8 S1/S2 (STEP 8-10)."""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, response as R, panel as P, geometry as G, toys as T

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
# data panel rates
DATA = dict(cross_M8=50, cross_nonM8=70, cross_tot=120,
            same_M8=7, same_nonM8=128, same_tot=135,
            B2=52, B3=18)

print("== STEP 8-10: panel PE model, B2/B3, same-layer M8 ==")
iss = GEN.sample_single(8_000_000, n=2.0, rng=np.random.default_rng(201))
s = GEN.resample_triggered(iss, 800_000, np.random.default_rng(202), Mmin=1)
H = s["H"]; M = s["M"]; pslab = s["pslab"]
rng = np.random.default_rng(9)

# ---------- STEP 9: panel M8 vs SiPM threshold (single cross-layer) ----------
print("  STEP 9: panel M8 vs threshold (single cross-muon) ...")
cross = ((H[:, 0] & H[:, 2]) | (H[:, 1] & H[:, 3]) |
         (H[:, 0] & H[:, 3]) | (H[:, 1] & H[:, 2])) & (M == 2) & (pslab > 0)
psub = pslab[cross]
pe_cross, e_cross = P.panel_pe(psub, np.random.default_rng(91), Y_slab=400.0, pde=0.40)
print(f"    cross-layer n={cross.sum()}, slab Edep mean={e_cross.mean():.2f} MeV, "
      f"total PE mean={pe_cross.sum(1).mean():.1f}")
thr_arr = [1, 2, 3, 5, 8, 10, 15, 20, 30]
pM8 = []; pdark = []
for thr in thr_arr:
    m8, fired = P.m8_mask(pe_cross, thr, noise=3.0, rng=np.random.default_rng(thr))
    pM8.append(float(m8.mean())); pdark.append(float((~fired.any(axis=1)).mean()))
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(thr_arr, pM8, "o-", label="P(M8)")
ax[0].plot(thr_arr, pdark, "s-", label="P(panel all-dark)")
ax[0].axhline(0.42, color="k", ls="--", label="data cross M8=42%")
ax[0].set_xlabel("SiPM threshold (PE)"); ax[0].set_ylabel("probability")
ax[0].set_title("STEP9: single cross-muon panel vs thr"); ax[0].legend(fontsize=8)
# total PE distribution (bright/dark bimodality check)
ax[1].hist(pe_cross.sum(1), 60, density=True)
ax[1].set_xlabel("total panel PE (8-SiPM sum)"); ax[1].set_title("single cross-muon panel PE")
ax[1].axvline(50, color="r", ls="--", label="~M8 threshold region")
ax[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/15_panel_threshold.png", dpi=130); plt.close()

# find threshold giving P(M8)~0.42 (data cross M8 rate)
i42 = np.argmin(np.abs(np.array(pM8) - 0.42))
thr_at_42 = thr_arr[i42]
print(f"    threshold giving P(M8)~0.42: thr={thr_at_42} PE (P(dark)={pdark[i42]:.3f})")
print(f"    => P(panel all-dark | single cross-muon) = {pdark[i42]:.3f}")

# ---------- STEP 10: B2/B3 compatibility ----------
print("  STEP 10: B2/B3 ...")
# small Edep_min and balance for cross-layer
edep_cross = np.zeros((cross.sum(), 4))
for i, ch in enumerate(G.ALLCH):
    from simulation_v5.response import landau_edep as _le
    edep_cross[:, i] = np.where(s["paths"][ch][cross] > 0,
                                _le(np.where(s["paths"][ch][cross] > 0, s["paths"][ch][cross], 1e-3),
                                    np.random.default_rng(70 + i)), 0)
# per topology, the two hit channels
def two_edep(topo):
    a, b = G.TOP_CH[topo]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
    m = cross & H[:, ia] & H[:, ib]
    ea = edep_cross[m & H[cross][:, ia] if False else np.zeros_like(m), ia]  # placeholder
    return m
# simpler: compute edep_min for each cross-layer event from edep_cross
hitmask = H[cross]
ea = np.where(hitmask[:, 0], edep_cross[:, 0], np.where(hitmask[:, 1], edep_cross[:, 1], 0))
# build the two-hit edep per event properly
e2 = np.sort(np.where(hitmask, edep_cross, -1), axis=1)[:, ::-1]  # desc, hit ones first
e_hi = e2[:, 0]; e_lo = np.where(e2[:, 1] >= 0, e2[:, 1], e2[:, 0])
emin_cross = np.minimum(e_hi, e_lo)
# panel PE for these
pe_c = pe_cross  # aligned with cross ordering
tot_pe = pe_c.sum(1)
# B3-like: strong small (e_lo high) but panel dark
strong = e_lo > 3.0   # "not particularly weak"
m8_c, fired_c = P.m8_mask(pe_c, thr_at_42, noise=3.0, rng=np.random.default_rng(44))
dark = ~fired_c.any(axis=1)
print(f"    cross: P(strong small & panel dark) = {np.mean(strong & dark):.3f} (B3 ~ {DATA['B3']}/{DATA['cross_tot']}={DATA['B3']/DATA['cross_tot']:.3f})")
print(f"    cross: P(panel dark) = {np.mean(dark):.3f} (B2+B3 ~ {(DATA['B2']+DATA['B3'])/DATA['cross_tot']:.3f})")
# Q_min / Q_balance proxy
qmin = e_lo
qbal = e_lo / np.maximum(e_hi, 1e-6)
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].hist(qmin[dark], 40, alpha=0.5, label=f"panel-dark (n={dark.sum()})", density=True)
ax[0].hist(qmin[~dark], 40, alpha=0.5, label="panel-M8", density=True)
ax[0].set_xlabel("small Edep_min (MeV, Q proxy)"); ax[0].legend(fontsize=8)
ax[0].set_title("B2/B3: small Edep_min by panel status")
ax[1].scatter(qmin, tot_pe, c=np.where(dark, "r", "g"), s=3, alpha=0.3)
ax[1].set_xlabel("small Edep_min (MeV)"); ax[1].set_ylabel("total panel PE")
ax[1].set_title("small Edep vs panel PE (green=M8, red=dark)")
ax[1].set_ylim(0, np.percentile(tot_pe, 99))
plt.tight_layout(); plt.savefig(f"{FIG}/16_b2b3_panel.png", dpi=130); plt.close()
with open(f"{TBL}/v5_b2b3_panel.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["metric", "value"])
    w_.writerow(["cross_n", int(cross.sum())])
    w_.writerow(["thr_pe_at_M8_42pct", thr_at_42])
    w_.writerow(["P_panel_dark_single_cross", round(float(np.mean(dark)), 4)])
    w_.writerow(["P_strong_small_dark_B3like", round(float(np.mean(strong & dark)), 4)])
    w_.writerow(["data_B3_frac", round(DATA['B3']/DATA['cross_tot'], 4)])
    w_.writerow(["data_B2pB3_frac", round((DATA['B2']+DATA['B3'])/DATA['cross_tot'], 4)])

# ---------- STEP 8: same-layer M8 S1/S2 ----------
print("  STEP 8: same-layer M8 mechanisms S1/S2 ...")
# S2 primary: single muon hitting exactly ONE upper block + crossing slab, no lower block
up = H[:, 0] | H[:, 1]           # any upper
lo = H[:, 2] | H[:, 3]           # any lower
one_up = ((H[:, 0] ^ H[:, 1]) & ~lo)   # exactly one upper, no lower
s2_primary = one_up & (pslab > 0)
print(f"    S2 primary (one upper + slab, no lower): n={s2_primary.sum()} of {len(s2_primary)} "
      f"({100*s2_primary.mean():.3f}%)")
# S2 full: add a secondary hit on the same-layer neighbour
rng2 = np.random.default_rng(88)
H_s2 = H.copy()
idx = np.where(s2_primary)[0]
for j in idx:
    if H[j, 0]: H_s2[j, 1] = True     # Ch0 present -> add Ch1
    elif H[j, 1]: H_s2[j, 0] = True
M_s2 = H_s2.sum(1)
u01_s2 = (H_s2[:, 0] & H_s2[:, 1]) & (M_s2 == 2)
print(f"    S2 -> U01 events: {u01_s2.sum()}")
# panel for S2 primaries
pe_s2, e_s2 = P.panel_pe(pslab[s2_primary], np.random.default_rng(92), Y_slab=400.0, pde=0.40)
m8_s2, _ = P.m8_mask(pe_s2, thr_at_42, noise=3.0, rng=np.random.default_rng(93))
print(f"    S2: P(panel M8 | U01+S2-primary) = {m8_s2.mean():.3f} "
      f"(data same-M8 = {DATA['same_M8']}/{DATA['same_tot']}={DATA['same_M8']/DATA['same_tot']:.3f})")

# S1: two physical tracks both same-layer; need one to cross slab
# use correlated_two_track with det_x on the M>=1 base, require slab crossing on either
Hc, _, info = T.correlated_two_track(s, p_corr=1.0, s_cm=12.0, sigma_deg=5.0,
                                     rng=np.random.default_rng(81), offset_mode="det_x")
# slab crossing: track1 or track2 crosses slab. track1 pslab known; track2 (info P2,d2) recompute
from simulation_v5.geometry import ray_box
hs2, _ = ray_box(info["P2"], info["d2"], G.SLAB_MIN, G.SLAB_MAX)
slab_either = (pslab > 0) | hs2
Mc = Hc.sum(1); u01_s1 = (Hc[:, 0] & Hc[:, 1]) & (Mc == 2)
l23_s1 = (Hc[:, 2] & Hc[:, 3]) & (Mc == 2)
same_s1 = u01_s1 | l23_s1
m8_s1 = same_s1 & slab_either
print(f"    S1 corr: same-layer M2 = {same_s1.sum()}, of which slab-crossed = {m8_s1.sum()} "
      f"({100*m8_s1.mean()/max(same_s1.mean(),1e-9):.1f}% of same-layer)")

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].bar(["S2\n(one real+extra)", "S1\n(two physical)"],
          [m8_s2.mean() if u01_s2.sum() else 0, float(m8_s1.sum())/max(float(same_s1.sum()),1)])
ax[0].axhline(DATA['same_M8']/DATA['same_tot'], color="r", ls="--", label=f"data same-M8={DATA['same_M8']/DATA['same_tot']:.3f}")
ax[0].set_ylabel("P(panel M8 | same-layer)"); ax[0].legend(fontsize=8)
ax[0].set_title("STEP8: same-layer M8 mechanisms")
# panel PE for S2
ax[1].hist(pe_s2.sum(1), 30, density=True, alpha=0.6, label="S2 primary panel PE")
ax[1].hist(pe_cross.sum(1), 30, density=True, alpha=0.6, label="single cross panel PE")
ax[1].set_xlabel("total panel PE"); ax[1].legend(fontsize=8)
ax[1].set_title("panel PE: S2 vs cross")
plt.tight_layout(); plt.savefig(f"{FIG}/17_samelayer_M8.png", dpi=130); plt.close()
with open(f"{TBL}/v5_samelayer_M8.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["mechanism", "P_M8_given_samelayer", "n"])
    w_.writerow(["S2_one_real_plus_extra", round(float(m8_s2.mean()) if u01_s2.sum() else 0, 4), int(u01_s2.sum())])
    w_.writerow(["S1_two_physical", round(float(m8_s1.sum())/max(float(same_s1.sum()),1), 4), int(same_s1.sum())])
    w_.writerow(["data_same_M8_frac", round(DATA['same_M8']/DATA['same_tot'], 4), DATA['same_M8']])
print("STEP 8-10 done.")
