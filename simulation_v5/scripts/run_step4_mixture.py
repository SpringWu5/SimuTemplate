#!/usr/bin/env python3
"""run_step4_mixture.py -- audit & validate the mixture fit (v5 STEP 4).

Reproduces the v4 claim (f_single=0, f_corr=0.25, f_fake=0.75) with the FIXED
geometric correlated model and a CORRECT multinomial likelihood, then checks
whether the fit is visually/statistically consistent. Outputs figures/tables.
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, components as C, likelihood as L
from simulation_v5 import geometry as G

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TBL, exist_ok=True)

print("== STEP 4: mixture audit (fixed correlated + multinomial likelihood) ==")
rng = np.random.default_rng(2024)
# build single-muon base (resampled, unweighted, M>=1 for toy completion)
print("  generating IS sample + resampling...")
iss = GEN.sample_single(8_000_000, n=2.0, rng=np.random.default_rng(11))
sM1 = GEN.resample_triggered(iss, 400_000, np.random.default_rng(12), Mmin=1)
sM2 = GEN.resample_triggered(iss, 400_000, np.random.default_rng(13), Mmin=2)

# C1 single (triggered M2 topology)
c1 = C.component_single(sM2)
print("  C1 single p_topo:", np.round(c1["p_topo"], 3), "same-layer=%.3f" % (c1["p_topo"][0]+c1["p_topo"][1]))

# C2 correlated: try transverse (physical) and det_x
c2t = C.component_correlated(sM1, p_corr=0.5, s_cm=12.0, sigma_deg=5.0,
                             offset_mode="transverse", rng=np.random.default_rng(21))
c2x = C.component_correlated(sM1, p_corr=0.5, s_cm=12.0, sigma_deg=5.0,
                             offset_mode="det_x", rng=np.random.default_rng(22))
print("  C2 corr transverse same-layer=%.3f M3=%.3f" % (c2t["p_topo"][0]+c2t["p_topo"][1], c2t["p_M3"]))
print("  C2 corr det_x     same-layer=%.3f M3=%.3f" % (c2x["p_topo"][0]+c2x["p_topo"][1], c2x["p_M3"]))

# F1 fake uniform
f1 = C.component_fake_uniform()

# ---- Fit A: C1 + C2(transverse) + F1 ----
for label, c2 in [("transverse", c2t), ("det_x", c2x)]:
    comps = [c1, c2, f1]
    CF = C.stack_topo(comps)
    res = L.fit_grid(CF, ngrid=41)
    d = res["diag"]
    print(f"\n  [Fit C1+C2({label})+F1] best f = {np.round(res['best'],3)}")
    print(f"    -2logL={d['neg2logL']:.2f}  Pearson={d['pearson']:.2f}  G-test={d['deviance_G']:.2f}  (dof=3)")
    print(f"    pred counts = {np.round(d['pred'],1)}")
    print(f"    data counts = {L.DATA_COUNTS.astype(int)}")
    print(f"    pulls       = {np.round(d['pull'],2)}")
    # table
    with open(f"{TBL}/v5_mixture_fit_{label}.csv", "w", newline="") as fp:
        w_ = csv.writer(fp)
        w_.writerow(["topo", "data", "pred", "pull"])
        for i, t in enumerate(G.TOPO):
            w_.writerow([t, int(L.DATA_COUNTS[i]), round(float(d["pred"][i]), 2), round(float(d["pull"][i]), 2)])
        w_.writerow(["f_single", "", round(float(res["best"][0]), 3), ""])
        w_.writerow(["f_corr", "", round(float(res["best"][1]), 3), ""])
        w_.writerow(["f_fake", "", round(float(res["best"][2]), 3), ""])
        w_.writerow(["neg2logL", "", round(float(d["neg2logL"]), 2), ""])
        w_.writerow(["Pearson_chi2", "", round(float(d["pearson"]), 2), ""])
        w_.writerow(["G_test", "", round(float(d["deviance_G"]), 2), ""])

    # ---- data vs prediction bar + pulls ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    x = np.arange(6)
    axes[0].bar(x - 0.3, L.DATA_COUNTS, 0.3, label="data", color="#444")
    axes[0].bar(x, d["pred"], 0.3, label="best fit", color="#2ca02c")
    axes[0].set_xticks(x); axes[0].set_xticklabels(G.TOPO); axes[0].set_ylabel("count (M2)")
    axes[0].set_title(f"Fit C1+C2({label})+F1: f=({res['best'][0]:.2f},{res['best'][1]:.2f},{res['best'][2]:.2f})")
    axes[0].legend(fontsize=8)
    colors = ["r" if abs(p) > 2 else "k" for p in d["pull"]]
    axes[1].bar(x, d["pull"], 0.4, color=colors)
    axes[1].set_xticks(x); axes[1].set_xticklabels(G.TOPO); axes[1].set_ylabel("pull (pred-data)/sqrt(pred)")
    axes[1].set_title(f"pulls  (Pearson={d['pearson']:.1f}, G={d['deviance_G']:.1f}, dof=3)")
    axes[1].axhline(0, color="k", lw=0.5)
    plt.tight_layout(); plt.savefig(f"{FIG}/10_mixture_fit_{label}.png", dpi=130); plt.close()

    # ---- ternary profile ----
    pts = res["pts"]; n2 = res["n2"]; n2 -= n2.min()
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sc = ax.scatter(pts[:, 2], pts[:, 1] + pts[:, 2] / 2, c=n2, cmap="viridis_r",
                    s=10, vmin=0, vmax=20)
    # 1/2/3-sigma contours (Delta -2logL = 3.84/5.99/... for 2-param)
    for cut, lbl in [(3.84, "1s"), (5.99, "2s"), (11.3, "3s")]:
        m = n2 <= cut
        if m.sum() > 2:
            ax.scatter(pts[m, 2], pts[m, 1] + pts[m, 2] / 2, s=2, c="k")
            ax.text(pts[n2.argmin(), 2], pts[n2.argmin(), 1] + pts[n2.argmin(), 2] / 2, lbl, fontsize=7)
    ax.set_xlabel("f_fake"); ax.set_ylabel("f_corr")
    ax.set_title(f"ternary -2logL profile  ({label})")
    plt.colorbar(sc, label="-2logL (rel)")
    plt.tight_layout(); plt.savefig(f"{FIG}/11_ternary_{label}.png", dpi=130); plt.close()

# ---- profile-likelihood 1D intervals on each fraction (transverse fit) ----
CF = C.stack_topo([c1, c2t, f1])
print("\n  profile-likelihood 1D intervals:")
with open(f"{TBL}/v5_profile_intervals.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["component", "best", "1sigma_lo", "1sigma_hi"])
    names = ["f_single", "f_corr", "f_fake"]
    for k in range(3):
        fs, prof, lo1, hi1, lo2, hi2 = L.confidence_interval_1d(CF, L.fit_grid(CF, 41)["best"], k)
        print(f"    {names[k]}: best={L.fit_grid(CF,41)['best'][k]:.3f}  1sigma=[{lo1:.3f},{hi1:.3f}]")
        w_.writerow([names[k], round(float(L.fit_grid(CF, 41)["best"][k]), 3), round(float(lo1), 3), round(float(hi1), 3)])

print("\nSTEP 4 done.")
