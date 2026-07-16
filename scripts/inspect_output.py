#!/usr/bin/env python3
"""
inspect_output.py -- quick SimuTemplate output inspector.

Reads the GeometryModel (detector -> 3D model map) and Simu trees from a
SimuTemplate ROOT file and prints a summary. Optionally saves a 3D scatter
of all volumes to a PNG.

Usage:
    python3 scripts/inspect_output.py build/output.root
    python3 scripts/inspect_output.py build/output.root --plot-output artifacts/overview.png
"""
import argparse
import sys

import uproot
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="SimuTemplate output ROOT file")
    ap.add_argument("--plot-output", default=None,
                    help="Optional PNG path for a 3D volume scatter")
    args = ap.parse_args()

    f = uproot.open(args.input)
    print("ROOT keys:", list(f.keys()))

    # ---- Geometry model (generic 3D export) ----
    if "GeometryModel" in f:
        geo = f["GeometryModel"].arrays(library="np")
        n = len(geo["X"])
        print(f"\n[GeometryModel] {n} volumes")
        names = sorted(set(geo["Name"]))
        print(f"  unique logical volumes: {len(names)}")
        for nm in names:
            m = geo["Name"] == nm
            print(f"    {nm:20s} x{int(m.sum())}  "
                  f"mat={set(geo['Material'][m])}")
    else:
        print("[GeometryModel] not found", file=sys.stderr)

    # ---- Simu tree (event data) ----
    if "Simu" in f:
        simu = f["Simu"]
        nev = simu.num_entries
        print(f"\n[Simu] {nev} events, branches: {simu.keys()}")
        if "eventID" in simu.keys():
            print("  eventID range:",
                  simu["eventID"].array(library="np").min(),
                  "..",
                  simu["eventID"].array(library="np").max())

        # ---- Hit summary: SiPM photons + scintillator truth ----
        def hit_stats(branch_name):
            if branch_name not in simu.keys():
                return None
            arr = simu[branch_name].array(library="np")
            lengths = np.array([len(x) for x in arr])
            return int(lengths.sum()), int((lengths > 0).sum())

        print("\n[Hit summary]")
        groups = [
            ("SiPM (MuonCube)",        "SiPMHit_Det_ID"),
            ("SiPM legacy (MuonSLab)", "SiPM_OldHit_Det_ID"),
            ("Scint truth (voxels)",   "VoxelID"),
        ]
        sipm_total = 0
        for label, br in groups:
            s = hit_stats(br)
            if s is None:
                print(f"  {label:24s} branch '{br}' not present")
                continue
            total, evts = s
            if "SiPM" in label:
                sipm_total += total
            flag = "OK" if total > 0 else "NONE"
            print(f"  {label:24s} hits={total:6d}  events_with_hits={evts}/{nev}  [{flag}]")

        if "VoxelEdep" in simu.keys():
            edep = simu["VoxelEdep"].array(library="np")
            tot_edep = sum(float(np.sum(x)) for x in edep)
            print(f"  {'Total scint Edep':24s} = {tot_edep:.3f} MeV "
                  f"(across {nev} events)")

        print("\n>>> VERDICT: " +
              ("SiPM photons detected -> detector chain OK"
               if sipm_total > 0 else
               "NO SiPM photons detected -> investigate"))
    else:
        print("[Simu] not found", file=sys.stderr)

    # ---- Optional 3D plot ----
    if args.plot_output and "GeometryModel" in f:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(9, 8))
        ax = fig.add_subplot(111, projection="3d")
        for nm in sorted(set(geo["Name"])):
            if nm in ("World",):
                continue
            m = geo["Name"] == nm
            ax.scatter(geo["X"][m], geo["Y"][m], geo["Z"][m], s=4, label=nm,
                       alpha=0.6)
        ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
        ax.set_title("SimuTemplate geometry (GeometryModel)")
        ax.legend(fontsize=7, loc="upper right")
        plt.tight_layout()
        import os
        os.makedirs(os.path.dirname(args.plot_output) or ".", exist_ok=True)
        plt.savefig(args.plot_output, dpi=150)
        print(f"\nSaved 3D plot -> {args.plot_output}")


if __name__ == "__main__":
    main()
