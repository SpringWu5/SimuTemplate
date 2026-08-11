#!/usr/bin/env python3
"""run_step4_5_small.py -- small Q forward model + asymmetry nature (STEP 4-5).

Q8/Q9: is the +20% left-column asymmetry a threshold, gain, or geometry effect?
Test by comparing Q-spectrum distortions and per-channel trigger rates under
each hypothesis. Same +20% must match T02/T13=2.08 AND be consistent with Q.
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, geometry as G
from simulation_v6 import small_v6 as SM

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
DATA_T02_T13 = 52 / 25.0; DATA_U01_L23 = 78 / 57.0

print("== STEP 4-5: small Q model + asymmetry nature ==")
iss = GEN.sample_single(8000000, n=2.0, rng=np.random.default_rng(101))
s = GEN.resample_triggered(iss, 600000, np.random.default_rng(102), Mmin=1)
rng = np.random.default_rng(5)
edep, npe = SM.small_edep_pe(s["paths"], rng)
Hg = s["H"]; Ng = Hg.shape[0]


def topo_from_fired(fired):
    M = fired.sum(1); m2 = M == 2
    tf = {}
    for t in G.TOPO:
        a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
        tf[t] = np.mean(m2 & fired[:, ia] & fired[:, ib])
    return tf, np.mean(m2 & (((fired[:, 0] & fired[:, 1]) | (fired[:, 2] & fired[:, 3]))))


def ratios(tf, slmask):
    t02 = tf["02"]; t13 = tf["13"]; u01 = tf["01"]; l23 = tf["23"]
    return t02 / max(t13, 1e-9), u01 / max(l23, 1e-9)


# ---- compare thr vs gain asymmetry: same +20%, what Q distortion? ----
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
print("  asymmetry nature comparison (dx=+0.20):")
rows = []
for kind, col in [("thr", "C0"), ("gain", "C1"), ("none", "C2")]:
    dx = 0.20 if kind != "none" else 0.0
    gain, thr = SM.asym_params(kind=kind, dx=dx, base_thr_mip=0.5)
    fired, Q, amp = SM.fire_and_Q(npe, np.random.default_rng(7), gain, thr, geom_H=Hg)
    tf, sl = topo_from_fired(fired)
    r02, r01 = ratios(tf, sl)
    # per-channel trigger rate (fraction of geometric hits that fire)
    rate = [np.mean(fired[Hg[:, i], i]) for i in range(4)]
    print(f"    {kind:5s}: T02/T13={r02:.2f} U01/L23={r01:.2f} "
          f"trig_rate={['%.3f' % r for r in rate]}")
    rows.append((kind, r02, r01, rate))
    # Q spectra: right (Ch0) vs left (Ch1) for fired events
    qR = Q[fired[:, 0], 0]; qL = Q[fired[:, 1], 1]
    axes[0, 0].hist(qR, 40, alpha=0.4, density=True, label=f"{kind} Ch0(R)", color=col)
    axes[0, 0].hist(qL, 40, alpha=0.4, density=True, histtype="step", lw=1.5, color=col)
    axes[0, 1].plot(rate, "o-", color=col, label=kind)
axes[0, 0].set_xlabel("Q (PE, charge proxy)"); axes[0, 0].set_title("Q spectra: Ch0(solid) vs Ch1(step)")
axes[0, 0].legend(fontsize=6)
axes[0, 1].set_xticks(range(4)); axes[0, 1].set_xticklabels(G.ALLCH)
axes[0, 1].set_ylabel("trigger rate (fired/geom-hit)"); axes[0, 1].set_title("per-channel trig rate")
axes[0, 1].legend(fontsize=7)

# ---- key discriminator: threshold asymmetry preserves Q shape; gain shifts it ----
# compute mean Q for left vs right under each
for kind, col, mk in [("thr", "C0", "o"), ("gain", "C1", "s")]:
    dx = 0.20
    gain, thr = SM.asym_params(kind=kind, dx=dx, base_thr_mip=0.5)
    fired, Q, amp = SM.fire_and_Q(npe, np.random.default_rng(8), gain, thr, geom_H=Hg)
    mQ = [Q[Hg[:, i] & (Q[:, i] > 0), i].mean() for i in range(4)]
    axes[1, 0].plot(mQ, mk + "-", color=col, label=f"{kind} dx=0.2")
axes[1, 0].set_xticks(range(4)); axes[1, 0].set_xticklabels(G.ALLCH)
axes[1, 0].set_ylabel("mean Q (fired)"); axes[1, 0].set_title("mean Q per channel: thr(shape same) vs gain(shift)")
axes[1, 0].legend(fontsize=8)
# Q_min distribution for cross-layer (B2/B3 discriminator) under thr asymmetry
gain, thr = SM.asym_params(kind="thr", dx=0.20, base_thr_mip=0.5)
fired, Q, amp = SM.fire_and_Q(npe, np.random.default_rng(9), gain, thr, geom_H=Hg)
M = fired.sum(1); cr = (M == 2) & ~((fired[:, 0] & fired[:, 1]) | (fired[:, 2] & fired[:, 3]))
e2 = np.sort(np.where(fired & (Q > 0), Q, -1), axis=1)[:, ::-1]
qmin = np.where(cr, e2[:, 1], np.nan)
axes[1, 1].hist(qmin[~np.isnan(qmin)], 50, density=True)
axes[1, 1].set_xlabel("Q_min (cross-layer weaker hit)"); axes[1, 1].set_title("Q_min proxy for B2/B3")
plt.tight_layout(); plt.savefig(f"{FIG}/02_small_asymmetry_nature.png", dpi=130); plt.close()

with open(f"{TBL}/v6_asymmetry_nature.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["kind", "T02_T13", "U01_L23", "rate_Ch0", "rate_Ch1", "rate_Ch2", "rate_Ch3"])
    for kind, r02, r01, rate in rows:
        w.writerow([kind, round(r02, 3), round(r01, 3)] + [round(r, 4) for r in rate])
print("STEP 4-5 done.")
