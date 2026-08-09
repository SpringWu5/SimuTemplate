#!/usr/bin/env python3
"""
analyze_stacked.py -- light-sharing & multiplicity analysis for the stacked run.

Per event: 8 slab SiPM photon counts (mapped to Ch4..Ch11), slab Edep, and which
small scints fired (Edep>0). For cosmic (O1) events we further split by small-sciont
topology (T02 = Ch0&Ch2, T13 = Ch1&Ch3) and compare the slab light-sharing to the
experimental targets. Also scans panel multiplicity vs threshold (M8 question).

No PDE in the sim (raw photons); PE ~ x0.40. Fraction f_i is PDE-independent.
"""
import argparse, os
import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# channel(int) -> Ch label ; map per StackedDetector header
CHMAP = {0: "Ch4", 100: "Ch5", 1000: "Ch8", 1100: "Ch9",
         2000: "Ch6", 2100: "Ch7", 3000: "Ch11", 3100: "Ch10"}
CH_IDS = [0, 100, 1000, 1100, 2000, 2100, 3000, 3100]   # 8 SiPMs
CH_LABELS = [CHMAP[c] for c in CH_IDS]
ID_CH11, ID_CH10 = 3000, 3100
# small scint volume copy numbers -> channel
SMALL = {20: 0, 21: 1, 22: 2, 23: 3}   # vol id -> Ch0..Ch3

# experimental light-sharing targets (approx, from prompt)
DATA = {"T02": {"f11": 0.252, "f10": 0.083}, "T13": {"f10": 0.229, "f11": 0.083}}


def load(path):
    t = uproot.open(path)["Simu"]
    return t.arrays(["VoxelID", "VoxelEdep", "SiPMHit_Det_ID"], library="np")


def per_event(a):
    n = len(a["VoxelID"])
    edep = {10: np.zeros(n), 20: np.zeros(n), 21: np.zeros(n), 22: np.zeros(n), 23: np.zeros(n)}
    for i in range(n):
        for j, v in enumerate(a["VoxelID"][i]):
            vi = int(v)
            if vi in edep:
                edep[vi][i] += float(a["VoxelEdep"][i][j])
    sipm = {c: np.zeros(n) for c in CH_IDS}
    for i in range(n):
        for ch in a["SiPMHit_Det_ID"][i]:
            c = int(ch)
            if c in sipm:
                sipm[c][i] += 1
    return edep, sipm, n


