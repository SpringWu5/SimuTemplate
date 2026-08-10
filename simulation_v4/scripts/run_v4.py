#!/usr/bin/env python3
"""run_v4.py -- STEP 1-4: IS generator validation, converged same-layer,
angular + geometry systematics, six-topology with uncertainties."""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "importance_sampling"))
import is_engine as E
FIG = os.path.join(ROOT, "figures"); TBL = os.path.join(ROOT, "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TBL, exist_ok=True)

SLAB_MIN = np.array([-10.0, -10.0, -1.0]); SLAB_MAX = np.array([10.0, 10.0, 1.0])
HX, HY, HZ = 1.0, 1.5, 1.5
DATA_TOPO = {"01": 78, "23": 57, "02": 52, "13": 25, "03": 25, "12": 18}   # V4 pure-2hit (~)
data_topo_frac = {t: DATA_TOPO[t] / sum(DATA_TOPO.values()) for t in E.TOPO}


def run(N, n=2.0, gap=10.0, L=10.0, dx=0.0, dy=0.0, conv="B", mT=0.7, mP=0.7, seed=1, **kw):
    rng = np.random.default_rng(seed)
    P0, d, th, ph, w = E.sample(N, n, rng, conv=conv, mT=mT, mP=mP, **kw)
    boxes = E.block_boxes(gap, L, HX, HY, HZ, dx, dy)
    hits, paths, hs, ps = E.propagate(P0, d, boxes, SLAB_MIN, SLAB_MAX)
    M, H, exc, inc = E.patterns(hits)
    return dict(theta=th, phi=ph, w=w, M=M, exc=exc, inc=inc, hits=hits, hslab=hs, pslab=ps)


def slfrac(r):
    m2 = (r["M"] == 2); W2 = r["w"][m2].sum()
    sel = m2 & (r["exc"]["01"] | r["exc"]["23"]); ws = r["w"][sel]
    f = ws.sum() / W2 if W2 else 0
    ess = ws.sum() ** 2 / (ws ** 2).sum() if ws.size else 0
    return f, ess, sel.sum()


# =================== STEP 1-2: validation (A/B/C) =====================
print("STEP 1-2: validation (3 methods, N=3e6)")
res = {}
for tag, kw in [("A_unbiased", dict(mT=1.0, mP=1.0, mX=0.0, mY=0.0)), ("B_IS", dict(mT=0.7, mP=0.7)),
                ("C_alt", dict(mT=0.5, mP=0.5, sig_phi=np.deg2rad(10.0), mX=0.5, mY=0.5))]:
    r = run(3_000_000, seed=7, **kw); res[tag] = r
    fr = E.weighted_fracs(r["w"], r["M"], r["exc"])
    sl, ess, n = slfrac(r)
    print(f"  {tag}: same_layer={sl:.4f}(ESS={ess:.0f},n={n})  " +
          " ".join(f"{t}={fr[t][0]:.3f}" for t in E.TOPO))

# proposal/weight diagnostics (method B)
rB = res["B_IS"]
fig, ax = plt.subplots(2, 3, figsize=(14, 7)); ax = ax.ravel()
ax[0].hist(rB["theta"] * 180 / np.pi, bins=90, density=True, alpha=.5, label="proposal")
wb = rB["w"] / rB["w"].sum() / (1 / 3e6)  # rough
ax[0].hist(rB["theta"] * 180 / np.pi, bins=90, weights=rB["w"], density=True, histtype="step", lw=1.5, label="weighted(target)")
ax[0].set_xlabel("theta(deg)"); ax[0].legend(fontsize=7); ax[0].set_title("theta: proposal vs weighted")
ax[1].hist(rB["phi"] * 180 / np.pi, bins=90, weights=rB["w"], density=True); ax[1].set_title("weighted phi")
ax[2].hist(np.log10(rB["w"] + 1e-30), bins=90); ax[2].set_title("log10(weight)")
ax[3].hist(rB["theta"][(rB["M"] == 2) & (rB["exc"]["01"] | rB["exc"]["23"])] * 180 / np.pi,
           weights=rB["w"][(rB["M"] == 2) & (rB["exc"]["01"] | rB["exc"]["23"])], bins=30)
ax[3].set_title("same-layer weighted theta")
ax[4].hist(rB["phi"][(rB["M"] == 2) & (rB["exc"]["01"] | rB["exc"]["23"])] * 180 / np.pi,
           weights=rB["w"][(rB["M"] == 2) & (rB["exc"]["01"] | rB["exc"]["23"])], bins=30)
ax[4].set_title("same-layer weighted phi")
m2 = rB["M"] == 2
ess_tot = rB["w"][m2].sum() ** 2 / (rB["w"][m2] ** 2).sum()
ax[5].text(0.1, 0.5, f"ESS(M2)={ess_tot:.0f}\nN(M2 raw)={m2.sum()}", fontsize=12)
ax[5].axis("off")
plt.tight_layout(); plt.savefig(f"{FIG}/01_is_diagnostics.png", dpi=130); plt.close()

# validation comparison bar
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(6); wd = 0.25
for k, tag in enumerate(["A_unbiased", "B_IS", "C_alt"]):
    fr = E.weighted_fracs(res[tag]["w"], res[tag]["M"], res[tag]["exc"])
    ax.bar(x + (k - 1) * wd, [fr[t][0] for t in E.TOPO], wd, label=tag, yerr=[fr[t][2] for t in E.TOPO], capsize=2)
ax.bar(x, [data_topo_frac[t] for t in E.TOPO], 0.05, color="k", label="data")
ax.set_xticks(x); ax.set_xticklabels(E.TOPO); ax.set_ylabel("P(topo|M2)"); ax.legend(fontsize=7)
ax.set_title("Validation: 3 sampling methods agree (within errs) vs data")
plt.tight_layout(); plt.savefig(f"{FIG}/02_validation.png", dpi=130); plt.close()

# =================== STEP 2b: high-stat same-layer =====================
print("\nSTEP 2b: high-stat same-layer (B_IS, N=1e7, 3 seeds)")
sl_seeds = []
for s in [11, 22, 33]:
    r = run(10_000_000, seed=s, mT=0.7, mP=0.7)
    sl, ess, n = slfrac(r); sl_seeds.append((sl, ess, n))
    print(f"  seed {s}: same_layer={sl:.4f} ESS={ess:.0f} raw_n={n}")
sl_mean = np.mean([x[0] for x in sl_seeds]); sl_ess = np.sum([x[1] for x in sl_seeds])
sl_relerr = 1 / np.sqrt(sl_ess)
print(f"  COMBINED: same_layer={sl_mean:.4f} ESS={sl_ess:.0f} relerr={sl_relerr:.3f}  (data=0.519)")

# =================== STEP 3: systematics =====================
print("\nSTEP 3a: angular model (n, conv A/B), gap=10,L=10")
ang = []
for n in [1.5, 2.0, 2.5, 3.0]:
    for conv in ["B", "A"]:
        r = run(4_000_000, n=n, conv=conv, seed=5)
        sl, ess, _ = slfrac(r); ang.append((n, conv, sl, ess))
        print(f"  n={n} conv{conv}: same_layer={sl:.4f} ESS={ess:.0f}")
print("\nSTEP 3b: geometry scan (n=2,convB): gap, Lsep, alignment")
geom = []
for gap in [8, 9, 10, 11, 12]:
    r = run(4_000_000, gap=gap, seed=9); sl, ess, _ = slfrac(r); geom.append(("gap", gap, sl, ess))
    print(f"  gap={gap}: sl={sl:.4f} ESS={ess:.0f}")
for L in [8, 9, 10, 11, 12]:
    r = run(4_000_000, L=L, seed=9); sl, ess, _ = slfrac(r); geom.append(("Lsep", L, sl, ess))
for d in [-2, -1, -0.5, 0.5, 1, 2]:
    r = run(4_000_000, dx=d, seed=9); sl, ess, _ = slfrac(r); geom.append(("xoff", d, sl, ess))
    r = run(4_000_000, dy=d, seed=9); sl, ess, _ = slfrac(r); geom.append(("yoff", d, sl, ess))

# =================== STEP 4: six-topology (nominal, with errs) =====================
print("\nSTEP 4: six-topology (n=2,convB,gap=10,L=10, N=1e7)")
rT = run(10_000_000, seed=44)
fr = E.weighted_fracs(rT["w"], rT["M"], rT["exc"])
print(f"{'topo':>5}{'MC':>9}{'relerr':>9}{'ESS':>9}{'data':>9}")
for t in E.TOPO:
    print(f"{t:>5}{fr[t][0]:9.4f}{fr[t][2]:9.3f}{fr[t][1]:9.0f}{data_topo_frac[t]:9.4f}")
sl_T, ess_T, _ = slfrac(rT)
print(f"same_layer(01+23) = {sl_T:.4f} ESS={ess_T:.0f}")

# ---- systematics figures ----
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot([a[0] for a in ang if a[1] == "B"], [a[2] for a in ang if a[1] == "B"], "o-", label="conv B (cos^n)")
ax[0].plot([a[0] for a in ang if a[1] == "A"], [a[2] for a in ang if a[1] == "A"], "s-", label="conv A (cos^(n+1))")
ax[0].axhline(0.519, color="k", ls=":", label="data 0.519"); ax[0].set_xlabel("n"); ax[0].set_ylabel("same-layer P"); ax[0].legend(fontsize=7); ax[0].set_title("same-layer vs angular model")
for key, mk in [("gap", "o"), ("Lsep", "s"), ("xoff", "^"), ("yoff", "v")]:
    g = [z for z in geom if z[0] == key]
    ax[1].plot([z[1] for z in g], [z[2] for z in g], mk + "-", label=key)
ax[1].axhline(0.519, color="k", ls=":"); ax[1].set_xlabel("parameter (cm)"); ax[1].set_ylabel("same-layer P"); ax[1].legend(fontsize=7); ax[1].set_title("same-layer vs geometry")
ax[2].bar(E.TOPO, [fr[t][0] for t in E.TOPO], yerr=[fr[t][2] for t in E.TOPO], capsize=3)
ax[2].scatter(E.TOPO, [data_topo_frac[t] for t in E.TOPO], color="k", zorder=5, label="data")
ax[2].set_ylabel("P(topo|M2)"); ax[2].set_title("corrected six-topology vs data"); ax[2].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/03_systematics_topology.png", dpi=130); plt.close()

# ---- tables ----
with open(f"{TBL}/v4_validation.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["method"] + E.TOPO + ["same_layer"])
    for tag in ["A_unbiased", "B_IS", "C_alt"]:
        fr = E.weighted_fracs(res[tag]["w"], res[tag]["M"], res[tag]["exc"])
        sl, _, _ = slfrac(res[tag])
        w.writerow([tag] + [f"{fr[t][0]:.4f}" for t in E.TOPO] + [f"{sl:.4f}"])
with open(f"{TBL}/v4_same_layer.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["metric", "value"]); w.writerow(["same_layer_fraction", f"{sl_mean:.4f}"])
    w.writerow(["ESS_combined", f"{sl_ess:.0f}"]); w.writerow(["rel_stat_error", f"{sl_relerr:.3f}"])
    w.writerow(["data", "0.519"]); w.writerow(["ratio_data_over_MC", f"{0.519/sl_mean:.1f}"])
with open(f"{TBL}/v4_systematics.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["vary", "param", "same_layer", "ESS"])
    for a in ang: w.writerow(["angular", f"n={a[0]}_{a[1]}", f"{a[2]:.4f}", f"{a[3]:.0f}"])
    for z in geom: w.writerow([z[0], z[1], f"{z[2]:.4f}", f"{z[3]:.0f}"])
with open(f"{TBL}/v4_topology.csv", "w", newline="") as fp:
    w = csv.writer(fp); w.writerow(["topo", "MC_frac", "rel_err", "ESS", "data_frac"])
    for t in E.TOPO: w.writerow([t, f"{fr[t][0]:.4f}", f"{fr[t][2]:.3f}", f"{fr[t][1]:.0f}", f"{data_topo_frac[t]:.4f}"])
print("\nSTEP 1-4 done. figures+tables in simulation_v4/.")
print(f"CORE RESULT: corrected same-layer = {sl_mean:.4f} +/- {sl_relerr*sl_mean:.4f} (ESS {sl_ess:.0f}), data 0.519, ratio {0.519/sl_mean:.1f}x")
