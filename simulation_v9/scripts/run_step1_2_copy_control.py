#!/usr/bin/env python3
"""run_step1_2_copy_control.py -- positive-control waveform-copy analysis (STEP 1-7).

THE critical test v8 lacked: do real cross-M8 events (two INDEPENDENT plastic
pulses from one muon) also show r~0.99, lag=0? If yes, high correlation is just
"plastic pulses look alike". The SCALED RESIDUAL is the discriminator.
Groups: E=same-dark, S=same-M8, T=cross-M8 (positive control), B=B2/B3.
"""
import os, sys, csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v8.dataio import load_hardware_data as D
from simulation_v9.waveform_copy import copy_metric, pair_from_event

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
df = D.load_event_table(); wf = D.load_all_waveforms(); bs = wf["baseline_subtracted_waveforms"]
try:
    from scipy.stats import mannwhitneyu

    def cliff_delta(x, y):
        x = np.asarray(x); y = np.asarray(y)
        s = sum(np.sum(xi > y) - np.sum(xi < y) for xi in x)
        return s / (len(x) * len(y))
except Exception:
    mannwhitneyu = None


def group_metrics(mask):
    out = []
    for _, row in df[mask].iterrows():
        p = pair_from_event(row, bs)
        if p is None:
            continue
        _, _, maj, mino = p
        out.append(copy_metric(maj, mino))
    return pd.DataFrame(out)


# build masks
topo = df["topology"]; m8 = df["panel_M8"] == 1
cross = topo.isin(["T02", "T13", "T03", "T12"]); same = topo.isin(["U01", "L23"])
bsub = df["B_subclass"]
groups = {
    "E_same_dark": same & ~m8,
    "S_same_M8": same & m8,
    "T_cross_M8": cross & m8,
    "B2": bsub.eq("B2_two_real_looking_weak"),
    "B3": bsub.eq("B3_two_real_strongish_no_M8"),
    "T_cross_nonM8": cross & ~m8,
}
res = {}
print("== STEP 1-2: waveform-copy positive control ==")
for name, mask in groups.items():
    m = group_metrics(mask)
    res[name] = m
    print(f"  {name:16s} n={len(m):3d}  r med={m['r'].median():.3f}  lag med={m['lag'].median():.0f}  "
          f"k med={m['k'].median():.3f}  resid med={m['resid'].median():.3f}  resid_rise={m['resid_rise'].median():.3f}")

# ---- KEY comparison: same-dark vs cross-M8 scaled residual ----
sd = res["E_same_dark"]; cm = res["T_cross_M8"]
print("\n=== scaled residual: same-dark(E) vs cross-M8(T, positive control) ===")
print(f"  same-dark resid: median={sd['resid'].median():.3f} mean={sd['resid'].mean():.3f}")
print(f"  cross-M8 resid:  median={cm['resid'].median():.3f} mean={cm['resid'].mean():.3f}")
if mannwhitneyu:
    u, p = mannwhitneyu(sd["resid"], cm["resid"], alternative="less")
    cd = cliff_delta(sd["resid"].values, cm["resid"].values)
    print(f"  Mann-Whitney (same-dark < cross-M8): U={u:.0f} p={p:.3e}")
    print(f"  Cliff's delta: {cd:.3f}")
    # bootstrap CI on difference of medians
    rng = np.random.default_rng(0); diffs = []
    sda = sd["resid"].values; cma = cm["resid"].values
    for _ in range(2000):
        diffs.append(np.median(rng.choice(sda, len(sda))) - np.median(rng.choice(cma, len(cma))))
    diffs = np.array(diffs)
    print(f"  bootstrap median diff (sd-cm): {np.median(diffs):.3f}  95%CI=[{np.percentile(diffs,2.5):.3f},{np.percentile(diffs,97.5):.3f}]")

# ---- plots ----
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
cols = ["r", "lag", "k", "resid", "resid_rise", "resid_tail"]
for ax, col in zip(axes.ravel(), cols):
    data = [res[g][col].dropna() for g in ["E_same_dark", "S_same_M8", "T_cross_M8", "B2", "B3"]]
    labels = ["same-dark", "same-M8", "cross-M8", "B2", "B3"]
    parts = ax.boxplot(data, labels=labels, showfliers=False)
    ax.set_title(col); plt.setp(ax.get_xticklabels(), rotation=15, fontsize=7)
    if col in ("r", "k", "resid", "resid_rise", "resid_tail"):
        ax.set_ylim(0, max(np.percentile(np.concatenate([d.values for d in data if len(d)]), 99) * 1.1, 0.05))
plt.suptitle("waveform-copy metric by group (cross-M8 = positive control)")
plt.tight_layout(); plt.savefig(f"{FIG}/01_copy_control_metrics.png", dpi=130); plt.close()

# residual histogram overlay
fig, ax = plt.subplots(figsize=(7, 4.5))
for g, col, lbl in [("E_same_dark", "C0", "same-dark"), ("T_cross_M8", "C2", "cross-M8"),
                    ("S_same_M8", "C1", "same-M8"), ("B3", "C3", "B3")]:
    ax.hist(res[g]["resid"], 30, range=(0, 1.5), density=True, alpha=0.5, color=col, label=lbl)
ax.set_xlabel("scaled residual RMS[V_b - k*V_a]/RMS[V_b]"); ax.set_title("KEY: scaled residual (low=exact copy)")
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/02_scaled_residual_hist.png", dpi=130); plt.close()

with open(f"{TBL}/v9_copy_control.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["group", "n", "r_med", "lag_med", "k_med", "resid_med", "resid_rise_med"])
    for name, m in res.items():
        w.writerow([name, len(m), round(m["r"].median(), 4), int(m["lag"].median()),
                    round(m["k"].median(), 4), round(m["resid"].median(), 4), round(m["resid_rise"].median(), 4)])
print("\nSTEP 1-2 done.")
