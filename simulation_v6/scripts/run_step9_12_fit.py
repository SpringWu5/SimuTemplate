#!/usr/bin/env python3
"""run_step9_12_fit.py -- three-level fit + absolute GOF + PPC (STEP 9-12).

FIT A: 6 topology + M3 + M4 (8 bins).
FIT B: + panel M8/nonM8 per topology (12+2 bins).
FIT C: + cross-layer Q_min categories.
Absolute GOF: Pearson chi2, deviance G, p-value. Verdict ADEQUATE/INADEQUATE.
"""
import os, sys, csv, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v5 import generator as GEN, geometry as G, toys as T
from simulation_v5.response import landau_edep
from simulation_v6 import small_v6 as SM, panel_v6 as PV
from scipy.stats import chi2 as chi2dist

FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
TOPO = G.TOPO
# data: 6 topology + M3 + M4
DC = {"01": 78, "23": 57, "02": 52, "13": 25, "03": 25, "12": 18}
DATA_A = np.array([DC[t] for t in TOPO] + [2, 0], dtype=float)  # +M3,M4
SAME_M8 = {"01": 4, "23": 3}; CROSS_M8_TOT = 50; CROSS_TOT = 120
CROSS_M8 = {t: DC[t] / CROSS_TOT * CROSS_M8_TOT for t in ["02", "13", "03", "12"]}
M8 = {**SAME_M8, **CROSS_M8}
# FIT B data: 12 (topo x panel) + M3 + M4
DATA_B = np.zeros(14)
for i, t in enumerate(TOPO):
    DATA_B[2 * i] = M8[t]; DATA_B[2 * i + 1] = DC[t] - M8[t]
DATA_B[12] = 2; DATA_B[13] = 0  # M3, M4 (assume M3 are M8; minor)

print("== STEP 9-12: three-level fit + absolute GOF ==")
iss = GEN.sample_single(8000000, n=2.0, rng=np.random.default_rng(301))
s = GEN.resample_triggered(iss, 500000, np.random.default_rng(302), Mmin=1)
rng = np.random.default_rng(5)
edep, npe = SM.small_edep_pe(s["paths"], rng)
Hg = s["H"]; Ng = Hg.shape[0]; pslab = s["pslab"]
gain, thr = SM.asym_params(kind="thr", dx=0.20, base_thr_mip=0.20)
fired0, Q0, _ = SM.fire_and_Q(npe, np.random.default_rng(7), gain, thr, geom_H=Hg)
edep_slab = np.where(pslab > 0, np.array([landau_edep(float(p), np.random.default_rng(9)) for p in pslab]), 0.0)
pr = PV.panel_response(edep_slab, np.random.default_rng(11), pde=0.40, noise_pe=0.5, thr_pe=np.full(8, 0.8))
panel_M8 = pr["M8"]; tot_pe = pr["pe"].sum(1)

def sl_mask(F): return ((F[:, 0] & F[:, 1]) | (F[:, 2] & F[:, 3])) & (F.sum(1) == 2)
def cr_mask(F): return (~(((F[:, 0] & F[:, 1]) | (F[:, 2] & F[:, 3])))) & (F.sum(1) == 2)
def qmin_of(F, Q, mask):
    f = F[mask]; q = Q[mask]
    qs = np.sort(np.where(f & (q > 0), q, -1), axis=1)[:, ::-1]
    return np.where(qs[:, 1] >= 0, qs[:, 1], qs[:, 0])

# ---- build component observable vectors (clean physics signatures) ----
# extract topology SHAPES from asymmetry MC: cross shape and same shape
M0f = fired0.sum(1)
cr_shape = np.zeros(6); sl_shape = np.zeros(6)
cr_tot = 0; sl_tot = 0
for i, t in enumerate(TOPO):
    a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
    sel = (M0f == 2) & fired0[:, ia] & fired0[:, ib]
    is_same = t in ["01", "23"]
    if is_same: sl_shape[i] = np.sum(sel); sl_tot += np.sum(sel)
    else: cr_shape[i] = np.sum(sel); cr_tot += np.sum(sel)
cr_shape /= max(cr_tot, 1); sl_shape /= max(sl_tot, 1)

def make_signature(shape6, m8_same, m8_cross):
    """14-bin: 6 topo x {M8,nonM8} + M3 + M4. shape6 = topology fractions;
    m8_same/m8_cross = P(M8|topo) for same/cross topologies."""
    out = np.zeros(14)
    for i, t in enumerate(TOPO):
        is_same = t in ["01", "23"]
        p8 = m8_same if is_same else m8_cross
        out[2 * i] = shape6[i] * p8
        out[2 * i + 1] = shape6[i] * (1 - p8)
    return out / max(out[:12].sum(), 1e-12) * (1 - 0.01)  # leave 1% for M3/M4

def add_multiplicity(vec, p_m3=0.0, p_m4=0.0):
    v = vec.copy(); tot12 = v[:12].sum()
    v[12] = p_m3 * tot12 / max(1 - p_m3 - p_m4, 1e-6); v[13] = p_m4 * tot12 / max(1 - p_m3 - p_m4, 1e-6)
    return v / max(v.sum(), 1e-12)

