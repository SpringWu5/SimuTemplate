#!/usr/bin/env python3
"""run_step3_panel_validate.py -- validate unified panel model vs Geant4 (STEP 3).

Feeds the SAME 120 Geant4 Edep values through panel_v6, compares the M-distribution
and per-SiPM photon statistics to Geant4 truth. Then recomputes P(panel dark |
single cross) under multiple 'dark' definitions (D1-D4).
"""
import os, sys, json, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v6 import panel_v6 as PV

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
NAMES = PV.NAMES

# load Geant4 truth library
with open(os.path.join(ROOT, "optical_library", "geant4_120events.json")) as f:
    lib = json.load(f)
e_g4 = np.array(lib["edep"])
g4_sipm = np.stack([np.array(lib["sipm"][n]) for n in NAMES], axis=1)  # [120,8] raw photons
rng = np.random.default_rng(42)

# ---- generate model photons for the SAME edep (many Poisson draws to fill stats) ----
Nrep = 200  # replicate each event to smooth
e_rep = np.repeat(e_g4, Nrep)
ph_model = PV.panel_photons(e_rep, rng)
# reshape to [120, Nrep, 8] -> per-event mean
ph_model_per = ph_model.reshape(120, Nrep, 8)

# ---- Fig: per-SiPM mean photons, Geant4 vs model ----
g4_mean = g4_sipm.mean(0)
mod_mean = ph_model.mean(0)
print("per-SiPM mean photons: Geant4 vs model")
for i, nm in enumerate(NAMES):
    print(f"  {nm}: G4={g4_mean[i]:.2f}  model={mod_mean[i]:.2f}")

# ---- M-distribution comparison (raw photon thresholds) ----
print("\nM-distribution (raw photon threshold):")
thr_list = [0.5, 1, 2, 3, 5, 10]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
# Geant4 M-dist
for Tp in [1, 2, 5]:
    Mg4 = (g4_sipm > Tp).sum(1)
    md = np.bincount(Mg4, minlength=9) / 120
    axes[0].plot(range(9), md, "o-", ms=4, label=f"G4 thr={Tp}")
# model M-dist (use all reps pooled)
for Tp in [1, 2, 5]:
    Mm = (ph_model > Tp).sum(1)
    md = np.bincount(Mm, minlength=9) / len(Mm)
    axes[0].plot(range(9), md, "--", ms=3, label=f"model thr={Tp}")
axes[0].set_xlabel("panel multiplicity M"); axes[0].set_ylabel("fraction")
axes[0].set_title("M-distribution: Geant4 (solid) vs model (dashed)"); axes[0].legend(fontsize=7)

# P(M8) vs threshold
g4_p8 = []; mod_p8 = []
for Tp in thr_list:
    g4_p8.append(np.mean((g4_sipm > Tp).sum(1) == 8))
    mod_p8.append(np.mean((ph_model > Tp).sum(1) == 8))
axes[1].plot(thr_list, g4_p8, "o-", label="Geant4")
axes[1].plot(thr_list, mod_p8, "s--", label="model (NB calibrated)")
axes[1].set_xlabel("threshold (raw photons)"); axes[1].set_ylabel("P(M=8)")
axes[1].set_xscale("log"); axes[1].set_title("P(M=8) vs threshold"); axes[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/01_panel_model_vs_geant4.png", dpi=130); plt.close()

print("\nP(M8) vs threshold:")
print(f"  {'thr':>5}{'G4':>8}{'model':>8}")
for Tp, g, m in zip(thr_list, g4_p8, mod_p8):
    print(f"  {Tp:>5}{g:>8.3f}{m:>8.3f}")

# ---- STEP 7: P(panel dark | single cross) under D1-D4 ----
# Use a large single-cross sample: replicate with Edep drawn from Landau over slab path
from simulation_v5 import generator as GEN
iss = GEN.sample_single(6_000_000, n=2.0, rng=np.random.default_rng(7))
s = GEN.resample_triggered(iss, 300_000, np.random.default_rng(8), Mmin=1)
pslab = s["pslab"]; H = s["H"]; M = s["M"]
cross = (((H[:, 0] & H[:, 2]) | (H[:, 1] & H[:, 3]) | (H[:, 0] & H[:, 3]) | (H[:, 1] & H[:, 2])) &
         (M == 2) & (pslab > 0))
edep_cross = np.where(pslab[cross] > 0,
                      np.maximum(PV.RATE.mean() * 0 + 2.0 * PV.__dict__.get("__x__", 1.0), 0.0), 0.0)  # placeholder
# proper slab Edep via Landau
from simulation_v5.response import landau_edep
edep_cross = np.array([landau_edep(float(p), np.random.default_rng(9)) for p in pslab[cross]])
print(f"\nsingle cross-layer events: {cross.sum()}, slab Edep mean={edep_cross.mean():.2f} MeV")

# scan PDE and threshold; report P(D1..D4)
print("\nP(panel dark | single cross) [D1=M0, D2=no ch>thr, D3=score<q05, D4=totalPE<thr]")
rng2 = np.random.default_rng(11)
rows = []
for pde in [0.30, 0.40, 0.50]:
    pe, ph = PV.panel_pe(edep_cross, rng2, pde=pde)
    for thr_pe in [0.5, 1.0, 2.0]:
        amp = pe + rng2.normal(0, 0.5, pe.shape)
        fired = amp > thr_pe
        M_ = fired.sum(1)
        D1 = np.mean(M_ == 0)
        D2 = np.mean(M_ < 8) * 0 + np.mean(~fired.any(1))  # no channel above thr
        tot_pe = pe.sum(1)
        # D3: score below 5th percentile of total PE (proxy ~ near 0)
        D3 = np.mean(tot_pe < np.percentile(tot_pe, 5))
        D4 = np.mean(tot_pe < thr_pe * 8 * 0.5)
        rows.append((pde, thr_pe, D1, D2, D3, D4, np.mean(M_ == 8)))
        print(f"  pde={pde} thr={thr_pe}: P(M0)={D1:.4f} P(no>thr)={D2:.4f} "
              f"P(M8)={np.mean(M_==8):.3f} <M>={M_.mean():.2f}")

with open(f"{TBL}/v6_panel_dark_probability.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["pde", "thr_pe", "P_M0", "P_no_above_thr", "P_M8", "mean_M"])
    for pde, thr, d1, d2, d3, d4, p8 in rows:
        w.writerow([pde, thr, round(d1, 5), round(d2, 5), round(p8, 4), ""])
print("\nSTEP 3 done.")
