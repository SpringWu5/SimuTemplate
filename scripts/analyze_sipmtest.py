#!/usr/bin/env python3
"""
analyze_sipmtest.py -- SiPM-sizing experiment analysis.

Compares three "unit SiPM" readout configurations on a single scintillator slab:
  C1: single 6x6 mm active area (8 sites)
  C2: single 3x3 mm active area (8 sites)
  C3: 2x2 array of 3x3 mm active areas (8 sites x 4 cells = 32 channels)

Reads the SimuTemplate output ROOT files (no PDE applied -- pure geometric
collection) and produces figures + a summary table.

Usage:
  python3 scripts/analyze_sipmtest.py \
      --c1 build/output_sipmtest_c1.root \
      --c2 build/output_sipmtest_c2.root \
      --c3 build/output_sipmtest_c3.root \
      --out artifacts/sipmtest
"""
import argparse
import os
import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

YIELD = 10000.0  # EJ-200 scintillation yield [photons/MeV] (matches Material "Scint")

# Slab half-size and SiPM site positions [mm] (slab 200x200x20, sites at +/-50 mm)
SLAB_HALF = 100.0
SITES = []           # (site_id=edge*1000+pos*100, x_mm, y_mm, label)
for edge, (ex, ey, name) in enumerate([("+X", "+X", "+X"), ("-X", "-X", "-X"),
                                       ("+Y", "+Y", "+Y"), ("-Y", "-Y", "-Y")]):
    pass
_EDGE_GEOM = {0: ("+X", (100, None)), 1: ("-X", (-100, None)),
              2: ("+Y", (None, 100)), 3: ("-Y", (None, -100))}
for edge in range(4):
    ename, (fx, fy) = _EDGE_GEOM[edge]
    for pos in (0, 1):
        along = 50 if pos == 0 else -50
        if fx is not None:
            x, y = fx, along
        else:
            x, y = along, fy
        SITES.append((edge * 1000 + pos * 100, x, y, f"{ename}{'+5cm' if pos==0 else '-5cm'}"))
SITE_IDS = [s[0] for s in SITES]