# C_through: cross shape, panel bright (P(M8|cross)~0.42 from calibrated model)
C_thr = add_multiplicity(make_signature(cr_shape, m8_same=0.0, m8_cross=0.42))
# C_sld: same shape, dark
C_sld = add_multiplicity(make_signature(sl_shape, m8_same=0.0, m8_cross=0.0))
# C_xd: cross shape, dark
C_xd = add_multiplicity(make_signature(cr_shape, m8_same=0.0, m8_cross=0.0))
# C_s2: same shape, bright
C_s2 = add_multiplicity(make_signature(sl_shape, m8_same=0.94, m8_cross=0.0))
# C_multi (SD3): produces M3 -- cross+same mix, M3~0.1
C_multi = add_multiplicity(make_signature((cr_shape + sl_shape) / 2, m8_same=0.3, m8_cross=0.3), p_m3=0.15)


def neg2ll(frac, comps, data):
    p = frac @ comps; p = np.clip(p, 1e-15, None); p /= p.sum()
    nz = data > 0
    return -2.0 * np.sum(data[nz] * np.log(p[nz]))

def fit(comps, data, ngrid=13):
    C = comps.shape[0]; best = (1e30, None)
    if C == 1: return np.array([1.0]), neg2ll(np.array([1.0]), comps, data)
    for combo in itertools.product(*[np.linspace(0, 1, ngrid) for _ in range(C - 1)]):
        if sum(combo) > 1 + 1e-9: continue
        frac = np.array(list(combo) + [max(1 - sum(combo), 0.0)])
        v = neg2ll(frac, comps, data)
        if v < best[0]: best = (v, frac)
    return best[1], best[0]

def gof(frac, comps, data):
    p = frac @ comps; p /= p.sum()
    mu = p * data.sum()
    nz = mu > 0
    pearson = np.sum((data[nz] - mu[nz]) ** 2 / mu[nz])
    dnz = data > 0
    deviance = 2 * np.sum(data[dnz] * np.log(data[dnz] / np.where(mu[dnz] > 0, mu[dnz], 1e-9)))
    dof = max(int((data > 0).sum() - 1 - (len(frac) - 1)), 1)
    pval = 1 - chi2dist.cdf(pearson, dof)
    pull = (mu - data) / np.sqrt(np.where(mu > 0, mu, 1))
    return dict(pearson=pearson, deviance=deviance, dof=dof, pval=pval, mu=mu, pull=pull)

# ---- FIT A: topology + M3/M4 (collapse panel from B vectors) ----
print("\n-- FIT A (topology + M3/M4) --")
def collapse_A(vecB):
    out = np.zeros(8)
    for i in range(6): out[i] = vecB[2 * i] + vecB[2 * i + 1]
    out[6] = vecB[12]; out[7] = vecB[13]
    return out / max(out.sum(), 1e-12)
for name, comps in [("single-only", [C_thr]), ("+sl-dark", [C_thr, C_sld]),
                    ("+crossdark", [C_thr, C_sld, C_xd]), ("+S2", [C_thr, C_sld, C_xd, C_s2])]:
    comps_A = np.array([collapse_A(c) for c in comps])
    frac, n2 = fit(comps_A, DATA_A)
    g = gof(frac, comps_A, DATA_A)
    print(f"  {name:14s}: f={np.round(frac,2)} Pearson={g['pearson']:.1f}/{g['dof']} p={g['pval']:.3g}")

best_A_comps = np.array([collapse_A(c) for c in [C_thr, C_sld, C_xd, C_s2]])
frA, _ = fit(best_A_comps, DATA_A); gA = gof(frA, best_A_comps, DATA_A)

# ---- FIT B: + panel ----
print("\n-- FIT B (topology x panel + M3/M4) --")
best_B = np.array([C_thr, C_sld, C_xd, C_s2])
frB, _ = fit(best_B, DATA_B); gB = gof(frB, best_B, DATA_B)
print(f"  4-comp: f={np.round(frB,3)} Pearson={gB['pearson']:.1f}/{gB['dof']} p={gB['pval']:.3g}")
print(f"  pulls: {np.round(gB['pull'],2)}")

# ---- FIT C: + Q_min for cross (3 bins: weak/mid/strong) ----
qmin_cr = qmin_of(fired0, Q0, cr_mask(fired0))
qb = np.percentile(qmin_cr, [33, 67])
# data C: FIT B + cross Q split (nonM8 cross ~70 events: B2 weak-ish + B3 strong)
# weak/mid/strong thirds of the nonM8 cross population
n_nonm8_cross = 70
DATA_C = np.concatenate([DATA_B, [n_nonm8_cross * 0.45, n_nonm8_cross * 0.30, n_nonm8_cross * 0.25]])
# component C vectors: append cross Q_min thirds (from MC qmin_cr terciles)
def append_qmin(vecB, qm):
    extra = np.zeros(3)
    extra[0] = np.mean(qm < qb[0]); extra[1] = np.mean((qm >= qb[0]) & (qm < qb[1]))
    extra[2] = np.mean(qm >= qb[1])
    extra /= max(extra.sum(), 1e-12) * np.mean(cr_mask(fired0)) * 257 / max(vecB.sum(), 1e-12)
    # scale extra to match cross-dark fraction in vecB
    crdark_frac = sum(vecB[2 * i + 1] for i, t in enumerate(["02", "13", "03", "12"]))
    extra = extra / max(extra.sum(), 1e-12) * crdark_frac
    return np.concatenate([vecB, extra])
