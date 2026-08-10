#!/usr/bin/env python3
"""audit2.py -- finish audit: projection-factor, O1 theta check, comparison figures, tables."""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures", "sampling_audit"); TBL = os.path.join(ROOT, "tables")
sys.path.insert(0, HERE); import acceptance_mc as am
slab_min = np.array([-am.SLAB["hx"], -am.SLAB["hy"], -am.SLAB["hz"]])
slab_max = np.array([+am.SLAB["hx"], +am.SLAB["hy"], +am.SLAB["hz"]])
TOPO = ["01", "23", "02", "13", "03", "12"]

def run(HW, ZP, N, n=2.0, L=10.0, seed=11):
    am.HW = HW; am.ZPLAN = ZP; rng = np.random.default_rng(seed)
    r = am.run_one(n, L, N, rng, slab_min, slab_max); M, H, exc, inc = am.patterns(r["hits"])
    return r, M, exc

def sl_frac(M, exc):
    n2 = (M == 2).sum()
    return (exc["01"].sum() + exc["23"].sum()) / n2 if n2 else 0.0, n2

# ---- A. HW scan (z=60) and z scan (HW=250): same-layer ----
HWs = [60, 100, 150, 200, 300, 400]; sl_hw = []
for HW in HWs:
    _, M, exc = run(HW, 60.0, 6_000_000); f, n2 = sl_frac(M, exc); sl_hw.append(f)
Zs = [8, 10, 15, 20, 60]; sl_z = []
for ZP in Zs:
    _, M, exc = run(250.0, float(ZP), 8_000_000); f, n2 = sl_frac(M, exc); sl_z.append(f)
# ---- B. corrected gap scan (z=10, HW=250) ----
hx, hy, hz = am.BK["hx"], am.BK["hy"], am.BK["hz"]
def boxes_gap(gap, L=10.0):
    xR = +gap / 2 + hx; xL = -gap / 2 - hx; zU = +L / 2; zL = -L / 2
    o = {}
    for nm, cx, cz in [("0", xR, zU), ("1", xL, zU), ("2", xR, zL), ("3", xL, zL)]:
        o[nm] = (np.array([cx - hx, -hy, cz - hz]), np.array([cx + hx, +hy, cz + hz]))
    return o
gaps = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 10, 12]; sl_gap_new = []
for g in gaps:
    am.HW = 250.0; am.ZPLAN = 10.0; rng = np.random.default_rng(31)
    P0, d, th, ph = am.gen_muons(2.0, 8_000_000, rng); bxs = boxes_gap(g); hits = {}
    for nm, (a, b) in bxs.items():
        h, p = am.ray_box(P0, d, a, b); hits[nm] = h
    M, H, exc, inc = am.patterns(hits); n2 = (M == 2).sum()
    sl_gap_new.append((exc["01"].sum() + exc["23"].sum()) / n2 if n2 else 0.0)
# OLD gap scan (truncated, z=60 HW=60) for comparison
sl_gap_old = []
for g in gaps:
    am.HW = 60.0; am.ZPLAN = 60.0; rng = np.random.default_rng(31)
    P0, d, th, ph = am.gen_muons(2.0, 5_000_000, rng); bxs = boxes_gap(g); hits = {}
    for nm, (a, b) in bxs.items():
        h, p = am.ray_box(P0, d, a, b); hits[nm] = h
    M, H, exc, inc = am.patterns(hits); n2 = (M == 2).sum()
    sl_gap_old.append((exc["01"].sum() + exc["23"].sum()) / n2 if n2 else 0.0)

# ---- C. projection factor: cos^2 vs cos^3 (reweight) at corrected cfg ----
am.HW = 250.0; am.ZPLAN = 10.0; rng = np.random.default_rng(42); N = 12_000_000
P0, d, th, ph = am.gen_muons(2.0, N, rng)
r = am.run_one(2.0, 10.0, N, rng, slab_min, slab_max); M, H, exc, inc = am.patterns(r["hits"])
w = np.cos(th)  # extra factor for cos^3 (projection)
m2 = (M == 2); slm = (exc["01"] | exc["23"]) & m2
sl_cos2 = slm.sum() / m2.sum() if m2.sum() else 0
sl_cos3 = w[slm].sum() / w[m2].sum() if w[m2].sum() else 0

