#!/usr/bin/env python3
"""run_step6_gain_threshold.py -- real-Q gain vs threshold discrimination (STEP 6).

Resolves the v6/v7 degeneracy using real Ch0-Ch3 nonclipped Q spectra.
Threshold asymmetry: cuts low-Q tail, preserves high-Q peak/shape.
Gain asymmetry: scales the whole Q distribution (incl. clipping fraction).
"""
import os, sys, csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v8.dataio import load_hardware_data as D

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
df = D.load_event_table()


def nonclip_q(ch):
    m = (df[f"hit{ch}"] == 1) & (df[f"ch{ch}_clipping"] == 0)
    return df.loc[m, f"ch{ch}_integral"].values

def clip_frac(ch):
    m = df[f"hit{ch}"] == 1
    return float(df.loc[m, f"ch{ch}_clipping"].mean())

qR = np.concatenate([nonclip_q(0), nonclip_q(2)])   # right column
qL = np.concatenate([nonclip_q(1), nonclip_q(3)])   # left column
print(f"right n={len(qR)} median={np.median(qR):.0f} mean={qR.mean():.1f}")
print(f"left  n={len(qL)} median={np.median(qL):.0f} mean={qL.mean():.1f}")
clipR = np.mean([clip_frac(0), clip_frac(2)]); clipL = np.mean([clip_frac(1), clip_frac(3)])
print(f"clip frac: right={clipR:.3f} left={clipL:.3f}")

# ---- discriminator 1: normalized Q shape overlay ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for q, col, lbl in [(qR, "C0", "right"), (qL, "C1", "left")]:
    axes[0].hist(q, 40, range=(0, 1500), density=True, alpha=0.5, color=col, label=f"{lbl} (med {np.median(q):.0f})")
axes[0].set_xlabel("Q (nonclipped, CSV unit ns)"); axes[0].set_title("raw Q shapes")
axes[0].legend(fontsize=8)
# normalized to same median (test gain: if gain, shapes overlap after scale)
qRn = qR / np.median(qR); qLn = qL / np.median(qL)
axes[1].hist(qRn, 40, range=(0, 5), density=True, alpha=0.5, color="C0", label="right/med")
axes[1].hist(qLn, 40, range=(0, 5), density=True, alpha=0.5, color="C1", label="left/med")
axes[1].set_xlabel("Q / channel-median"); axes[1].set_title("shape (overlap=>gain; diff low tail=>threshold)")
axes[1].legend(fontsize=8)
# low-Q tail: fraction below 20th pct of combined
qall = np.concatenate([qR, qL]); p20 = np.percentile(qall, 20); p50 = np.percentile(qall, 50)
fr_lo = np.mean(qR < p20); fl_lo = np.mean(qL < p20)
axes[2].bar(["right", "left"], [fr_lo, fl_lo], color=["C0", "C1"])
axes[2].set_ylabel(f"frac Q<{p20:.0f}"); axes[2].set_title("low-Q tail fraction")
plt.tight_layout(); plt.savefig(f"{FIG}/01_gain_threshold_Q.png", dpi=130); plt.close()

# ---- likelihood: threshold-only vs gain-only vs both ----
# model: underlying Q ~ empirical (pooled, smoothed). threshold cuts Q<thr; gain scales Q by g.
from scipy.stats import gaussian_kde
kde = gaussian_kde(qall)
def nll_threshold(thr_L, qL_data, qR_ref):
    # left = right distribution with extra threshold cut at thr_L (in left units)
    # P(Q|left) propto P(Q|right) for Q>thr_L ; normalize
    grid = np.linspace(max(thr_L, 1), 2000, 400)
    p = kde(grid); p[grid < thr_L] = 0; p /= p.sum() / (grid[1]-grid[0])
    # evaluate data likelihood via interpolation
    pg = np.interp(qL_data, grid, p)
    pg = np.clip(pg, 1e-12, None)
    return -np.sum(np.log(pg))

def nll_gain(g, qL_data):
    qs = qL_data / g  # unscale left to compare to pooled
    pg = np.clip(kde(qs), 1e-12, None)
    return -np.sum(np.log(pg))

# scan
print("\n=== likelihood scan ===")
thr_grid = np.linspace(0, 200, 41); g_grid = np.linspace(0.7, 1.0, 31)
nll_t = [nll_threshold(t, qL, qR) for t in thr_grid]
nll_g = [nll_gain(g, qL) for g in g_grid]
bt = thr_grid[np.argmin(nll_t)]; bg = g_grid[np.argmin(nll_g)]
print(f"  threshold-only: best thr_L={bt:.0f}  nll={min(nll_t):.1f}")
print(f"  gain-only:      best g_L={bg:.3f}  nll={min(nll_g):.1f}")
# combined
best = (1e30, 0, 0)
for t in thr_grid[::2]:
    for g in g_grid[::2]:
        qs = qL / g
        grid = np.linspace(max(t, 1), 2000, 300); p = kde(grid); p[grid < t] = 0
        if p.sum() == 0: continue
        p /= p.sum() / (grid[1]-grid[0])
        pg = np.clip(np.interp(qs, grid, p), 1e-12, None)
        v = -np.sum(np.log(pg))
        if v < best[0]: best = (v, t, g)
print(f"  gain+threshold: best thr={best[1]:.0f} g={best[2]:.3f} nll={best[0]:.1f}")
# AIC (1 param each except combined 2)
print(f"\n  AIC: thr-only={min(nll_t)*2+2:.0f}  gain-only={min(nll_g)*2+2:.0f}  both={best[0]*2+4:.0f}")
d_thr_gain = min(nll_t) - min(nll_g)
print(f"  Δnll(thr-gain) = {d_thr_gain:.1f}  ({'GAIN favored' if d_thr_gain>0 else 'THRESHOLD favored'})")

with open(f"{TBL}/v8_gain_threshold.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["test", "param", "nll", "AIC"])
    w.writerow(["threshold_only", round(bt,1), round(min(nll_t),1), round(min(nll_t)*2+2,0)])
    w.writerow(["gain_only", round(bg,4), round(min(nll_g),1), round(min(nll_g)*2+2,0)])
    w.writerow(["gain_plus_threshold", f"thr={best[1]:.0f},g={best[2]:.3f}", round(best[0],1), round(best[0]*2+4,0)])
    w.writerow(["clip_frac_right", round(clipR,4), "", ""])
    w.writerow(["clip_frac_left", round(clipL,4), "", ""])
    w.writerow(["left_right_mean_ratio", round(qL.mean()/qR.mean(),4), "", ""])
print("\nSTEP 6 done.")