def channel_site(ch):
    return (ch // 1000) * 1000 + ((ch % 1000) // 100) * 100


def load(path):
    t = uproot.open(path)["Simu"]
    a = t.arrays(["Primary_X", "Primary_Y", "VoxelEdep",
                  "SiPMHit_Det_ID", "SiPMHit_Time", "SiPMHit_Wavelength"],
                 library="np")
    return a


def per_event(a):
    """Return arrays: mx, my, edep, total_hits, per_site_counts(8), wl[], t[]."""
    n = len(a["Primary_X"])
    mx = np.array([float(v) for v in a["Primary_X"]])
    my = np.array([float(v) for v in a["Primary_Y"]])
    edep = np.array([float(np.sum(v)) for v in a["VoxelEdep"]])
    total = np.zeros(n)
    persite = np.zeros((n, len(SITE_IDS)))
    all_wl, all_t = [], []
    for i in range(n):
        chs = a["SiPMHit_Det_ID"][i]
        total[i] = len(chs)
        for ch in chs:
            s = channel_site(int(ch))
            j = SITE_IDS.index(s)
            persite[i, j] += 1
        if len(chs):
            all_wl.extend(list(a["SiPMHit_Wavelength"][i]))
            all_t.extend(list(a["SiPMHit_Time"][i]))
    return mx, my, edep, total, persite, np.array(all_wl), np.array(all_t)


def nearest_site_dist(x, y):
    d = np.array([np.hypot(x - sx, y - sy) for (_, sx, sy, _) in SITES])
    return d.min(axis=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--c1", required=True)
    ap.add_argument("--c2", required=True)
    ap.add_argument("--c3", required=True)
    ap.add_argument("--out", default="artifacts/sipmtest")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    data = {}
    for label, path in [("C1 (6mm)", args.c1), ("C2 (3mm)", args.c2),
                        ("C3 (2x2 array)", args.c3)]:
        a = load(path)
        data[label] = per_event(a)

    labels = list(data.keys())
    site_labels = [s[3] for s in SITES]

    # ---------- Figure 1: mean total collected photons / event ----------
    fig, ax = plt.subplots(figsize=(5, 4))
    means = [data[l][3].mean() for l in labels]
    stds = [data[l][3].std() for l in labels]
    ax.bar(labels, means, yerr=stds, capsize=5, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylabel("Collected photons / event")
    ax.set_title("Light yield (geometric, no PDE)")
    for i, m in enumerate(means):
        ax.text(i, m + stds[i], f"{m:.0f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/01_light_yield.png", dpi=150); plt.close()

    # ---------- Figure 2: collection efficiency ----------
    fig, ax = plt.subplots(figsize=(5, 4))
    eff = []
    for l in labels:
        mx, my, edep, total = data[l][:4]
        produced = np.where(edep > 0, edep * YIELD, np.nan)
        e = total / produced
        eff.append(np.nanmean(e))
    ax.bar(labels, np.array(eff) * 100, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylabel("Collection efficiency (%)")
    ax.set_title("Photons reaching active area / produced")
    for i, e in enumerate(eff):
        ax.text(i, e * 100, f"{e*100:.2f}%", ha="center", va="bottom", fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/02_efficiency.png", dpi=150); plt.close()

    # ---------- Figure 3: per-site (8 SiPMs) light distribution + symmetry ----------
    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(SITE_IDS))
    w = 0.27
    for k, l in enumerate(labels):
        site_means = data[l][4].mean(axis=0)
        ax.bar(x + (k - 1) * w, site_means, w, label=l)
    ax.set_xticks(x); ax.set_xticklabels(site_labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Mean photons / event / site")
    ax.set_title("Per-SiPM response (8 sites) -- symmetry indicator")
    ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/03_per_site.png", dpi=150); plt.close()

    # ---------- Figure 4: uniformity heatmaps ----------
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True, sharey=True)
    gridx = np.unique(np.round(data[labels[0]][0], 3))
    gridy = np.unique(np.round(data[labels[0]][1], 3))
    for ax, l in zip(axes, labels):
        mx, my, total = data[l][0], data[l][1], data[l][3]
        Z = np.full((len(gridy), len(gridx)), np.nan)
        for ix, gx in enumerate(gridx):
            for iy, gy in enumerate(gridy):
                m = (mx == gx) & (my == gy)
                if m.any():
                    Z[iy, ix] = total[m].mean()
        im = ax.imshow(Z, origin="lower", extent=[gridx.min(), gridx.max(),
                                                  gridy.min(), gridy.max()], aspect="auto")
        ax.set_title(l); ax.set_xlabel("muon x (mm)"); ax.set_ylabel("muon y (mm)")
        plt.colorbar(im, ax=ax, fraction=0.046, label="photons")
    plt.tight_layout(); plt.savefig(f"{args.out}/04_uniformity.png", dpi=150); plt.close()

    # ---------- Figure 5: attenuation vs nearest-SiPM distance ----------
    fig, ax = plt.subplots(figsize=(6, 4))
    for l in labels:
        mx, my, total = data[l][0], data[l][1], data[l][3]
        d = nearest_site_dist(mx, my)
        order = np.argsort(d)
        ax.plot(d[order], total[order], ".", ms=3, alpha=0.4, label=l)
    ax.set_xlabel("Muon distance to nearest SiPM (mm)")
    ax.set_ylabel("Collected photons / event")
    ax.set_title("Attenuation with distance to readout")
    ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/05_attenuation.png", dpi=150); plt.close()

    # ---------- Figure 6: wavelength spectrum at SiPM ----------
    fig, ax = plt.subplots(figsize=(6, 4))
    for l in labels:
        wl = data[l][5]
        if len(wl):
            ax.hist(wl, bins=60, range=(300, 700), histtype="step", density=True, label=l)
    ax.set_xlabel("Wavelength at SiPM (nm)"); ax.set_ylabel("Normalised counts")
    ax.set_title("Photon wavelength spectrum at SiPM"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/06_wavelength.png", dpi=150); plt.close()

    # ---------- Figure 7: arrival-time spectrum ----------
    fig, ax = plt.subplots(figsize=(6, 4))
    for l in labels:
        tt = data[l][6]
        if len(tt):
            ax.hist(tt, bins=80, range=(0, 40), histtype="step", density=True, label=l)
    ax.set_xlabel("Arrival time (ns)"); ax.set_ylabel("Normalised counts")
    ax.set_title("Photon arrival-time spectrum at SiPM"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/07_time.png", dpi=150); plt.close()

    # ---------- Figure 8 (C3): intra-array sub-cell split ----------
    c3 = data["C3 (2x2 array)"]
    # group hits by cell index (0..3) across all sites
    fig, ax = plt.subplots(figsize=(5, 4))
    # recompute cell counts from raw
    cell_counts = np.zeros(4)
    a3 = uproot.open(args.c3)["Simu"].arrays(["SiPMHit_Det_ID"], library="np")
    for arr in a3["SiPMHit_Det_ID"]:
        for ch in arr:
            cell_counts[int(ch) % 100] += 1
    ax.bar([f"cell {i}" for i in range(4)], cell_counts, color="#C44E52")
    ax.set_ylabel("Total photons"); ax.set_title("C3: intra-array (4 sub-cell) light share")
    plt.tight_layout(); plt.savefig(f"{args.out}/08_array_split.png", dpi=150); plt.close()

    # ---------- Summary table ----------
    print("\n================ SiPM-sizing experiment summary ================")
    print(f"{'metric':<34}" + "".join(f"{l:>16}" for l in labels))
    def row(name, vals, fmt="{:.2f}"):
        print(f"{name:<34}" + "".join(f"{fmt.format(v):>16}" for v in vals))
    row("events", [len(data[l][3]) for l in labels], "{:.0f}")
    row("mean photons/event", [data[l][3].mean() for l in labels])
    row("std photons/event", [data[l][3].std() for l in labels])
    row("photons/MeV (collected/Edep)", [(data[l][3].sum()/data[l][2].sum()) for l in labels], "{:.1f}")
    row("collection efficiency (%)", [e*100 for e in eff])
    # symmetry: CV across the 8 sites (pooled over events)
    cv = []
    for l in labels:
        sm = data[l][4].mean(axis=0)
        cv.append(sm.std() / sm.mean() if sm.mean() else np.nan)
    row("site-response CV (lower=more uniform)", cv, "{:.3f}")
    # 4-edge means
    for l in labels:
        sm = data[l][4].mean(axis=0)
        edges = [sm[0:2].mean(), sm[2:4].mean(), sm[4:6].mean(), sm[6:8].mean()]
        print(f"   {l:<30} per-edge means [+X,-X,+Y,-Y] = " +
              " ".join(f"{v:.1f}" for v in edges))
    print("===============================================================")
    print(f"\nFigures written to {args.out}/")

    # save a machine-readable summary
    with open(f"{args.out}/summary.txt", "w") as f:
        f.write("SiPM-sizing experiment summary\n")
        for l in labels:
            sm = data[l][4].mean(axis=0)
            f.write(f"\n{l}: events={len(data[l][3])} mean_photons={data[l][3].mean():.2f} "
                    f"photons_per_MeV={data[l][3].sum()/data[l][2].sum():.1f} "
                    f"siteCV={(sm.std()/sm.mean() if sm.mean() else float('nan')):.3f}\n")


if __name__ == "__main__":
    main()
