#!/usr/bin/env python3
"""
analyze_sipm_cornercase.py -- corner/edge incidence: 6 mm vs 3 mm SiPM.

Probes whether the 3 mm SiPM signal degrades (vs 6 mm) when muons strike near
slab edges/corners. Compares only C1 (6 mm) and C2 (3 mm) single-SiPM configs.

Outputs: response maps, C2/C1 degradation map, single-SiPM catchment curve
R(d) with exponential attenuation length, region (interior/edge/corner)
breakdown, photon-count percentiles, parameter-free detection-coverage-vs-
threshold curve, and an asymmetry-based position-reconstruction residual.

Usage:
  python3 scripts/analyze_sipm_cornercase.py \
      --c1 build/output_corner_c1.root --c2 build/output_corner_c2.root \
      --out artifacts/corner
"""
import argparse
import os
import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

YIELD = 10000.0  # EJ-200 scintillation yield [photons/MeV]

# 8 SiPM site centres [mm] on the 20x20 cm slab (edge*1000 + pos*100)
# edge: 0=+X,1=-X,2=+Y,3=-Y ; pos 0/1 at +5cm/-5cm along the edge
SITES = [
    (0,     100,   50, "+X +5cm", 0), (100,   100,  -50, "+X -5cm", 0),
    (1000, -100,   50, "-X +5cm", 1), (1100, -100,  -50, "-X -5cm", 1),
    (2000,   50,  100, "+Y +5cm", 2), (2100,  -50,  100, "+Y -5cm", 2),
    (3000,   50, -100, "-Y +5cm", 3), (3100,  -50, -100, "-Y -5cm", 3),
]
SITE_IDS = [s[0] for s in SITES]
SITE_CX = np.array([s[1] for s in SITES], float)
SITE_CY = np.array([s[2] for s in SITES], float)
SITE_EDGE = np.array([s[4] for s in SITES])