# ---- D. O1 optical sample theta check ----
mu = json.load(open(os.path.join(ROOT, "..", "data", "muons_stacked.json")))
pz = np.array([e["particles_at_detector"][0]["pz"] for e in mu])
px = np.array([e["particles_at_detector"][0]["px"] for e in mu])
py = np.array([e["particles_at_detector"][0]["py"] for e in mu])
o1theta = np.arctan2(np.hypot(px, py), np.abs(pz)) * 180 / np.pi

# ---- figures ----
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot(HWs, sl_hw, "o-"); ax[0].set_xlabel("plane half-width (cm), z=60"); ax[0].set_ylabel("same-layer frac"); ax[0].set_title("HW scan (z=60): same-layer stays ~0\n(large HW needs huge stats; truncation+stats)")
ax[1].plot(Zs, sl_z, "s-", color="#C44E52"); ax[1].set_xlabel("plane height z (cm), HW=250"); ax[1].set_ylabel("same-layer frac"); ax[1].set_title("Plane-HEIGHT scan: close plane -> same-layer nonzero")
ax[2].plot(gaps, sl_gap_old, "o--", color="#888", label="OLD (z=60,HW=60, truncated)")
ax[2].plot(gaps, sl_gap_new, "s-", color="#C44E52", label="NEW (z=10,HW=250, corrected)")
ax[2].axhline(0.519, color="k", ls=":", label="data=0.52")
ax[2].set_xlabel("same-layer gap (cm)"); ax[2].set_ylabel("same-layer frac of M2"); ax[2].set_title("Gap scan: OLD (artifact) vs NEW (corrected)"); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{FIG}/02_hw_z_gap_scan.png", dpi=130); plt.close()

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(o1theta, bins=40); ax.axvline(55, color="r", ls="--", label="truncation ~55deg (old plane)")
ax.axvline(73, color="k", ls=":", label="same-layer threshold ~73deg")
ax.set_xlabel("theta (deg)"); ax.set_ylabel("O1 tracks"); ax.set_title("O1 optical sample theta (from old truncated generator)"); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/03_O1_theta.png", dpi=130); plt.close()

# ---- tables ----
with open(f"{TBL}/audit_hw_z_scan.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["HW_cm_z60", "sl_z60", "z_cm_HW250", "sl_HW250"])
    for i in range(max(len(HWs), len(Zs))):
        w_.writerow([HWs[i] if i < len(HWs) else "", f"{sl_hw[i]:.4f}" if i < len(sl_hw) else "",
                     Zs[i] if i < len(Zs) else "", f"{sl_z[i]:.4f}" if i < len(sl_z) else ""])
with open(f"{TBL}/audit_gap_old_vs_new.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["gap_cm", "sl_OLD_truncated", "sl_NEW_corrected"])
    for i, g in enumerate(gaps): w_.writerow([g, f"{sl_gap_old[i]:.4f}", f"{sl_gap_new[i]:.4f}"])
with open(f"{TBL}/audit_projection.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["model", "same_layer_frac"]); w_.writerow(["cos^2 (current)", f"{sl_cos2:.4f}"]); w_.writerow(["cos^3 (projection-corrected)", f"{sl_cos3:.4f}"])
print("same-layer: cos^2=%.4f  cos^3=%.4f" % (sl_cos2, sl_cos3))
print("O1 theta: min/mean/max=%.0f/%.0f/%.0f deg; frac>55deg=%.2f; frac>73deg=%.2f" %
      (o1theta.min(), o1theta.mean(), o1theta.max(), (o1theta > 55).mean(), (o1theta > 73).mean()))
print("gap NEW at 10cm:", [f for f, g in zip(sl_gap_new, gaps) if g == 10.0][0])
print("saved figures+tables")