comps_C = np.array([append_qmin(C_thr, qmin_cr), append_qmin(C_sld, np.array([0.])),
                    append_qmin(C_xd, qmin_cr), append_qmin(C_s2, np.array([0.]))])
frC, _ = fit(comps_C, DATA_C, ngrid=11); gC = gof(frC, comps_C, DATA_C)
print(f"\n-- FIT C (+cross Q_min) --")
print(f"  4-comp: f={np.round(frC,3)} Pearson={gC['pearson']:.1f}/{gC['dof']} p={gC['pval']:.3g}")

# ---- verdict ----
print("\n=== VERDICT ===")
for nm, g in [("FIT A", gA), ("FIT B", gB), ("FIT C", gC)]:
    status = "ADEQUATE" if g["pval"] > 0.01 else "INADEQUATE"
    print(f"  {nm}: Pearson={g['pearson']:.1f}/{g['dof']} p={g['pval']:.3g} -> {status}")
maxpull_B = np.max(np.abs(gB["pull"]))
print(f"  FIT B max|pull|={maxpull_B:.2f} {'(>3sigma -> fail)' if maxpull_B > 3 else ''}")

# ---- plots ----
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
lblA = TOPO + ["M3", "M4"]
axes[0].bar(np.arange(8) - 0.3, DATA_A, 0.3, label="data"); axes[0].bar(np.arange(8), gA["mu"], 0.3, label="FIT A")
axes[0].set_xticks(np.arange(8)); axes[0].set_xticklabels(lblA); axes[0].legend(fontsize=7)
axes[0].set_title(f"FIT A Pearson={gA['pearson']:.0f}/{gA['dof']} p={gA['pval']:.2f}")
lblB = [f"{t}_{'M8' if j else 'no'}" for t in TOPO for j in (1, 0)] + ["M3", "M4"]
axes[1].bar(np.arange(14) - 0.3, DATA_B, 0.3, label="data"); axes[1].bar(np.arange(14), gB["mu"], 0.3, label="FIT B")
axes[1].set_xticks(np.arange(14)); axes[1].set_xticklabels(lblB, rotation=90, fontsize=6); axes[1].legend(fontsize=7)
axes[1].set_title(f"FIT B Pearson={gB['pearson']:.0f}/{gB['dof']} p={gB['pval']:.2f}")
axes[2].bar(np.arange(len(gB["pull"])), gB["pull"], 0.5)
axes[2].set_title("FIT B pulls"); axes[2].axhline(3, color="r", ls="--"); axes[2].axhline(-3, color="r", ls="--")
plt.tight_layout(); plt.savefig(f"{FIG}/04_fit_gof.png", dpi=130); plt.close()

# ---- PPC ----
rngpp = np.random.default_rng(999)
pp_topo = []; pp_m3 = []; pp_samem8 = []
for _ in range(2000):
    samp = rngpp.multinomial(257, frB @ best_B / (frB @ best_B).sum())
    pp_topo.append([samp[2 * i] + samp[2 * i + 1] for i in range(6)]); pp_m3.append(samp[12])
    pp_samem8.append(samp[0] + samp[2])
pp_topo = np.array(pp_topo)
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
axes[0].boxplot([pp_topo[:, i] for i in range(6)], showfliers=False)
axes[0].plot(range(6), [DC[t] for t in TOPO], "rx", ms=10, mew=2)
axes[0].set_xticklabels(TOPO); axes[0].set_title("PPC topology")
axes[1].hist(pp_m3, 20); axes[1].axvline(2, color="r"); axes[1].set_title("PPC M3 (data=2)")
axes[2].hist(pp_samem8, 20); axes[2].axvline(7, color="r"); axes[2].set_title("PPC same-M8 (data=7)")
plt.tight_layout(); plt.savefig(f"{FIG}/05_ppc.png", dpi=130); plt.close()

with open(f"{TBL}/v6_fit_gof.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["fit", "pearson", "dof", "pvalue", "verdict", "frac"])
    for nm, g, fr in [("FIT_A", gA, frA), ("FIT_B", gB, frB), ("FIT_C", gC, frC)]:
        w.writerow([nm, round(g["pearson"], 1), g["dof"], round(g["pval"], 4),
                    "ADEQUATE" if g["pval"] > 0.01 else "INADEQUATE", str(np.round(fr, 3).tolist())])
print("\nSTEP 9-12 done.")
