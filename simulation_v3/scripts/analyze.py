#!/usr/bin/env python3
"""
analyze.py -- Phase-3 acceptance/topology/slab/energy analysis.

Reads processed/summary.json (all n,L scans) + processed/triggered_n*_L10.npz
(focused triggered records), produces figures under figures/ and tables under
tables/. Compares single-muon MC topology structure to the experimental targets.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "processed")
FIG = os.path.join(ROOT, "figures")
TBL = os.path.join(ROOT, "tables")
os.makedirs(TBL, exist_ok=True)

# ---- experimental targets (from the task prompt; "about" values) ----
DATA_M = {"M2": 260, "M3": 2, "M4": 0}                      # 262 events, all trigger (>=2)
DATA_TOPO = {"01": 78, "23": 57, "02": 56, "13": 25, "03": 25, "12": 19}  # 2-hit counts
TOPO = ["01", "23", "02", "13", "03", "12"]
TOPO_KIND = {"01": "same-layer", "23": "same-layer",
             "02": "cross same-side", "13": "cross same-side",
             "03": "cross diagonal", "12": "cross diagonal"}
data_topo_frac = {t: DATA_TOPO[t] / sum(DATA_TOPO.values()) for t in TOPO}
data_M_tot = sum(DATA_M.values())
data_M_frac = {k: v / data_M_tot for k, v in DATA_M.items()}


def g_test(obs, exp):
    """G-test (likelihood-ratio chi2) on counts; obs,exp arrays."""
    obs = np.asarray(obs, float); exp = np.asarray(exp, float)
    m = exp > 0
    return 2.0 * np.nansum(obs[m] * np.log(obs[m] / exp[m]))


summary = json.load(open(os.path.join(PROC, "summary.json")))


# ============================================================= topology vs data
def topo_table():
    rows = []
    for r in summary:
        n, L = r["n"], r["L"]
        c = r["topology_M2_counts"]
        tot = sum(c.values())
        f = {t: (c[t] / tot if tot else 0.0) for t in TOPO}
        # expected counts under MC fractions vs data total (260) for G-test
        exp = np.array([f[t] * 260 for t in TOPO])
        obs = np.array([data_topo_frac[t] * 260 for t in TOPO])
        g = g_test(obs, exp) if tot else float("nan")
        sl = f["01"] + f["23"]
        rows.append(dict(n=n, L=L, tot_M2=tot, same_layer_frac=sl, G=g, **{t: f[t] for t in TOPO}))
    return rows


rows = topo_table()
import csv
with open(os.path.join(TBL, "topology_vs_data.csv"), "w", newline="") as fp:
    w = csv.writer(fp)
    w.writerow(["n", "L", "M2_count", "01", "23", "02", "13", "03", "12",
                "same_layer_frac", "G_test_vs_data"])
    for r in rows:
        w.writerow([r["n"], r["L"], r["tot_M2"], *(f"{r[t]:.4f}" for t in TOPO),
                    f"{r['same_layer_frac']:.4f}", f"{r['G']:.2f}"])

# nominal scan over n at L=10
nom = [r for r in rows if abs(r["L"] - 10) < 1e-6]
# ---- Fig: 6-topology fractions, MC(n,L=10) vs data ----
fig, ax = plt.subplots(figsize=(8, 4.2))
x = np.arange(6)
ax.bar(x - 0.2, [data_topo_frac[t] for t in TOPO], 0.4, label="data", color="#444")
for k, r in enumerate(nom):
    ax.bar(x + (k - 1) * 0.13, [r[t] for t in TOPO], 0.12,
           label=f"MC n={r['n']:.1f}")
ax.set_xticks(x); ax.set_xticklabels(TOPO)
ax.set_ylabel("fraction of 2-hit events")
ax.set_title("2-hit topology fractions: data vs single-muon MC (L=10 cm)")
ax.legend(fontsize=7, ncol=3); ax.set_yscale("log"); ax.set_ylim(1e-5, 1)
plt.tight_layout(); plt.savefig(f"{FIG}/topology/07_topology_fractions_log.png", dpi=150); plt.close()

# ---- Fig: same-layer fraction vs n and L ----
fig, ax = plt.subplots(figsize=(7, 4))
for n in sorted(set(r["n"] for r in rows)):
    rr = sorted([r for r in rows if r["n"] == n], key=lambda z: z["L"])
    ax.plot([z["L"] for z in rr], [z["same_layer_frac"] for z in rr], "o-", label=f"n={n:.1f}")
ax.axhline(data_topo_frac["01"] + data_topo_frac["23"], color="k", ls="--",
           label=f"data = {data_topo_frac['01']+data_topo_frac['23']:.2f}")
ax.set_xlabel("layer separation (cm)"); ax.set_ylabel("same-layer 2-hit fraction (01+23)")
ax.set_title("Single-muon same-layer fraction vs geometry (MC ~ 0)")
ax.set_ylim(-0.02, 0.6); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/topology/08_same_layer_frac.png", dpi=150); plt.close()

# ---- Fig: M2/M3/M4 fractions vs n (L=10) vs data ----
fig, ax = plt.subplots(figsize=(7, 4))
width = 0.25
mk = ["M2", "M3", "M4"]
data_mf = [data_M_frac[k] for k in mk]
ax.bar(np.arange(3) - width, data_mf, width, label="data", color="#444")
for k, n in enumerate(sorted(set(r["n"] for r in summary))):
    r = next(rr for rr in summary if rr["n"] == n and abs(rr["L"] - 10) < 1e-6)
    mc = [r["M_counts"][k] / max(1, sum(r["M_counts"].values())) for k in mk]
    ax.bar(np.arange(3) + (k - 1) * width * 0.5, mc, width * 0.5, label=f"MC n={n:.1f}")
ax.set_yscale("symlog", linthresh=1e-4); ax.set_ylim(0, 1.2)
ax.set_xticks(range(3)); ax.set_xticklabels(mk)
ax.set_ylabel("fraction of triggered (M>=2) events")
ax.set_title("Trigger multiplicity: data vs single-muon MC (L=10)")
ax.legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{FIG}/topology/09_multiplicity.png", dpi=150); plt.close()

# ============================================================= slab crossing
def slab_table():
    out = []
    for r in summary:
        for t in TOPO:
            ps = r["slab_cross"][t]
            out.append(dict(n=r["n"], L=r["L"], topo=t, kind=TOPO_KIND[t],
                            P_slab_inc=ps["P_slab_inc"], P_slab_exc=ps["P_slab_exc"],
                            n_inc=ps["n_inc"], n_exc=ps["n_exc"]))
    return out


sl = slab_table()
with open(os.path.join(TBL, "slab_crossing_by_topology.csv"), "w", newline="") as fp:
    w = csv.writer(fp)
    w.writerow(["n", "L", "topology", "kind", "P_slab_inclusive", "P_slab_exclusive", "n_inc", "n_exc"])
    for r in sl:
        w.writerow([r["n"], r["L"], r["topo"], r["kind"],
                    f"{r['P_slab_inc']:.4f}", f"{r['P_slab_exc']:.4f}", r["n_inc"], r["n_exc"]])

# ---- Fig: P(slab crossed | topology) at n=2,L=10 ----
r10 = next(r for r in summary if r["n"] == 2.0 and abs(r["L"] - 10) < 1e-6)
fig, ax = plt.subplots(figsize=(7, 4))
inc = [r10["slab_cross"][t]["P_slab_inc"] for t in TOPO]
exc = [r10["slab_cross"][t]["P_slab_exc"] for t in TOPO]
ax.bar(np.arange(6) - 0.2, inc, 0.4, label="inclusive (>=pair)", color="#4C72B0")
ax.bar(np.arange(6) + 0.2, exc, 0.4, label="exclusive (M=2)", color="#C44E52")
ax.set_xticks(range(6)); ax.set_xticklabels(TOPO)
ax.set_ylabel("P(slab crossed | topology)"); ax.set_ylim(0, 1.05)
ax.set_title("Slab crossing probability by topology (single muon, n=2, L=10)")
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/acceptance/13_slab_cross_prob.png", dpi=150); plt.close()

# ============================================================= focused triggered records
def load_trig(n):
    return np.load(os.path.join(PROC, f"triggered_n{n:.1f}_L10.npz"), allow_pickle=True)


D = load_trig(2.0)
theta = D["theta"] * 180 / np.pi
phi = D["phi"] * 180 / np.pi
hslab = D["hslab"]; sx = D["sx"]; sy = D["sy"]
pslab = D["pslab"]

def mask(topo, kind="exc"):
    return D[f"{kind}_{topo}"] == 1

# ---- accepted theta/phi (generated vs triggered) ----
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(theta, bins=40, histtype="step", lw=1.5, density=True, label="triggered (M>=2)")
ax.set_xlabel("zenith theta (deg)"); ax.set_ylabel("a.u.")
ax.set_title("Accepted zenith distribution (single muon, n=2, L=10)")
ax.legend()
plt.tight_layout(); plt.savefig(f"{FIG}/acceptance/05_accepted_theta.png", dpi=150); plt.close()

# ---- same-layer vs cross-layer theta (cross-layer from 02+13; same-layer empty) ----
fig, ax = plt.subplots(figsize=(6, 4))
cross = mask("02", "inc") | mask("13", "inc") | mask("03", "inc") | mask("12", "inc")
ax.hist(theta[cross], bins=30, histtype="step", lw=1.5, density=True, label="cross-layer (02/13/03/12)")
ax.hist(theta[mask("01", "inc") | mask("23", "inc")], bins=30, histtype="step", lw=1.5,
        label="same-layer (01/23)  [EMPTY in MC]")
ax.set_xlabel("zenith theta (deg)"); ax.set_ylabel("a.u.")
ax.set_title("Same-layer vs cross-layer theta (single muon)")
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/topology/10_same_vs_cross_theta.png", dpi=150); plt.close()

# ---- slab intersection heatmaps per cross topology ----
fig, axes = plt.subplots(1, 4, figsize=(16, 3.6))
for ax, t in zip(axes, ["02", "13", "03", "12"]):
    m = mask(t, "inc") & hslab
    if m.sum():
        ax.hist2d(sx[m], sy[m], bins=30, range=[[-10, 10], [-10, 10]], cmap="viridis")
        ax.set_title(f"T{t[0]}{t[1]}  (n={m.sum()})")
    else:
        ax.set_title(f"T{t[0]}{t[1]} (none)")
    ax.set_xlabel("slab x (cm)"); ax.set_ylabel("slab y (cm)"); ax.set_aspect("equal")
plt.tight_layout(); plt.savefig(f"{FIG}/acceptance/14-17_slab_heatmaps.png", dpi=150); plt.close()

# ---- slab path length distribution ----
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(pslab[hslab] * 2.05, bins=40, histtype="step", lw=1.5)
ax.set_xlabel("slab Edep proxy (MeV)"); ax.set_ylabel("triggered events")
ax.set_title("Slab energy deposit (proxy) for slab-crossing triggered muons")
plt.tight_layout(); plt.savefig(f"{FIG}/acceptance/18_slab_pathlen.png", dpi=150); plt.close()

# ============================================================= energy / clipping proxy
DEDX = 2.05  # MeV/cm (MIP in EJ-200, rho=1.023)
def block_edep(i):
    return D[f"path{i}"] * DEDX

# small-block Edep distribution by topology (sum of the two hit blocks)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, (t, ia, ib) in zip(axes, [("02", 0, 2), ("13", 1, 3)]):
    m = mask(t, "inc")
    e = block_edep(ia) + block_edep(ib)
    ax.hist(e[m], bins=30, histtype="step", lw=1.5)
    ax.set_xlabel(f"summed small-block Edep proxy (MeV)  [{t}]"); ax.set_ylabel("events")
    ax.set_title(f"Small-block energy deposit, topology {t}")
plt.tight_layout(); plt.savefig(f"{FIG}/energy/19-20_small_edep_by_topo.png", dpi=150); plt.close()

# clipping proxy: max single-block Edep; scan saturation threshold
emax = np.maximum.reduce([block_edep(i) for i in range(4)])
fig, ax = plt.subplots(figsize=(7, 4))
thr = np.arange(3, 12, 0.5)
for t, lab in [("02", "cross 02"), ("13", "cross 13")]:
    m = mask(t, "inc")
    frac = [np.mean(emax[m] > T) for T in thr]
    ax.plot(thr, frac, "o-", label=lab)
ax.set_xlabel("small-block saturation threshold (MeV proxy)")
ax.set_ylabel("clipped fraction")
ax.set_title("Clipping proxy vs threshold by topology (single muon)")
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/energy/23_clipping_vs_topo.png", dpi=150); plt.close()

# clipped vs slab crossing & slab signal
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
clip = emax > 6.0  # arbitrary proxy threshold
axes[0].bar(["clipped", "not clipped"],
            [np.mean(hslab[clip]), np.mean(hslab[~clip])], color=["#C44E52", "#4C72B0"])
axes[0].set_ylabel("P(slab crossed)"); axes[0].set_ylim(0, 1.05)
axes[0].set_title("Clipping vs slab crossing (proxy)")
axes[1].hist(pslab[hslab] * DEDX, bins=30, histtype="step", label="all slab-crossed")
axes[1].hist((pslab * DEDX)[clip & hslab], bins=30, histtype="step", label="clipped & slab-crossed")
axes[1].set_xlabel("slab Edep proxy (MeV)"); axes[1].set_ylabel("events")
axes[1].set_title("Clipped events vs slab signal"); axes[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/energy/24-25_clipping_vs_panel.png", dpi=150); plt.close()

# ============================================================= print key conclusions
print("\n================ PHASE-3 ACCEPTANCE: KEY RESULTS ================")
r10 = next(r for r in summary if r["n"] == 2.0 and abs(r["L"] - 10) < 1e-6)
c = r10["topology_M2_counts"]; tot = sum(c.values())
print(f"Nominal n=2, L=10 cm:  generated {r10['ngen']:,}, triggered(M>=2) {r10['n_trigger_ge2']}")
print(f"  M2={r10['M_counts']['M2']}  M3={r10['M_counts']['M3']}  M4={r10['M_counts']['M4']}   "
      f"(data M2/M3/M4 = 260/2/0)")
print("  single-muon 2-hit topology fractions (MC) vs data:")
for t in TOPO:
    fmc = c[t] / tot if tot else 0
    print(f"    {t}: MC={fmc:.4f}  data={data_topo_frac[t]:.4f}   [{TOPO_KIND[t]}]")
sl_mc = (c["01"] + c["23"]) / tot if tot else 0
print(f"  same-layer(01+23): MC={sl_mc:.4g}  data={data_topo_frac['01']+data_topo_frac['23']:.4f}")
print("  P(slab crossed | topology), n=2 L=10:")
for t in TOPO:
    print(f"    {t}: inc={r10['slab_cross'][t]['P_slab_inc']:.3f}  exc={r10['slab_cross'][t]['P_slab_exc']:.3f}  (n_inc={r10['slab_cross'][t]['n_inc']})")
print("===================================================================")
print(f"\nFigures -> figures/{{acceptance,topology,energy}}/ ; tables -> tables/")
