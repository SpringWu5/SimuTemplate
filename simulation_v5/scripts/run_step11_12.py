#!/usr/bin/env python3
"""run_step11_12.py -- joint topology+panel mixture, model comparison, PPC (STEP 11-12).

12-bin data vector = 6 topologies x {M8, nonM8}. Panel M8 is the key discriminator:
single through-going muon -> bright panel (M8); non-crossing events -> dark (nonM8).

Models compared (AIC/BIC):
  M1: single only
  M2: single + correlated(det_x)
  M3: single + correlated + non-crossing(B2/B3)
"""
import os, sys, csv, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, response as R, geometry as G, toys as T, panel as P

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
TOPO = G.TOPO
# ---- data 12-bin: topology x panel ----
# pure-M2 topology counts
DC = {"01": 78, "23": 57, "02": 52, "13": 25, "03": 25, "12": 18}
SAME_M8 = {"01": 4, "23": 3}
CROSS_M8_TOT = 50; CROSS_TOT = sum(DC[t] for t in ["02", "13", "03", "12"])
# distribute cross M8 proportionally
CROSS_M8 = {t: DC[t] / CROSS_TOT * CROSS_M8_TOT for t in ["02", "13", "03", "12"]}
M8 = {**SAME_M8, **CROSS_M8}
data12 = np.zeros(12)
for i, t in enumerate(TOPO):
    data12[2 * i] = M8[t]            # M8 bin
    data12[2 * i + 1] = DC[t] - M8[t]  # nonM8 bin
NTOT12 = data12.sum()

print("== STEP 11-12: joint topology+panel mixture + model comparison ==")
iss = GEN.sample_single(8_000_000, n=2.0, rng=np.random.default_rng(301))
s = GEN.resample_triggered(iss, 600_000, np.random.default_rng(302), Mmin=1)
Hg = s["H"]; Ng = Hg.shape[0]; pslab = s["pslab"]

# precompute small npe + slab pe for panel conditionals
rng = np.random.default_rng(5)
npe = np.zeros((Ng, 4))
for i, ch in enumerate(G.ALLCH):
    from simulation_v5.response import landau_edep as _le
    path = s["paths"][ch]
    e = np.where(path > 0, _le(np.where(path > 0, path, 1e-3), rng), 0.0)
    npe[:, i] = np.where(path > 0, rng.poisson(12.0 * e), 0.0)
pe_slab, _ = P.panel_pe(pslab, np.random.default_rng(51), Y_slab=400.0, pde=0.40)

# channel asymmetry: +20% left column (Ch1,Ch3)
def fire_pattern(thr_mip_base=0.5, dx=0.20, small_thr_factor=0.5, seed=0):
    r = np.random.default_rng(seed)
    thr_small = np.array([thr_mip_base, thr_mip_base*(1+dx), thr_mip_base, thr_mip_base*(1+dx)]) * R.E_MIP_VERT * 12.0
    amp = npe + r.normal(0, 2.0, (Ng, 4))
    fired = (amp > thr_small) & Hg
    return fired

def panel_m8(thr_pe=30, seed=0):
    m8, _ = P.m8_mask(pe_slab, thr_pe, noise=3.0, rng=np.random.default_rng(seed))
    return m8 & (pslab > 0)

def comp12(fired, m8, name):
    """Build 12-bin vector from fired pattern + panel mask."""
    M = fired.sum(1); m2 = M == 2
    out = np.zeros(12)
    for i, t in enumerate(TOPO):
        a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
        sel = m2 & fired[:, ia] & fired[:, ib]
        nm8 = np.sum(sel & m8); nn = np.sum(sel & ~m8)
        out[2*i] = nm8; out[2*i+1] = nn
    return out / max(out.sum(), 1e-9)

# C1 through-going single muon: cross-layer M2 + slab crossing (bright).
fired_orig = fire_pattern(seed=1); m8c = panel_m8(seed=1)
M0 = fired_orig.sum(1)
cr_bright = (M0 == 2) & m8c & ~(((fired_orig[:, 0] & fired_orig[:, 1]) | (fired_orig[:, 2] & fired_orig[:, 3])))
C1 = comp12(fired_orig & (M0 == 2)[:, None] & m8c[:, None], m8c, "C_through")
print(f"  C_through: bright cross fraction of M2 built")

