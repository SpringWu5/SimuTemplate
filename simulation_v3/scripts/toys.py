#!/usr/bin/env python3
"""
toys.py -- minimal multi-track and stochastic fake-hit toy models on top of the
single-muon hit-pattern distribution, to test what EXTRA mechanism is needed to
reproduce the observed topology structure (esp. same-layer doubles & M3).

NOT a physical air-shower model -- a parameterised toy, clearly labelled.
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures", "comparison")
TBL = os.path.join(ROOT, "tables")
os.makedirs(FIG, exist_ok=True)
sys.path.insert(0, HERE)
import acceptance_mc as am

DATA_TOPO = {"01": 78, "23": 57, "02": 56, "13": 25, "03": 25, "12": 19}
TOPO = list(DATA_TOPO)
TOP_BITS = {"01": (0, 1), "23": (2, 3), "02": (0, 2), "13": (1, 3), "03": (0, 3), "12": (1, 2)}
data_topo_frac = {t: DATA_TOPO[t] / sum(DATA_TOPO.values()) for t in TOPO}
DATA_M = {"M2": 260, "M3": 2, "M4": 0}
data_M_tot = sum(DATA_M.values())
data_M_frac = {k: v / data_M_tot for k, v in DATA_M.items()}


def single_pattern_dist(n=2.0, L=10.0, N=8_000_000, seed=11):
    """High-stat single-track 4-bit pattern probability (16 bins)."""
    rng = np.random.default_rng(seed)
    slab_min = np.array([-am.SLAB["hx"], -am.SLAB["hy"], -am.SLAB["hz"]])
    slab_max = np.array([+am.SLAB["hx"], +am.SLAB["hy"], +am.SLAB["hz"]])
    r = am.run_one(n, L, N, rng, slab_min, slab_max)
    H = np.stack([r["hits"][c] for c in am.ALLCH], axis=1).astype(int)  # (N,4)
    pat = H[:, 0] * 8 + H[:, 1] * 4 + H[:, 2] * 2 + H[:, 3] * 1
    p = np.bincount(pat, minlength=16) / N
    return p


def topo_and_M(p):
    """From 16-pattern prob -> topology frac (of M=2) and M2/M3/M4 frac (of M>=2)."""
    counts = np.array([p[i] for i in range(16)])
    M = np.array([bin(i).count("1") for i in range(16)])
    ge2 = counts[M >= 2].sum()
    m2 = counts[M == 2].sum()
    topo = {}
    for t in TOPO:
        a, b = TOP_BITS[t]
        # exclusive: exactly those two bits, pattern == (1<<a)|(1<<b)
        pat_id = (1 << (3 - a)) | (1 << (3 - b))   # map bit index to pattern int (bit3=Ch0)
        topo[t] = counts[pat_id] / m2 if m2 > 0 else 0.0
    mfrac = {f"M{k}": counts[M == k].sum() / ge2 if ge2 > 0 else 0.0 for k in range(2, 5)}
    return topo, mfrac


# bit ordering in pattern int: bit3=Ch0, bit2=Ch1, bit1=Ch2, bit0=Ch3 (matches pat formula above)
def multi_event_dist(p_single, p_multi):
    p_or = np.zeros(16)
    for i in range(16):
        if p_single[i] == 0:
            continue
        for j in range(16):
            p_or[i | j] += p_single[i] * p_single[j]
    return (1 - p_multi) * p_single + p_multi * p_or


def fake_event_dist(p_single, p_fake, prefer_same_layer=False):
    """Each non-hit block gets a fake trigger hit w.p. p_fake."""
    out = np.zeros(16)
    bits = [3, 2, 1, 0]  # Ch0..Ch3 bit positions in pattern int
    for b in range(16):
        pb = p_single[b]
        if pb == 0:
            continue
        hit_bits = {bits[k] for k in range(4) if (b >> bits[k]) & 1}
        free = [bits[k] for k in range(4) if bits[k] not in hit_bits]
        # iterate over subsets of free bits (<=4 -> 16 cases)
        for mask in range(1 << len(free)):
            extra = [free[i] for i in range(len(free)) if (mask >> i) & 1]
            if prefer_same_layer:
                # boost probability of fake in the partner same-layer channel
                pp = 1.0
                # (simple illustrative variant: not used by default)
            pextra = p_fake ** len(extra) * (1 - p_fake) ** (len(free) - len(extra))
            nb = b
            for e in extra:
                nb |= (1 << e)
            out[nb] += pb * pextra
    return out


def g_test_frac(mc_frac, data_frac):
    obs = np.array([data_frac[t] for t in TOPO]); exp = np.array([mc_frac[t] for t in TOPO])
    s = exp.sum(); exp = exp / s * obs.sum()
    m = exp > 0
    return 2 * np.nansum(obs[m] * np.log(obs[m] / exp[m]))


def main():
    print("computing single-track pattern distribution (8e6 muons, n=2, L=10)...")
    p1 = single_pattern_dist()
    base_topo, base_M = topo_and_M(p1)
    print("single-muon same-layer(01+23) frac =", base_topo["01"] + base_topo["23"])

    # ---- multi-track scan ----
    pms = np.linspace(0, 1, 51)
    mt_sl = []; mt_g = []; mt_m3 = []; mt_topo_at = {}
    for pm in pms:
        pe = multi_event_dist(p1, pm)
        t, m = topo_and_M(pe)
        mt_sl.append(t["01"] + t["23"]); mt_g.append(g_test_frac(t, data_topo_frac))
        mt_m3.append(m["M3"])
    mt_sl = np.array(mt_sl); mt_g = np.array(mt_g)

    # ---- fake-hit scan ----
    pfs = np.linspace(0, 0.6, 61)
    fk_sl = []; fk_g = []; fk_m3 = []
    for pf in pfs:
        pe = fake_event_dist(p1, pf)
        t, m = topo_and_M(pe)
        fk_sl.append(t["01"] + t["23"]); fk_g.append(g_test_frac(t, data_topo_frac))
        fk_m3.append(m["M3"])
    fk_sl = np.array(fk_sl); fk_g = np.array(fk_g)

    data_sl = data_topo_frac["01"] + data_topo_frac["23"]

    # ---- figures ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    axes[0].plot(pms, mt_sl, "o-", ms=3, label="same-layer frac (toy)")
    axes[0].axhline(data_sl, color="k", ls="--", label=f"data = {data_sl:.2f}")
    axes[0].set_xlabel("p_multi (prob. of 2nd track)"); axes[0].set_ylabel("same-layer 2-hit fraction")
    axes[0].set_title("Multi-track toy: same-layer fraction"); axes[0].legend(fontsize=8)
    axes[1].plot(pfs, fk_sl, "o-", ms=3, color="#C44E52", label="same-layer frac (toy)")
    axes[1].axhline(data_sl, color="k", ls="--", label=f"data = {data_sl:.2f}")
    axes[1].set_xlabel("p_fake (fake-hit prob.)"); axes[1].set_ylabel("same-layer 2-hit fraction")
    axes[1].set_title("Fake-hit toy: same-layer fraction"); axes[1].legend(fontsize=8)
    plt.tight_layout(); plt.savefig(f"{FIG}/39_toy_same_layer.png", dpi=150); plt.close()

    # G-test vs data
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(pms, mt_g, "o-", ms=3, label="multi-track")
    ax.plot(pfs, fk_g, "s-", ms=3, color="#C44E52", label="fake-hit")
    ax.set_xlabel("p_multi / p_fake"); ax.set_ylabel("G-test vs data (topology)")
    ax.set_title("Toy goodness-of-fit (lower=closer to data topology)")
    ax.legend()
    plt.tight_layout(); plt.savefig(f"{FIG}/40_toy_gtest.png", dpi=150); plt.close()

    # best-match p_multi / p_fake (min G excluding endpoints)
    i_mt = np.argmin(mt_g[1:-1]) + 1
    i_fk = np.argmin(fk_g[1:-1]) + 1
    # p_multi needed to reach data same-layer
    pm_need = float(np.interp(data_sl, mt_sl, pms)) if mt_sl[-1] >= data_sl else float("nan")
    pf_need = float(np.interp(data_sl, fk_sl, pfs)) if fk_sl[-1] >= data_sl else float("nan")

    print("\n================ TOY MODEL RESULTS ================")
    print(f"data same-layer fraction = {data_sl:.3f}")
    print(f"multi-track: p_multi needed for same-layer = {pm_need:.3f}" if pm_need == pm_need else "multi-track: cannot reach data same-layer even at p_multi=1")
    print(f"fake-hit  : p_fake  needed for same-layer = {pf_need:.3f}" if pf_need == pf_need else "fake-hit: cannot reach")
    print(f"best-G multi-track: p_multi={pms[i_mt]:.2f} G={mt_g[i_mt]:.1f}")
    print(f"best-G fake-hit  : p_fake ={pfs[i_fk]:.2f} G={fk_g[i_fk]:.1f}")

    # topology at best multi-track
    pe = multi_event_dist(p1, pms[i_mt]); t, m = topo_and_M(pe)
    print("topology at best multi-track vs data:")
    for k in TOPO:
        print(f"  {k}: toy={t[k]:.3f}  data={data_topo_frac[k]:.3f}")
    print(f"  M2/M3/M4 toy = {m['M2']:.3f}/{m['M3']:.3f}/{m['M4']:.3f}  data = {data_M_frac['M2']:.3f}/{data_M_frac['M3']:.3f}/{data_M_frac['M4']:.3f}")
    print("===================================================")

    import csv
    with open(os.path.join(TBL, "toy_summary.csv"), "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["model", "param_for_same_layer", "best_G", "best_param", "note"])
        w.writerow(["multi-track", f"{pm_need:.3f}" if pm_need == pm_need else "unreachable",
                    f"{mt_g[i_mt]:.1f}", f"{pms[i_mt]:.2f}", "2nd independent cosmic track w.p. p_multi"])
        w.writerow(["fake-hit", f"{pf_need:.3f}" if pf_need == pf_need else "unreachable",
                    f"{fk_g[i_fk]:.1f}", f"{pfs[i_fk]:.2f}", "random fake trigger hit w.p. p_fake"])
    print(f"\nFigures -> {FIG}/ ; table -> tables/toy_summary.csv")


if __name__ == "__main__":
    main()
