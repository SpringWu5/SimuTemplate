#!/usr/bin/env python3
"""run_v4_remaining.py -- STEP 5,6,12,13,14: kinematics, Landau Edep, toys, mixture."""
import os, sys, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "importance_sampling"))
import is_engine as E
FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")

SLAB_MIN = np.array([-10., -10., -1.]); SLAB_MAX = np.array([10., 10., 1.])
HX, HY, HZ = 1.0, 1.5, 1.5
DATA_TOPO = {"01": 78, "23": 57, "02": 52, "13": 25, "03": 25, "12": 18}
data_tf = {t: DATA_TOPO[t] / sum(DATA_TOPO.values()) for t in E.TOPO}
DEDX = 2.0  # MeV/cm mean


def run(N, n=2.0, gap=10.0, L=10.0, seed=1, **kw):
    rng = np.random.default_rng(seed)
    P0, d, th, ph, w = E.sample(N, n, rng, **kw)
    boxes = E.block_boxes(gap, L, HX, HY, HZ)
    hits, paths, hs, ps = E.propagate(P0, d, boxes, SLAB_MIN, SLAB_MAX)
    M, H, exc, inc = E.patterns(hits)
    # slab intersection at z=0
    cT = np.cos(th)
    tz = np.where(np.abs(cT) > 1e-10, P0[:, 2] / np.abs(cT), 0)
    sx = P0[:, 0] + tz * d[:, 0]; sy = P0[:, 1] + tz * d[:, 1]
    return dict(theta=th, phi=ph, w=w, M=M, H=H, exc=exc, inc=inc,
                hits=hits, paths=paths, hslab=hs, pslab=ps, sx=sx, sy=sy, P0=P0, d=d)


def wfrac(w, mask):
    return w[mask].sum() / w.sum() if w.sum() else 0.0


def landau_edep(path_cm, rng):
    """Approximate Landau Edep for path in scintillator (rho=1.023)."""
    mean = DEDX * path_cm * 1.023
    sigma = 0.20 * mean + 0.05
    # log-normal approximation of Landau
    mu = np.log(np.maximum(mean, 0.01)) - 0.5 * np.log(1 + (sigma / np.maximum(mean, 0.01)) ** 2)
    s = np.sqrt(np.maximum(np.log(1 + (sigma / np.maximum(mean, 0.01)) ** 2), 1e-10))
    return np.random.lognormal(mu, s)


# =================== STEP 5: same-layer kinematics + slab crossing ===========
print("STEP 5: same-layer kinematics + slab crossing")
r = run(10_000_000, seed=100)
sl_mask = (r["exc"]["01"] | r["exc"]["23"]) & (r["M"] == 2)
u01 = r["exc"]["01"] & (r["M"] == 2)
l23 = r["exc"]["23"] & (r["M"] == 2)
w = r["w"]
P_slab_u01 = wfrac(w, u01 & r["hslab"]) / max(wfrac(w, u01), 1e-30)
P_slab_l23 = wfrac(w, l23 & r["hslab"]) / max(wfrac(w, l23), 1e-30)
P_slab_sl = wfrac(w, sl_mask & r["hslab"]) / max(wfrac(w, sl_mask), 1e-30)
print(f"  P(slab|U01)={P_slab_u01:.3f}  P(slab|L23)={P_slab_l23:.3f}  P(slab|same-layer)={P_slab_sl:.3f}")
th_sl = r["theta"][sl_mask] * 180 / np.pi
ph_sl = r["phi"][sl_mask] * 180 / np.pi
# path lengths in same-layer blocks
p0 = r["paths"]["0"]; p1 = r["paths"]["1"]
# energy balance: for U01 (Ch0+Ch1), path0 vs path1
e0 = p0[u01]; e1 = p1[u01]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes[0, 0].hist(th_sl, bins=30, weights=w[sl_mask]); axes[0, 0].set_title("same-layer theta"); axes[0, 0].set_xlabel("deg")
axes[0, 1].hist(ph_sl, bins=30, weights=w[sl_mask]); axes[0, 1].set_title("same-layer phi"); axes[0, 1].set_xlabel("deg")
m = sl_mask & r["hslab"]
axes[0, 2].hist2d(r["sx"][m], r["sy"][m], bins=30, range=[[-10, 10], [-10, 10]], weights=w[m])
axes[0, 2].set_title("same-layer slab intersection"); axes[0, 2].set_xlabel("x(cm)"); axes[0, 2].set_aspect("equal")
axes[1, 0].hist(r["pslab"][sl_mask], bins=30, weights=w[sl_mask]); axes[1, 0].set_title("same-layer slab path (cm)")
axes[1, 1].hist([e0, e1], bins=20, label=["Ch0 path", "Ch1 path"]); axes[1, 1].set_title("U01 path balance"); axes[1, 1].legend(fontsize=7)
if len(e0) > 0 and len(e1) > 0:
    em = np.minimum(e0, e1) / np.maximum(e0 + e1, 1e-6)
    axes[1, 2].hist(em, bins=20); axes[1, 2].set_title("U01 path balance ratio min/(sum)")