# Build same-layer pairs via crosstalk from SINGLE-BLOCK originals, split by slab crossing.
single_block = (fired_orig.sum(1) == 1)
# dark same-layer: single-block, pslab==0 -> copy neighbour
Hsd = fired_orig.copy()
m_dark = np.zeros(Ng, bool)
rxc = np.random.default_rng(12)
for j in np.where(single_block & (pslab == 0))[0]:
    if rxc.random() < 0.6:
        if Hsd[j, 0]: Hsd[j, 1] = True
        elif Hsd[j, 1]: Hsd[j, 0] = True
        elif Hsd[j, 2]: Hsd[j, 3] = True
        elif Hsd[j, 3]: Hsd[j, 2] = True
C_samedark = comp12(Hsd, m_dark, "C_samedark")

# C_S2 bright same-layer: single-block + pslab>0 -> copy neighbour (panel from slab)
Hsb = fired_orig.copy()
for j in np.where(single_block & (pslab > 0))[0]:
    if Hsb[j, 0]: Hsb[j, 1] = True
    elif Hsb[j, 1]: Hsb[j, 0] = True
    elif Hsb[j, 2]: Hsb[j, 3] = True
    elif Hsb[j, 3]: Hsb[j, 2] = True
C_S2 = comp12(Hsb, m8c, "C_S2")

# C_crossdark: independent two-track (no through-going single), cross topology, panel dark.
Hi, _ = T.independent_two_track(s, p_multi=1.0, rng=np.random.default_rng(313))
C_crossdark = comp12(Hi, np.zeros(Ng, bool), "C_crossdark")
C_crossdark[0] = C_crossdark[1] = C_crossdark[2] = C_crossdark[3] = 0.0
C_crossdark /= max(C_crossdark.sum(), 1e-9)

def neg2ll(frac, comps, data):
    p = frac @ comps; p = np.clip(p, 1e-12, None); p /= p.sum()
    nz = data > 0
    return -2.0 * np.sum(data[nz] * np.log(p[nz]))

def fit(comps, data, ngrid=21):
    C = comps.shape[0]; best = (1e30, None)
    if C == 1:
        return np.array([1.0]), neg2ll(np.array([1.0]), comps, data)
    grids = [np.linspace(0, 1, ngrid) for _ in range(C - 1)]
    for combo in itertools.product(*grids):
        if sum(combo) > 1 + 1e-9: continue
        frac = np.array(list(combo) + [max(1 - sum(combo), 0.0)])
        v = neg2ll(frac, comps, data)
        if v < best[0]: best = (v, frac)
    return best[1], best[0]

# ---- model comparison ----
def aic(n2ll, k): return n2ll + 2 * k
def bic(n2ll, k, n): return n2ll + k * np.log(n)

results = {}
for name, comps, k in [("M1_through", np.array([C1]), 0),
                       ("M2_+samedark", np.array([C1, C_samedark]), 1),
                       ("M3_+crossdark", np.array([C1, C_samedark, C_crossdark]), 2),
                       ("M4_+S2", np.array([C1, C_samedark, C_crossdark, C_S2]), 3)]:
    frac, n2 = fit(comps, data12, ngrid=15)
    results[name] = dict(frac=frac, n2ll=n2, aic=aic(n2, k), bic=bic(n2, k, NTOT12), comps=comps)
    print(f"  {name}: frac={np.round(frac,3)} -2logL={n2:.1f} AIC={aic(n2,k):.1f} BIC={bic(n2,k,NTOT12):.1f}")

best_name = min(results, key=lambda x: results[x]["aic"])
best = results[best_name]; bf = best["frac"]; comps_best = best["comps"]
pred = bf @ comps_best; pred /= pred.sum()
pred_counts = pred * NTOT12
pull = (pred_counts - data12) / np.sqrt(np.where(pred_counts > 0, pred_counts, 1))
print(f"\n  BEST={best_name}")
print(f"  {'bin':<10}{'data':>7}{'pred':>7}{'pull':>7}")
for i, t in enumerate(TOPO):
    print(f"  {t+'_M8':<10}{data12[2*i]:>7.0f}{pred_counts[2*i]:>7.1f}{pull[2*i]:>7.2f}")
    print(f"  {t+'_no':<10}{data12[2*i+1]:>7.0f}{pred_counts[2*i+1]:>7.1f}{pull[2*i+1]:>7.2f}")