def channel_site(ch):
    return (ch // 1000) * 1000 + ((ch % 1000) // 100) * 100


def load(path):
    return uproot.open(path)["Simu"].arrays(
        ["Primary_X", "Primary_Y", "VoxelEdep",
         "SiPMHit_Det_ID", "SiPMHit_Time", "SiPMHit_Wavelength"], library="np")


def per_event(a):
    n = len(a["Primary_X"])
    mx = np.array([float(v) for v in a["Primary_X"]])
    my = np.array([float(v) for v in a["Primary_Y"]])
    edep = np.array([float(np.sum(v)) for v in a["VoxelEdep"]])
    total = np.zeros(n); persite = np.zeros((n, len(SITE_IDS)))
    wl_all, t_all = [], []
    for i in range(n):
        chs = a["SiPMHit_Det_ID"][i]
        total[i] = len(chs)
        for ch in chs:
            j = SITE_IDS.index(channel_site(int(ch)))
            persite[i, j] += 1
        if len(chs):
            wl_all.extend(list(a["SiPMHit_Wavelength"][i]))
            t_all.extend(list(a["SiPMHit_Time"][i]))
    return mx, my, edep, total, persite, np.array(wl_all), np.array(t_all)


def region(x, y):
    # mm thresholds (80 mm = 8 cm)
    ax, ay = abs(x), abs(y)
    if ax >= 80 and ay >= 80:
        return "corner"
    if ax >= 80 or ay >= 80:
        return "edge"
    return "interior"


def exp_fit(dbin, rbin):
    """Fit r = r0*exp(-d/lambda) on positive bins; return (lambda_mm, r0)."""
    m = rbin > 0
    if m.sum() < 3:
        return np.nan, np.nan
    slope, intercept = np.polyfit(dbin[m], np.log(rbin[m]), 1)
    lam = -1.0 / slope if slope != 0 else np.nan
    return lam, np.exp(intercept)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--c1", required=True)
    ap.add_argument("--c2", required=True)
    ap.add_argument("--out", default="artifacts/corner")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    D = {"C1 (6mm)": per_event(load(args.c1)), "C2 (3mm)": per_event(load(args.c2))}
    labels = list(D.keys())

    # ---- per-position mean collected (for maps / coverage) ----
    def pos_means(d):
        mx, my, total = d[0], d[1], d[3]
        px, py, pm = [], [], []
        for (x, y) in sorted(set(zip(np.round(mx, 3), np.round(my, 3)))):
            m = (np.round(mx, 3) == x) & (np.round(my, 3) == y)
            px.append(x); py.append(y); pm.append(total[m].mean())
        return np.array(px), np.array(py), np.array(pm)

    # ===== Fig 1: response maps C1, C2 =====
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, l in zip(axes, labels):
        px, py, pm = pos_means(D[l])
        vmax = max(pos_means(D[k])[2].max() for k in labels)
        sc = ax.scatter(px, py, c=pm, s=60, cmap="viridis", vmin=0, vmax=vmax)
        ax.set_title(f"{l}: mean collected photons"); ax.set_xlabel("x (cm)")
        ax.set_ylabel("y (cm)"); ax.set_aspect("equal")
        plt.colorbar(sc, ax=ax, fraction=0.046)
    plt.tight_layout(); plt.savefig(f"{args.out}/01_response_maps.png", dpi=150); plt.close()

    # ===== Fig 2: C2/C1 degradation ratio map =====
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    p1x, p1y, p1m = pos_means(D[labels[0]])
    p2x, p2y, p2m = pos_means(D[labels[1]])
    # align by position
    ratio = np.full_like(p1m, np.nan)
    for i, (x, y) in enumerate(zip(p1x, p1y)):
        j = np.where((p2x == x) & (p2y == y))[0]
        if len(j) and p1m[i] > 0:
            ratio[i] = p2m[j[0]] / p1m[i]
    sc = ax.scatter(p1x, p1y, c=ratio, s=60, cmap="RdYlGn", vmin=0, vmax=0.6)
    ax.set_title("C2/C1 collected ratio (pure area ~0.25)\nlower red = extra degradation")
    ax.set_xlabel("x (cm)"); ax.set_ylabel("y (cm)"); ax.set_aspect("equal")
    plt.colorbar(sc, ax=ax, fraction=0.046)
    plt.tight_layout(); plt.savefig(f"{args.out}/02_degradation_ratio.png", dpi=150); plt.close()

    # ===== Fig 3: catchment curve R(d) + exp fits =====
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    fits = {}
    for l, color in zip(labels, ["#4C72B0", "#C44E52"]):
        mx, my, total, persite = D[l][0], D[l][1], D[l][3], D[l][4]
        dd, pp = [], []
        for i in range(len(mx)):
            for j in range(len(SITES)):
                d = np.hypot(mx[i] - SITE_CX[j], my[i] - SITE_CY[j])
                dd.append(d); pp.append(persite[i, j])
        dd = np.array(dd); pp = np.array(pp)
        bins = np.arange(0, 260, 10)
        idx = np.clip(np.digitize(dd, bins) - 1, 0, len(bins) - 2)
        dbin, rbin, nbin = [], [], []
        for b in range(len(bins) - 1):
            m = idx == b
            if m.sum():
                dbin.append(0.5 * (bins[b] + bins[b + 1])); rbin.append(pp[m].mean()); nbin.append(m.sum())
        dbin = np.array(dbin); rbin = np.array(rbin)
        lam, r0 = exp_fit(dbin, rbin)
        fits[l] = (lam, r0)
        ax.plot(dbin, rbin, "o-", ms=4, color=color, label=f"{l}  (λ={lam:.0f} mm)" if lam==lam else l)
        if lam == lam:
            ax.plot(dbin, r0 * np.exp(-dbin / lam), "--", color=color, lw=1)
    ax.set_xlabel("distance muon→SiPM centre d (mm)")
    ax.set_ylabel("mean photons at that SiPM")
    ax.set_title("Single-SiPM catchment curve R(d)")
    ax.legend(fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/03_catchment.png", dpi=150); plt.close()

    # ===== Fig 4: region breakdown =====
    fig, ax = plt.subplots(figsize=(6, 4))
    regs = ["interior", "edge", "corner"]
    x = np.arange(len(regs)); w = 0.35
    for k, l in enumerate(labels):
        mx, my, total = D[l][0], D[l][1], D[l][3]
        means = [total[[region(mx[i], my[i]) == r for i in range(len(mx))]].mean() for r in regs]
        ax.bar(x + (k - 0.5) * w, means, w, label=l)
    ax.set_xticks(x); ax.set_xticklabels(regs)
    ax.set_ylabel("mean collected photons / event")
    ax.set_title("Response by slab region"); ax.legend(fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/04_regions.png", dpi=150); plt.close()

    # ===== Fig 5: percentile histogram of per-position means =====
    fig, ax = plt.subplots(figsize=(6, 4))
    for l, color in zip(labels, ["#4C72B0", "#C44E52"]):
        _, _, pm = pos_means(D[l])
        ax.hist(pm, bins=20, histtype="step", color=color, label=l)
        for q, ls in [(5, ":"), (50, "--")]:
            v = np.percentile(pm, q)
            ax.axvline(v, color=color, ls=ls, lw=1, alpha=0.7)
        print(f"  {l}: per-position min={pm.min():.1f}  p5={np.percentile(pm,5):.1f}  "
              f"p50={np.percentile(pm,50):.1f}  max={pm.max():.1f}")
    ax.set_xlabel("mean collected photons (per position)")
    ax.set_ylabel("# positions"); ax.set_title("Per-position photon yield distribution")
    ax.legend(fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/05_percentiles.png", dpi=150); plt.close()

    # ===== Fig 6: coverage vs threshold =====
    fig, ax = plt.subplots(figsize=(6, 4))
    pm_dict = {l: pos_means(D[l])[2] for l in labels}
    Tmax = max(v.max() for v in pm_dict.values())
    Ts = np.linspace(0, Tmax, 80)
    for l, color in zip(labels, ["#4C72B0", "#C44E52"]):
        cov = np.array([(pm_dict[l] >= T).mean() for T in Ts])
        ax.plot(Ts, cov * 100, color=color, label=l)
    ax.set_xlabel("detection threshold T (photons)")
    ax.set_ylabel("positions with signal ≥ T (%)")
    ax.set_title("Parameter-free coverage vs threshold")
    ax.legend(fontsize=9); ax.set_ylim(0, 101)
    plt.tight_layout(); plt.savefig(f"{args.out}/06_coverage.png", dpi=150); plt.close()

    # ===== Fig 7: C1 vs C2 per-position scatter =====
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.scatter(p1m, p2m, s=25, alpha=0.6)
    lim = max(p1m.max(), p2m.max())
    ax.plot([0, lim], [0, lim / 4], "r--", lw=1, label="pure area (×0.25)")
    ax.plot([0, lim], [0, lim], "k:", lw=0.8, label="1:1")
    ax.set_xlabel("C1 photons (6 mm)"); ax.set_ylabel("C2 photons (3 mm)")
    ax.set_title("Per-position C1 vs C2"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/07_c1_vs_c2.png", dpi=150); plt.close()

    # ===== Fig 8: position reconstruction (light-weighted centroid + calib) =====
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    recon_rms = {}
    for ax, axis in zip(axes, ["x", "y"]):
        coord = SITE_CX if axis == "x" else SITE_CY
        for l, color in zip(labels, ["#4C72B0", "#C44E52"]):
            mx, my, persite, total = D[l][0], D[l][1], D[l][4], D[l][3]
            true = (mx if axis == "x" else my) / 10.0  # cm
            m = total > 0  # cannot reconstruct events with no detected light
            # light-weighted centroid of the 8 SiPM positions (cm)
            wsum = persite[m].sum(axis=1)
            cen = (persite[m] * coord).sum(axis=1) / wsum / 10.0
            t = true[m]
            # degree-2 calibration: true = f(centroid)
            coef = np.polyfit(cen, t, 2)
            est = np.polyval(coef, cen)
            resid = t - est
            rms = np.sqrt((resid ** 2).mean())
            recon_rms[(l, axis)] = rms
            ax.scatter(t, est, s=8, alpha=0.3, color=color,
                       label=f"{l} (RMS={rms:.1f} cm, n={m.sum()})")
        ax.plot([-11, 11], [-11, 11], "k--", lw=0.8)
        ax.set_xlabel(f"true {axis} (cm)"); ax.set_ylabel(f"reconstructed {axis} (cm)")
        ax.set_title(f"{axis} reconstruction (centroid, calibrated)"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/08_reconstruction.png", dpi=150); plt.close()

    # ===== Summary =====
    print("\n=========== corner-case experiment summary ===========")
    print(f"{'metric':<40}" + "".join(f"{l:>14}" for l in labels))
    def row(name, vals, fmt="{:.2f}"):
        print(f"{name:<40}" + "".join(f"{fmt.format(v):>14}" for v in vals))
    row("events", [len(D[l][3]) for l in labels], "{:.0f}")
    row("mean photons/event", [D[l][3].mean() for l in labels])
    row("photons/MeV", [D[l][3].sum() / D[l][2].sum() for l in labels], "{:.1f}")
    row("C2/C1 overall ratio", [np.nan, D[labels[1]][3].mean() / D[labels[0]][3].mean()], "{:.3f}")
    row("catchment λ (mm)", [fits[l][0] for l in labels], "{:.0f}")
    # per-region C2/C1
    for r in regs:
        m1 = D[labels[0]][3][[region(D[labels[0]][0][i], D[labels[0]][1][i]) == r for i in range(len(D[labels[0]][3]))]].mean()
        m2 = D[labels[1]][3][[region(D[labels[1]][0][i], D[labels[1]][1][i]) == r for i in range(len(D[labels[1]][3]))]].mean()
        print(f"   {r:<36} C1={m1:6.1f}  C2={m2:6.1f}  C2/C1={m2/m1:.3f}")
    print("   reconstruction RMS (cm): " + ", ".join(f"{a}:{recon_rms[(l,a)]:.1f}" for l in labels for a in ['x','y']))
    print("======================================================")
    print(f"\nFigures -> {args.out}/")


if __name__ == "__main__":
    main()