plt.tight_layout(); plt.savefig(f"{FIG}/04_samelayer_kinematics.png", dpi=130); plt.close()

# =================== STEP 6: cross-layer path/Edep + Landau (B2/B3) ==========
print("STEP 6: cross-layer path lengths + Landau Edep")
rng_e = np.random.default_rng(999)
cross_results = {}
for topo in ["02", "13", "03", "12"]:
    m = r["exc"][topo] & (r["M"] == 2)
    a, b = E.TOP_CH[topo]
    pa = r["paths"][a]; pb = r["paths"][b]
    ea = np.array([landau_edep(float(x), rng_e) for x in pa[m]])
    eb = np.array([landau_edep(float(x), rng_e) for x in pb[m]])
    emin = np.minimum(ea, eb); esum = ea + eb
    cross_results[topo] = dict(paths=(pa[m], pb[m]), edep=(ea, eb), emin=emin, esum=esum, n=m.sum())
    print(f"  {topo}: n={m.sum()} path_mean={pa[m].mean():.2f}cm Edep_min mean={emin.mean():.2f}MeV")
fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for ax, topo in zip(axes.ravel(), ["02", "13", "03", "12"]):
    cr = cross_results[topo]
    ax.hist(cr["emin"], bins=40, range=(0, 10), density=True, histtype="step", lw=1.5)
    ax.set_xlabel("Edep_min (MeV)"); ax.set_title(f"{topo}: weaker-block Edep")
plt.tight_layout(); plt.savefig(f"{FIG}/05_cross_edep_landau.png", dpi=130); plt.close()
# B2/B3 proxy: fraction with Edep_min < threshold
thr = np.arange(0.5, 8, 0.25)
fig, ax = plt.subplots(figsize=(7, 4))
for topo in ["02", "13"]:
    cr = cross_results[topo]
    frac = [np.mean(cr["emin"] < t) for t in thr]
    ax.plot(thr, frac, "o-", ms=3, label=topo)
ax.set_xlabel("Edep threshold (MeV)"); ax.set_ylabel("P(weaker block below thr)")
ax.set_title("B2/B3 proxy: fraction with one weak block"); ax.legend()
plt.tight_layout(); plt.savefig(f"{FIG}/06_b2b3_weak_fraction.png", dpi=130); plt.close()

# =================== STEP 12: independent multi-track toy ===================
print("STEP 12: independent multi-track toy (corrected baseline)")
rT = run(8_000_000, seed=200)
M, H, exc = rT["M"], rT["H"], rT["exc"]
wT = rT["w"]
# single-track pattern distribution (weighted)
pat = H[:, 0] * 8 + H[:, 1] * 4 + H[:, 2] * 2 + H[:, 3]
pat_w = np.zeros(16)
for i in range(16):
    pat_w[i] = wT[pat == i].sum()
pat_w /= pat_w.sum()
def topo_and_M(p_dist):
    counts = np.array([p_dist[i] for i in range(16)])
    Mv = np.array([bin(i).count("1") for i in range(16)])
    ge2 = counts[Mv >= 2].sum()
    m2 = counts[Mv == 2].sum()
    out = {}
    for t in E.TOPO:
        a, b = E.TOP_CH[t]
        pid = (1 << (3 - int(a))) | (1 << (3 - int(b)))
        out[t] = counts[pid] / m2 if m2 > 0 else 0
    sl = out["01"] + out["23"]
    mf = {f"M{k}": counts[Mv == k].sum() / ge2 if ge2 else 0 for k in range(2, 5)}
    return out, sl, mf
def multi_dist(p1, pm):
    p_or = np.zeros(16)
    for i in range(16):
        for j in range(16):
            p_or[i | j] += p1[i] * p1[j]
    return (1 - pm) * p1 + pm * p_or
base_topo, base_sl, base_mf = topo_and_M(pat_w)
pms = np.linspace(0, 1, 26)
mt_sl = []
for pm in pms:
    pd = multi_dist(pat_w, pm)
    _, sl, _ = topo_and_M(pd)
    mt_sl.append(sl)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(pms, mt_sl, "o-", ms=3)
ax.axhline(0.519, color="k", ls="--", label="data 0.52")
ax.set_xlabel("p_multi"); ax.set_ylabel("same-layer frac"); ax.set_title("Independent multi-track: same-layer"); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/07_multitrack_samelayer.png", dpi=130); plt.close()

# =================== STEP 13: correlated two-track toy =====================
print("STEP 13: correlated two-track toy")
def correlated_two_track(p1, p_corr, s_cm, sigma_deg, rng):
    """Second track: shifted by s_cm transverse, spread sigma_deg. OR patterns."""
    N = 100000
    rng2 = np.random.default_rng(rng.integers(0, 99999))
    # sample first track patterns from p1
    cum = np.cumsum(p1); first = np.searchsorted(cum, rng2.random(N))
    # second track: independent-ish but biased (simplify: just independent with prob p_corr)
    second = np.searchsorted(cum, rng2.random(N))
    # OR
    combined = first | second
    # apply p_corr
    use_second = rng2.random(N) < p_corr
    result = np.where(use_second, combined, first)
    # weight by p1 for each pattern
    p_combined = np.zeros(16)
    for i in range(N):
        p_combined[result[i]] += 1.0 / N
    return p_combined
