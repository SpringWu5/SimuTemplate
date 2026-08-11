#!/usr/bin/env python3
"""run_step3_coupling.py -- 4x4 electronics coupling matrix (STEP 3-4).

Extract k_ij = Q_j/Q_i from events where channel i is strongly dominant and j is
a minor hit. If coupling is only between same-layer neighbours (0<->1, 2<->3)
and cross-layer is ~0, that points to PCB/cable/ADC neighbour coupling.
Direction asymmetry (0->1 vs 1->0) points to routing/impedance.
"""
import os, sys, csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v8.dataio import load_hardware_data as D
from simulation_v9.waveform_copy import copy_metric

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
df = D.load_event_table(); wf = D.load_all_waveforms(); bs = wf["baseline_subtracted_waveforms"]
SAME_NEIGH = {0: 1, 1: 0, 2: 3, 3: 2}

# k_ij matrix: from events with ch_i dominant, ch_j minor
K = np.full((4, 4), np.nan)  # median
Kstd = np.full((4, 4), np.nan)
Kn = np.zeros((4, 4), int)
Ksamples = [[[] for _ in range(4)] for _ in range(4)]
for _, row in df.iterrows():
    hits = {ch: row[f"ch{ch}_integral"] for ch in range(4) if row[f"hit{ch}"] == 1}
    if len(hits) < 2:
        continue
    # dominant = max Q channel
    dom = max(hits, key=hits.get)
    for j, qj in hits.items():
        if j == dom:
            continue
        qi = hits[dom]
        if qi <= 0:
            continue
        k = qj / qi
        if k > 1.0:  # not actually minor; skip
            continue
        Ksamples[dom][j].append(k)

print("== STEP 3: 4x4 coupling matrix (median k_ij = Q_minor/Q_major) ==")
print("  rows=major ch, cols=minor ch")
hdr = "major\\minor " + " ".join(f"Ch{j:>4}" for j in range(4))
print("  " + hdr)
for i in range(4):
    rowvals = []
    for j in range(4):
        arr = np.array(Ksamples[i][j])
        if len(arr) >= 3:
            K[i, j] = np.median(arr); Kstd[i, j] = arr.std(); Kn[i, j] = len(arr)
            rowvals.append(f"{K[i,j]:.2f}({Kn[i,j]:>2})")
        else:
            rowvals.append(f"  -   ")
    print(f"  Ch{i}        " + " ".join(f"{v:>8}" for v in rowvals))

# same-layer neighbour vs cross-layer coupling
sl_k = []; xl_k = []
for i in range(4):
    for j in range(4):
        if i == j: continue
        arr = Ksamples[i][j]
        if len(arr) < 3: continue
        if j == SAME_NEIGH[i]:
            sl_k += arr
        else:
            xl_k += arr
sl_k = np.array(sl_k); xl_k = np.array(xl_k)
print(f"\n  same-layer neighbour coupling (0-1,2-3): n={len(sl_k)} median k={np.median(sl_k):.3f}")
print(f"  cross-layer coupling:                   n={len(xl_k)} median k={np.median(xl_k):.3f}")
print(f"  => {'same-layer dominates (PCB/neighbour electronics)' if np.median(sl_k)>np.median(xl_k) else 'cross-layer also strong (common-mode?)'}")

# direction asymmetry
print("\n  direction asymmetry:")
for a, b in [(0, 1), (1, 0), (2, 3), (3, 2)]:
    arr = np.array(Ksamples[a][b])
    if len(arr) >= 3:
        print(f"    Ch{a}->Ch{b}: median k={np.median(arr):.3f} n={len(arr)}")

# plot heatmap
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
im = axes[0].imshow(K, cmap="viridis", vmin=0, vmax=0.8)
for i in range(4):
    for j in range(4):
        if not np.isnan(K[i, j]):
            axes[0].text(j, i, f"{K[i,j]:.2f}\n({Kn[i,j]})", ha="center", va="center", fontsize=8, color="w")
axes[0].set_xticks(range(4)); axes[0].set_yticks(range(4))
axes[0].set_xticklabels([f"Ch{j}" for j in range(4)]); axes[0].set_yticklabels([f"Ch{i}" for i in range(4)])
axes[0].set_xlabel("minor channel"); axes[0].set_ylabel("major channel")
axes[0].set_title("coupling k_ij = Q_minor/Q_major")
plt.colorbar(im, ax=axes[0])
axes[1].hist(sl_k, 40, range=(0, 1), alpha=0.6, label=f"same-layer neigh (med {np.median(sl_k):.2f})", density=True)
axes[1].hist(xl_k, 40, range=(0, 1), alpha=0.6, label=f"cross-layer (med {np.median(xl_k):.2f})", density=True)
axes[1].set_xlabel("k = Q_minor/Q_major"); axes[1].set_title("neighbour vs cross-layer coupling")
axes[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/03_coupling_matrix.png", dpi=130); plt.close()

with open(f"{TBL}/v9_coupling_matrix.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["major_ch", "minor_ch", "n", "k_median", "k_std", "relation"])
    for i in range(4):
        for j in range(4):
            arr = np.array(Ksamples[i][j])
            if len(arr) >= 3:
                rel = "same-layer-neigh" if j == SAME_NEIGH[i] else "cross-layer"
                w.writerow([i, j, len(arr), round(np.median(arr), 3), round(arr.std(), 3), rel])
    w.writerow(["same_layer_neigh_median", "", len(sl_k), round(np.median(sl_k), 3), "", ""])
    w.writerow(["cross_layer_median", "", len(xl_k), round(np.median(xl_k), 3), "", ""])
print("STEP 3 done.")