pearson = np.sum((data12 - pred_counts) ** 2 / np.where(pred_counts > 0, pred_counts, 1))
print(f"  Pearson chi2={pearson:.1f} (dof={12-1-len(bf)})")

# ---- plot data vs pred (best) ----
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
labels = [f"{t}_{'M8' if j else 'no'}" for t in TOPO for j in (1, 0)]
x = np.arange(12)
axes[0].bar(x - 0.3, data12, 0.3, label="data", color="#444")
axes[0].bar(x, pred_counts, 0.3, label=f"{best_name} pred", color="#2ca02c")
axes[0].set_xticks(x); axes[0].set_xticklabels(labels, rotation=45, fontsize=7)
axes[0].set_ylabel("count"); axes[0].set_title(f"joint fit: frac={np.round(bf,2)}")
axes[0].legend(fontsize=8)
axes[1].bar(x, pull, 0.4, color=["r" if abs(p) > 2 else "k" for p in pull])
axes[1].set_xticks(x); axes[1].set_xticklabels(labels, rotation=45, fontsize=7)
axes[1].set_ylabel("pull"); axes[1].set_title(f"pulls (Pearson={pearson:.1f})")
plt.tight_layout(); plt.savefig(f"{FIG}/18_joint_fit.png", dpi=130); plt.close()

# AIC/BIC comparison bar
fig, ax = plt.subplots(figsize=(7, 4))
names = list(results); ax.bar(names, [results[n]["aic"] for n in names], 0.5, label="AIC")
ax.bar(names, [results[n]["bic"] for n in names], 0.3, label="BIC", alpha=0.6)
ax.set_ylabel("AIC/BIC (lower=better)"); ax.legend(fontsize=8)
ax.set_title("model comparison"); plt.tight_layout(); plt.savefig(f"{FIG}/19_model_comparison.png", dpi=130); plt.close()

# ---- STEP 12: posterior predictive check ----
print("  STEP 12: posterior predictive ...")
rngpp = np.random.default_rng(999)
npp = 2000
pp_topo = np.zeros((npp, 6)); pp_m8_cross = np.zeros(npp); pp_m8_same = np.zeros(npp)
pp_m3 = np.zeros(npp)
for b in range(npp):
    sample12 = rngpp.multinomial(int(NTOT12), pred)
    # recover topology + panel
    for i, t in enumerate(TOPO):
        pp_topo[b, i] = sample12[2*i] + sample12[2*i+1]
    pp_m8_cross[b] = sum(sample12[2*i] for i, t in enumerate(TOPO) if t in ["02","13","03","12"])
    pp_m8_same[b] = sum(sample12[2*i] for i, t in enumerate(TOPO) if t in ["01","23"])
data_topo = np.array([DC[t] for t in TOPO])
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
axes[0].boxplot([pp_topo[:, i] for i in range(6)], positions=range(6), showfliers=False)
axes[0].plot(range(6), data_topo, "rx", ms=10, mew=2, label="data")
axes[0].set_xticklabels(TOPO); axes[0].set_ylabel("count"); axes[0].legend(fontsize=8)
axes[0].set_title("PPC: six topology")
axes[1].hist(pp_m8_cross, 30); axes[1].axvline(CROSS_M8_TOT, color="r", label=f"data {CROSS_M8_TOT}")
axes[1].set_xlabel("cross-M8 count"); axes[1].legend(fontsize=8); axes[1].set_title("PPC: cross M8")
axes[2].hist(pp_m8_same, 30); axes[2].axvline(sum(SAME_M8.values()), color="r", label=f"data {sum(SAME_M8.values())}")
axes[2].set_xlabel("same-M8 count"); axes[2].legend(fontsize=8); axes[2].set_title("PPC: same M8")
plt.tight_layout(); plt.savefig(f"{FIG}/20_posterior_predictive.png", dpi=130); plt.close()

with open(f"{TBL}/v5_joint_fit.csv", "w", newline="") as fp:
    w_ = csv.writer(fp); w_.writerow(["model", "frac", "neg2logL", "AIC", "BIC"])
    for name in results:
        r = results[name]
        w_.writerow([name, str(np.round(r["frac"],3).tolist()), round(r["n2ll"],1), round(r["aic"],1), round(r["bic"],1)])
    w_.writerow(["best", best_name, "", "", ""])
    w_.writerow(["pearson_chi2", round(pearson, 2), "", "", ""])
print("STEP 11-12 done.")
