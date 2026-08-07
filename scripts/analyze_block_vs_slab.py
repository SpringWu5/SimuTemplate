#!/usr/bin/env python3
"""
analyze_block_vs_slab.py -- compare the small scintillator BLOCK's single SiPM
to the slab's SiPMs when the muon strikes right above one slab SiPM.

  Block : 2x3x3 cm, 1 SiPM (6 mm) on a 2x3 side face, muon through 3 cm.
  Slab  : 20x20x2 cm, 8 SiPMs (6 mm), muon over the +X/+5cm SiPM (channel 0),
          region x in [7,10] cm, y in [4,6] cm (the block footprint).

No PDE (raw photons) in both. Reports photons/muon and photons/MeV for:
  block SiPM  vs  slab under-SiPM (ch0)  vs  slab other-7 avg  vs  slab all-8 avg.
"""
import argparse
import os
import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def per_event(path, block=False):
    t = uproot.open(path)["Simu"]
    a = t.arrays(["VoxelEdep", "SiPMHit_Det_ID"], library="np")
    n = len(a["VoxelEdep"])
    edep = np.array([float(np.sum(v)) for v in a["VoxelEdep"]])
    ch0 = np.zeros(n); other = np.zeros(n); total = np.zeros(n)
    for i in range(n):
        ds = a["SiPMHit_Det_ID"][i]
        total[i] = len(ds)
        for ch in ds:
            if int(ch) == 0:
                ch0[i] += 1
            else:
                other[i] += 1
    return edep, ch0, other, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--block", required=True)
    ap.add_argument("--slab", required=True)
    ap.add_argument("--out", default="artifacts/block_vs_slab")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    be, b0, _, _ = per_event(args.block)          # block: only ch0
    se, s0, sO, sT = per_event(args.slab)         # slab: ch0 = under-SiPM

    n_other = 7.0
    metrics = {
        "Block SiPM":         (b0, be),
        "Slab under-SiPM":    (s0, se),
        "Slab other-7 (avg)": (sO / n_other, se),
        "Slab all-8 (avg)":   (sT / 8.0, se),
    }

    print("\n=========== block vs slab (muon over one slab SiPM) ===========")
    print(f"{'quantity':<22}{'ph/mu':>12}{'ph/MeV':>12}{'Edep(MeV)':>12}")
    rows = {}
    for k, (ph, ed) in metrics.items():
        pmu = ph.mean()
        pmev = ph.sum() / ed.sum() if ed.sum() else float("nan")
        rows[k] = (pmu, pmev, ed.mean())
        print(f"{k:<22}{pmu:>12.1f}{pmev:>12.2f}{ed.mean():>12.2f}")
    print("==============================================================")

    # ---- Fig 1: photons/muon bar ----
    fig, ax = plt.subplots(figsize=(7, 4))
    keys = list(metrics)
    vals = [rows[k][0] for k in keys]
    ax.bar(keys, vals, color=["#C44E52", "#4C72B0", "#888888", "#55A868"])
    ax.set_ylabel("photons / muon")
    ax.set_title("SiPM light yield: block vs slab (muon above one slab SiPM)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right", fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/01_photons_per_muon.png", dpi=150); plt.close()

    # ---- Fig 2: photons/MeV (collection efficiency) bar ----
    fig, ax = plt.subplots(figsize=(7, 4))
    vals = [rows[k][1] for k in keys]
    ax.bar(keys, vals, color=["#C44E52", "#4C72B0", "#888888", "#55A868"])
    ax.set_ylabel("photons / MeV (collection efficiency)")
    ax.set_title("Per-SiPM collection efficiency")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right", fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/02_per_mev.png", dpi=150); plt.close()

    # ---- Fig 3: per-event histogram block vs slab-under ----
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.hist(b0, bins=40, histtype="step", lw=1.5, label=f"Block SiPM (μ={b0.mean():.0f})")
    ax.hist(s0, bins=40, histtype="step", lw=1.5, label=f"Slab under-SiPM (μ={s0.mean():.1f})")
    ax.set_xlabel("photons / muon"); ax.set_ylabel("events")
    ax.set_title("Per-event SiPM yield distribution"); ax.legend(fontsize=9)
    plt.tight_layout(); plt.savefig(f"{args.out}/03_histogram.png", dpi=150); plt.close()

    # ---- summary text ----
    with open(f"{args.out}/summary.txt", "w") as f:
        f.write("block vs slab (muon over one slab SiPM)\n")
        for k in keys:
            pmu, pmev, ed = rows[k]
            f.write(f"{k}: {pmu:.1f} ph/mu, {pmev:.2f} ph/MeV, Edep={ed:.2f} MeV\n")
    print(f"\nFigures -> {args.out}/")


if __name__ == "__main__":
    main()