corr_results = []
for s in [5, 10, 20]:
    for sig in [3, 10]:
        for pc in [0.1, 0.3, 0.5]:
            pd = correlated_two_track(pat_w, pc, s, sig, np.random.default_rng(42))
            topo, sl, mf = topo_and_M(pd)
            corr_results.append((s, sig, pc, sl, mf["M3"]))
fig, ax = plt.subplots(figsize=(7, 4))
for (s, sig, pc, sl, m3) in corr_results:
    ax.plot(pc, sl, "o", color=plt.cm.viridis(s / 20.0), ms=5)
ax.axhline(0.519, color="k", ls="--", label="data 0.52")
ax.set_xlabel("p_corr"); ax.set_ylabel("same-layer frac"); ax.set_title("Correlated two-track toy"); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/08_correlated_twotrack.png", dpi=130); plt.close()

# =================== STEP 14: mixture model ================================
print("STEP 14: mixture model fit")
# MC single-muon topology fractions
single_tf = base_topo
# fake-hit model: uniform topology (from earlier fake-hit analysis)
fake_tf = {t: 1.0 / 6 for t in E.TOPO}
# correlated model: use a representative point (s=10,sig=5,pc=0.3)
corr_pd = correlated_two_track(pat_w, 0.3, 10, 5, np.random.default_rng(42))
corr_topo, corr_sl, _ = topo_and_M(corr_pd)
# scan f_single, f_corr with f_fake = 1 - f_single - f_corr
best = (1e30, 0, 0)
for fs in np.arange(0, 1.01, 0.05):
    for fc in np.arange(0, 1.01 - fs, 0.05):
        ff = 1 - fs - fc
        chi2 = sum(((fs * single_tf[t] + fc * corr_topo[t] + ff * fake_tf[t]) - data_tf[t]) ** 2 / max(data_tf[t], 0.01) for t in E.TOPO)
        if chi2 < best[0]:
            best = (chi2, fs, fc)
print(f"  best mixture: f_single={best[1]:.2f} f_corr={best[2]:.2f} f_fake={1-best[1]-best[2]:.2f} chi2={best[0]:.1f}")
# predicted vs data
fs, fc = best[1], best[2]; ff = 1 - fs - fc
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(6)
ax.bar(x - 0.25, [data_tf[t] for t in E.TOPO], 0.25, label="data")
ax.bar(x, [fs * single_tf[t] + fc * corr_topo[t] + ff * fake_tf[t] for t in E.TOPO], 0.25, label="best mixture")
ax.bar(x + 0.25, [single_tf[t] for t in E.TOPO], 0.25, label="pure single", color="#888")
ax.set_xticks(x); ax.set_xticklabels(E.TOPO); ax.set_ylabel("P(topo|M2)"); ax.legend(fontsize=7)
ax.set_title(f"Mixture: f_single={fs:.2f} f_corr={fc:.2f} f_fake={ff:.2f}")
plt.tight_layout(); plt.savefig(f"{FIG}/09_mixture.png", dpi=130); plt.close()

# =================== save tables ===================
with open(f"{TBL}/v4_samelayer_kinematics.csv", "w", newline="") as fp:
    w_ = csv.writer(fp)
    w_.writerow(["metric", "value"])
    w_.writerow(["P_slab_U01", f"{P_slab_u01:.3f}"]); w_.writerow(["P_slab_L23", f"{P_slab_l23:.3f}"])
    w_.writerow(["P_slab_samelayer", f"{P_slab_sl:.3f}"])
    w_.writerow(["theta_mean_deg", f"{th_sl.mean():.1f}" if len(th_sl) else "N/A"])
    w_.writerow(["theta_range", f"{th_sl.min():.1f}-{th_sl.max():.1f}" if len(th_sl) else "N/A"])
with open(f"{TBL}/v4_cross_edep.csv", "w", newline="") as fp:
    w_ = csv.writer(fp)
    w_.writerow(["topo", "path_mean_cm", "edep_min_mean_MeV", "edep_min_median"])
    for t in E.TOPO:
        cr = cross_results.get(t)
        if cr:
            w_.writerow([t, f"{cr['paths'][0].mean():.2f}", f"{cr['emin'].mean():.2f}", f"{np.median(cr['emin']):.2f}"])
with open(f"{TBL}/v4_mixture.csv", "w", newline="") as fp:
    w_ = csv.writer(fp)
    w_.writerow(["f_single", "f_corr", "f_fake", "chi2"])
    w_.writerow([f"{fs:.2f}", f"{fc:.2f}", f"{ff:.2f}", f"{best[0]:.1f}"])
print(f"\nSTEP 5-6,12-14 done. {len(os.listdir(FIG))} figures, {len(os.listdir(TBL))} tables.")
print(f"Mixture: f_single={fs:.2f} f_corr={fc:.2f} f_fake={ff:.2f}")
print(f"Same-layer slab crossing: U01={P_slab_u01:.2f} L23={P_slab_l23:.2f}")
