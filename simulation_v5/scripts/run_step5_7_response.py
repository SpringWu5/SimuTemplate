#!/usr/bin/env python3
"""run_step5_7_response.py -- small detector forward model + asymmetry (STEP 5-7).

Efficient: precompute per-channel Edep + N_PE once, then all threshold/asymmetry
scans are vectorised comparisons (no re-drawing Poisson).
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, response as R, geometry as G

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
DATA_TF = {"01": 0.306, "23": 0.224, "02": 0.204, "13": 0.098, "03": 0.098, "12": 0.071}
DATA_T02_T13 = 52 / 25.0; DATA_U01_L23 = 78 / 57.0
Y = 12.0

print("== STEP 5-7: small detector forward model + channel asymmetry ==")
iss = GEN.sample_single(8_000_000, n=2.0, rng=np.random.default_rng(101))
s = GEN.resample_triggered(iss, 800_000, np.random.default_rng(102), Mmin=1)
Hg = s["H"]; Ng = Hg.shape[0]

# ---- precompute Edep + N_PE once per channel ----
rng = np.random.default_rng(7)
edep = np.zeros((Ng, 4)); npe = np.zeros((Ng, 4))
for i, ch in enumerate(G.ALLCH):
    path = s["paths"][ch]
    e = np.where(path > 0, R.landau_edep(np.where(path > 0, path, 1e-3), rng), 0.0)
    edep[:, i] = e
    npe[:, i] = np.where(path > 0, rng.poisson(Y * e), 0.0)

def topo_from_thr(thr_pe, noise_pe=2.0, gain=None, seed=0):
    """Fast: draw noise, apply per-channel threshold, return topology dict."""
    r = np.random.default_rng(seed)
    g = np.ones(4) if gain is None else gain
    amp = g * npe + r.normal(0, noise_pe, (Ng, 4))
    fired = (amp > thr_pe) & Hg
    M = fired.sum(axis=1); m2 = M == 2; ge2 = M >= 2
    W2 = m2.sum(); Wge2 = ge2.sum()
    tf = {}
    for t in G.TOPO:
        a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
        tf[t] = float(np.sum(m2 & fired[:, ia] & fired[:, ib]) / W2) if W2 else 0.0
    mf = {f"M{k}": float(np.sum(M == k) / Wge2) if Wge2 else 0.0 for k in (2, 3, 4)}
    return dict(tf=tf, mf=mf, same_layer=tf["01"] + tf["23"], n2=W2)

# ---- STEP 5: path-length + Edep distributions ----
sl = ((Hg[:, 0] & Hg[:, 1]) | (Hg[:, 2] & Hg[:, 3])) & (s["M"] == 2)
cr = ((Hg[:, 0] & Hg[:, 2]) | (Hg[:, 1] & Hg[:, 3]) | (Hg[:, 0] & Hg[:, 3]) | (Hg[:, 1] & Hg[:, 2])) & (s["M"] == 2)
def both_e(mask):
    pp = [edep[mask & Hg[:, i], i] for i in range(4)]
    return np.concatenate(pp)
e_sl = both_e(sl); e_cr = both_e(cr)
print(f"  Edep same-layer mean={e_sl.mean():.2f}MeV  cross-layer mean={e_cr.mean():.2f}MeV")

# response validation figure
edep_grid = np.linspace(0.1, 15, 60)
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for thr_mip, col in [(0.05, "g"), (0.1, "b"), (0.2, "orange"), (0.3, "r"), (0.5, "k")]:
    thr_pe = thr_mip * R.E_MIP_VERT * Y
    eff = [np.mean((rng.poisson(Y * e, 20000) + rng.normal(0, 2, 20000)) > thr_pe) for e in edep_grid]
    axes[0].plot(edep_grid, eff, col, label=f"thr={thr_mip:.2f} MIP")
axes[0].set_xlabel("Edep (MeV)"); axes[0].set_ylabel("trigger eff"); axes[0].legend(fontsize=7)
axes[0].set_title("STEP5: trigger eff vs Edep")
axes[1].plot(edep_grid, Y * edep_grid, "k"); axes[1].set_xlabel("Edep"); axes[1].set_ylabel("<N_PE>")
axes[1].set_title(f"Edep->PE (Y={Y}/MeV)")
axes[2].hist(e_sl, 40, alpha=0.6, label="same-layer", density=True)
axes[2].hist(e_cr, 40, alpha=0.6, label="cross-layer", density=True)
axes[2].set_xlabel("Edep (MeV)"); axes[2].set_title("Landau Edep"); axes[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{FIG}/12_response_model.png", dpi=130); plt.close()

# ---- STEP 7: topology vs uniform threshold; same-layer vs threshold ----
thr_scan = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7]
sl_vs_thr = []; t02t13_vs_thr = []; topo_vs_thr = {t: [] for t in G.TOPO}
for k, tm in enumerate(thr_scan):
    tp = topo_from_thr(np.full(4, tm * R.E_MIP_VERT * Y), seed=k * 13)
    for t in G.TOPO: topo_vs_thr[t].append(tp["tf"][t])
    sl_vs_thr.append(tp["same_layer"])
    t02t13_vs_thr.append(tp["tf"]["02"] / max(tp["tf"]["13"], 1e-6))
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(thr_scan, sl_vs_thr, "o-"); axes[0].axhline(0.53, color="k", ls="--", label="data 0.53")
axes[0].set_xlabel("threshold (MIP)"); axes[0].set_ylabel("same-layer"); axes[0].legend(fontsize=8)
axes[0].set_title("STEP7: same-layer vs threshold")
for t in G.TOPO: axes[1].plot(thr_scan, topo_vs_thr[t], "o-", ms=3, label=t)
axes[1].set_xlabel("threshold (MIP)"); axes[1].set_ylabel("P(topo|M2)"); axes[1].legend(fontsize=7)
axes[1].set_title("topology vs threshold")
axes[2].plot(thr_scan, t02t13_vs_thr, "o-"); axes[2].axhline(DATA_T02_T13, color="k", ls="--")
axes[2].set_xlabel("threshold (MIP)"); axes[2].set_ylabel("T02/T13")
axes[2].set_title("T02/T13 (identical channels)")
plt.tight_layout(); plt.savefig(f"{FIG}/13_topology_vs_threshold.png", dpi=130); plt.close()
with open(f"{TBL}/v5_samelayer_vs_threshold.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["thr_mip", "same_layer", "T02_T13"] + G.TOPO)
    for i, th in enumerate(thr_scan):
        w_.writerow([th, round(sl_vs_thr[i], 4), round(t02t13_vs_thr[i], 3)] + [round(topo_vs_thr[t][i], 4) for t in G.TOPO])

# ---- STEP 6: channel asymmetry ----
print("  STEP 6: channel asymmetry ...")
base_arr = [0.2, 0.35, 0.5, 0.7]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
dx_arr = np.linspace(-0.6, 0.6, 25)
for base in base_arr:
    r02 = []; 
    for k, dx in enumerate(dx_arr):
        thr = np.array([base, base * (1 + dx), base, base * (1 + dx)]) * R.E_MIP_VERT * Y
        tp = topo_from_thr(thr, seed=int(base * 100) + k)
        r02.append(tp["tf"]["02"] / max(tp["tf"]["13"], 1e-6))
    axes[0].plot(dx_arr, r02, "o-", ms=3, label=f"base={base}")
axes[0].axhline(DATA_T02_T13, color="k", ls="--", label=f"data {DATA_T02_T13:.2f}")
axes[0].set_xlabel("dx (left-col thr factor-1)"); axes[0].set_ylabel("T02/T13")
axes[0].set_title("T02/T13 vs left-column asymmetry"); axes[0].legend(fontsize=7)
dz_arr = np.linspace(-0.6, 0.6, 25)
for base in base_arr:
    r01 = []
    for k, dz in enumerate(dz_arr):
        thr = np.array([base, base, base * (1 + dz), base * (1 + dz)]) * R.E_MIP_VERT * Y
        tp = topo_from_thr(thr, seed=int(base * 100) + k + 500)
        r01.append(tp["tf"]["01"] / max(tp["tf"]["23"], 1e-6))
    axes[1].plot(dz_arr, r01, "o-", ms=3, label=f"base={base}")
axes[1].axhline(DATA_U01_L23, color="k", ls="--", label=f"data {DATA_U01_L23:.2f}")
axes[1].set_xlabel("dz (lower-layer thr factor-1)"); axes[1].set_ylabel("U01/L23")
axes[1].set_title("U01/L23 vs lower-layer asymmetry"); axes[1].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{FIG}/14_channel_asymmetry_scan.png", dpi=130); plt.close()

# 2D joint at base=0.5
base = 0.5; DX = np.linspace(-0.6, 0.6, 19); DZ = np.linspace(-0.6, 0.6, 19)
rm = np.zeros((len(DX), len(DZ), 2))
for ix, dx in enumerate(DX):
    for iz, dz in enumerate(DZ):
        thr = np.array([base, base * (1 + dx), base * (1 + dz), base * (1 + dx + dz)]) * R.E_MIP_VERT * Y
        tp = topo_from_thr(thr, seed=ix * 19 + iz)
        rm[ix, iz, 0] = tp["tf"]["02"] / max(tp["tf"]["13"], 1e-6)
        rm[ix, iz, 1] = tp["tf"]["01"] / max(tp["tf"]["23"], 1e-6)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for k, (name, tgt) in enumerate([("T02/T13", DATA_T02_T13), ("U01/L23", DATA_U01_L23)]):
    im = axes[k].imshow(rm[..., k], origin="lower", extent=[DZ[0], DZ[-1], DX[0], DX[-1]], aspect="auto", cmap="RdBu_r")
    try:
        cs = axes[k].contour(rm[..., k], levels=[tgt], extent=[DZ[0], DZ[-1], DX[0], DX[-1]], colors="w", linewidths=2)
    except Exception:
        pass
    axes[k].set_xlabel("dz"); axes[k].set_ylabel("dx"); axes[k].set_title(f"{name} base={base}")
    plt.colorbar(im, ax=axes[k])
plt.tight_layout(); plt.savefig(f"{FIG}/14b_asymmetry_2d.png", dpi=130); plt.close()
# joint best
best = (1e9, 0, 0)
for ix in range(len(DX)):
    for iz in range(len(DZ)):
        chi = ((rm[ix, iz, 0] - DATA_T02_T13) / 0.3) ** 2 + ((rm[ix, iz, 1] - DATA_U01_L23) / 0.2) ** 2
        if chi < best[0]: best = (chi, DX[ix], DZ[iz])
_, bdx, bdz = best
thr_best = np.array([base, base * (1 + bdx), base * (1 + bdz), base * (1 + bdx + bdz)]) * R.E_MIP_VERT * Y
tp_best = topo_from_thr(thr_best, seed=777)
print(f"  joint best (dx,dz)=({bdx:+.2f},{bdz:+.2f}) base={base} MIP")
print(f"  -> T02/T13={tp_best['tf']['02']/max(tp_best['tf']['13'],1e-6):.2f} "
      f"U01/L23={tp_best['tf']['01']/max(tp_best['tf']['23'],1e-6):.2f}")
print("  topology:", {t: round(tp_best["tf"][t], 3) for t in G.TOPO})
print("  data    :", DATA_TF)
with open(f"{TBL}/v5_channel_asymmetry.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["param", "value"])
    w_.writerow(["base_thr_mip", base]); w_.writerow(["dx_leftcol", round(float(bdx), 3)])
    w_.writerow(["dz_lowerlayer", round(float(bdz), 3)])
    w_.writerow(["T02_T13_MC", round(tp_best['tf']['02']/max(tp_best['tf']['13'],1e-6), 3)])
    w_.writerow(["U01_L23_MC", round(tp_best['tf']['01']/max(tp_best['tf']['23'],1e-6), 3)])
    for t in G.TOPO:
        w_.writerow([f"tf_{t}_MC", round(tp_best["tf"][t], 4)]); w_.writerow([f"tf_{t}_data", DATA_TF[t]])
print("STEP 5-7 done.")