def fractions(sipm, mask):
    """mean per-SiPM fraction f_i over events in mask."""
    tot = np.zeros(mask.sum())
    arr = {c: sipm[c][mask] for c in CH_IDS}
    S = sum(arr.values())
    Ssafe = np.where(S > 0, S, 1)
    fi = {c: np.mean(np.where(S > 0, arr[c] / Ssafe, 0.0)) for c in CH_IDS}
    return fi, S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--tag", default="stacked")
    ap.add_argument("--out", default="simulation_v3/figures/optics")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    os.makedirs("simulation_v3/tables", exist_ok=True)

    edep, sipm, n = per_event(load(args.input))
    slabE = edep[10]
    sm = {ch: edep[vid] for vid, ch in SMALL.items()}     # Ch0..Ch3 Edep
    fired = {ch: sm[ch] > 0 for ch in sm}
    panel_pos = slabE > 0   # slab crossed

    # topology masks (small-sciont)
    T = {"T02": fired[0] & fired[2], "T13": fired[1] & fired[3],
         "T03": fired[0] & fired[3], "T12": fired[1] & fired[2]}

    print(f"\n=== {args.tag}: {n} events ===")
    print(f"slab-crossed (panel-positive) events: {panel_pos.sum()} ({panel_pos.mean()*100:.0f}%)")
    for k, m in T.items():
        print(f"  {k}: {m.sum()} small-sciont events; of those slab-crossed {(m&panel_pos).sum()}")

    # ---- Fig 1: mean f_i (all events with slab light) ----
    mlight = sum(sipm.values()) > 0
    fi, _ = fractions(sipm, mlight)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(CH_LABELS, [fi[c] for c in CH_IDS], color="#4C72B0")
    ax.set_ylabel("mean f_i (N_i / sum N_SiPM)")
    ax.set_title(f"{args.tag}: mean slab SiPM light-sharing fraction")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout(); plt.savefig(f"{args.out}/{args.tag}_fractions_all.png", dpi=150); plt.close()

    # ---- Fig 2: f for T02 and T13 vs data ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    rows = []
    for ax, key in zip(axes, ["T02", "T13"]):
        m = T[key] & mlight
        if m.sum() == 0:
            ax.set_title(f"{key}: no events"); continue
        fk, _ = fractions(sipm, m)
        x = np.arange(8)
        ax.bar(x - 0.2, [fk[c] for c in CH_IDS], 0.4, label=f"MC {key} (n={m.sum()})")
        # mark data f10/f11
        ax.axhline(DATA[key]["f11"], color="r", ls="--", lw=1, label=f"data f11={DATA[key]['f11']}")
        ax.axhline(DATA[key]["f10"], color="g", ls=":", lw=1, label=f"data f10={DATA[key]['f10']}")
        ax.set_xticks(x); ax.set_xticklabels(CH_LABELS, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("f_i"); ax.set_title(f"{key} light sharing: MC vs data"); ax.legend(fontsize=7)
        rows.append((key, m.sum(), fk[ID_CH11], fk[ID_CH10]))
    plt.tight_layout(); plt.savefig(f"{args.out}/{args.tag}_fractions_T02_T13.png", dpi=150); plt.close()

    # ---- Fig 3: X_front = (N11-N10)/(N11+N10) ----
    S = sipm[ID_CH11] + sipm[ID_CH10]
    xf = np.where(S > 0, (sipm[ID_CH11] - sipm[ID_CH10]) / np.where(S > 0, S, 1), np.nan)
    mm = mlight & ~np.isnan(xf)
    fig, ax = plt.subplots(figsize=(6, 4))
    for key, col in [("T02", "#4C72B0"), ("T13", "#C44E52")]:
        m = T[key] & mm
        if m.sum(): ax.hist(xf[m], bins=30, histtype="step", lw=1.5, density=True, label=f"{key} (n={m.sum()})", color=col)
    ax.set_xlabel("X_front = (N11 - N10)/(N11 + N10)"); ax.set_ylabel("a.u.")
    ax.set_title(f"{args.tag}: front-face Ch10/Ch11 asymmetry"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/{args.tag}_xfront.png", dpi=150); plt.close()

    # ---- Fig 4: panel multiplicity M (of 8 SiPMs) vs threshold ----
    thr = [0.5, 1, 2, 3, 5, 10, 20, 50]
    Mdist = {}
    fig, ax = plt.subplots(figsize=(7, 4))
    P8 = []
    for Tp in thr:
        over = np.array([sipm[c] > Tp for c in CH_IDS]).sum(axis=0)  # M per event
        Mdist[Tp] = np.bincount(over, minlength=9) / max(1, len(over))
        P8.append(Mdist[Tp][8])
    for Tp in [1, 2, 5, 10]:
        ax.plot(range(9), Mdist[Tp], "o-", ms=4, label=f"thr={Tp} ph")
    ax.set_xlabel("panel multiplicity M (of 8 SiPMs)"); ax.set_ylabel("fraction of slab-crossed events")
    ax.set_title(f"{args.tag}: panel M distribution vs SiPM threshold"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{args.out}/{args.tag}_multiplicity.png", dpi=150); plt.close()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(thr, P8, "o-")
    ax.set_xlabel("SiPM threshold (raw photons; PE~x0.4)"); ax.set_ylabel("P(M=8)")
    ax.set_xscale("log"); ax.set_title(f"{args.tag}: P(panel M=8) vs threshold")
    plt.tight_layout(); plt.savefig(f"{args.out}/{args.tag}_M8_vs_threshold.png", dpi=150); plt.close()

    # ---- summary ----
    print("\nlight-sharing f_i (all slab-light events):")
    for c in CH_IDS: print(f"  {CHMAP[c]}: {fi[c]:.3f}")
    print("\nT02/T13 f11,f10 vs data:")
    print(f"{'topo':>5}{'n':>6}{'f11_MC':>9}{'f11_data':>10}{'f10_MC':>9}{'f10_data':>10}")
    for key, nn, f11, f10 in rows:
        d = DATA[key]
        print(f"{key:>5}{nn:6d}{f11:9.3f}{d['f11']:10.3f}{f10:9.3f}{d['f10']:10.3f}")
    print(f"\nP(M=8) vs threshold {thr}: {[f'{p:.3f}' for p in P8]}")
    import csv
    with open(f"simulation_v3/tables/stacked_{args.tag}_lightshare.csv", "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["topo", "n", "f11_MC", "f11_data", "f10_MC", "f10_data"])
        for key, nn, f11, f10 in rows:
            w.writerow([key, nn, f"{f11:.3f}", DATA[key]["f11"], f"{f10:.3f}", DATA[key]["f10"]])
    print(f"\nfigures -> {args.out}/{args.tag}_*.png")


if __name__ == "__main__":
    main()
