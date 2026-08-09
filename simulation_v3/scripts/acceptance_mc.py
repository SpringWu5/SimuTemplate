#!/usr/bin/env python3
"""
acceptance_mc.py -- Phase-3 geometry-acceptance Monte Carlo (NO optics).

Generates cosmic single muons (dN/dOmega ∝ cos^n(theta)), propagates straight
tracks through the real finite-size detector (4 small scints + central slab),
and records per-muon hits, path lengths, slab crossing, intersection, theta/phi.

Scans angular exponent n and upper/lower layer separation.
Saves aggregates + a record sample to simulation_v3/processed/.
"""
import os, argparse
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = yaml.safe_load(open(os.path.join(ROOT, "configs", "geometry.yaml")))

SLAB = CFG["slab"]; BK = CFG["block"]; GAP = CFG["same_layer_gap"]
ZPLAN = CFG["generation"]["z_plane"]; HW = CFG["generation"]["half_width"]

# block centres (x), y centred at 0
xR = +GAP / 2 + BK["hx"]   # +6
xL = -GAP / 2 - BK["hx"]   # -6
hx, hy, hz = BK["hx"], BK["hy"], BK["hz"]


def block_boxes(L):
    """Return list of (name, xmin,xmax,ymin,ymax,zmin,zmax) for Ch0..Ch3 at layer sep L."""
    zU = +L / 2; zL = -L / 2
    boxes = []
    # Ch0 upper right, Ch1 upper left, Ch2 lower right, Ch3 lower left
    for name, cx, cz in [("0", xR, zU), ("1", xL, zU), ("2", xR, zL), ("3", xL, zL)]:
        boxes.append((name, cx - hx, cx + hx, -hy, +hy, cz - hz, cz + hz))
    return boxes


def ray_box(P0, d, bmin, bmax):
    """Vectorised axis-aligned ray-box. P0,d:(N,3); bmin,bmax:(3,). -> hit(N,), path(N,)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (bmin - P0) / d
        t2 = (bmax - P0) / d
    tmin = np.minimum(t1, t2)
    tmax = np.maximum(t1, t2)
    te = np.max(tmin, axis=1)
    tx = np.min(tmax, axis=1)
    hit = (te < tx) & (tx > 0)
    te = np.clip(te, 0, None)
    path = np.where(hit, tx - te, 0.0)
    return hit, path


def gen_muons(n, N, rng):
    """N muons, dN/dOmega ∝ cos^n(theta). Returns P0(N,3), dir(N,3), theta(N,)."""
    x0 = rng.uniform(-HW, HW, N); y0 = rng.uniform(-HW, HW, N)
    u = rng.random(N)
    cosT = u ** (1.0 / (n + 1.0))            # cosθ distributed as (n+1)cos^nθ
    theta = np.arccos(cosT)
    phi = rng.uniform(0, 2 * np.pi, N)
    dx = np.sin(theta) * np.cos(phi)
    dy = np.sin(theta) * np.sin(phi)
    dz = -cosT                                # downward
    P0 = np.stack([x0, y0, np.full(N, ZPLAN)], axis=1)
    d = np.stack([dx, dy, dz], axis=1)
    return P0, d, theta, phi


def run_one(n, L, N, rng, slab_min, slab_max):
    P0, d, theta, phi = gen_muons(n, N, rng)
    boxes = block_boxes(L)
    hits = {}; paths = {}
    for (nm, *lims) in boxes:
        bmin = np.array(lims[0::2]); bmax = np.array(lims[1::2])
        h, p = ray_box(P0, d, bmin, bmax)
        hits[nm] = h; paths[nm] = p
    hslab, pslab = ray_box(P0, d, slab_min, slab_max)
    # slab intersection (x,y) where track crosses z=0
    tz = ZPLAN / np.cos(theta)                # t at z=0 (cosθ>0)
    sx = P0[:, 0] + tz * d[:, 0]
    sy = P0[:, 1] + tz * d[:, 1]
    return dict(P0=P0, d=d, theta=theta, phi=phi, hits=hits, paths=paths,
                hslab=hslab, pslab=pslab, sx=sx, sy=sy)


TOPO = ["01", "23", "02", "13", "03", "12"]
# topology -> required channels present (exclusive: exactly those two)
TOP_CH = {"01": ("0", "1"), "23": ("2", "3"), "02": ("0", "2"),
          "13": ("1", "3"), "03": ("0", "3"), "12": ("1", "2")}
ALLCH = ["0", "1", "2", "3"]


def patterns(hits):
    """Return M (multiplicity 0..4), and per-topology exclusive & inclusive masks."""
    H = np.stack([hits[c] for c in ALLCH], axis=1)   # (N,4)
    M = H.sum(axis=1)
    exc = {}; inc = {}
    for t in TOPO:
        a, b = TOP_CH[t]
        ia, ib = ALLCH.index(a), ALLCH.index(b)
        both = H[:, ia] & H[:, ib]
        inc[t] = both
        exc[t] = both & (M == 2)
    return M, H, exc, inc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260809)
    ap.add_argument("--sample", type=int, default=200000, help="record sample size saved per (n,L)")
    ap.add_argument("--focus", action="store_true",
                    help="focused high-stat run: single (n,L) from --fn/--fL, save ALL triggered records")
    ap.add_argument("--fn", type=float, default=2.0)
    ap.add_argument("--fL", type=float, default=10.0)
    ap.add_argument("--fN", type=int, default=30000000)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    slab_min = np.array([-SLAB["hx"], -SLAB["hy"], -SLAB["hz"]])
    slab_max = np.array([+SLAB["hx"], +SLAB["hy"], +SLAB["hz"]])

    if args.focus:
        n, L, N = args.fn, args.fL, args.fN
        r = run_one(n, L, N, rng, slab_min, slab_max)
        M, H, exc, inc = patterns(r["hits"])
        mtrig = M >= 2
        idx = np.where(mtrig)[0]
        rec = {
            "theta": r["theta"][idx], "phi": r["phi"][idx], "M": M[idx],
            "hslab": r["hslab"][idx], "pslab": r["pslab"][idx],
            "sx": r["sx"][idx], "sy": r["sy"][idx], "H": H[idx],
            "path0": r["paths"]["0"][idx], "path1": r["paths"]["1"][idx],
            "path2": r["paths"]["2"][idx], "path3": r["paths"]["3"][idx],
        }
        for t in TOPO:
            rec[f"exc_{t}"] = exc[t][idx]; rec[f"inc_{t}"] = inc[t][idx]
        out = os.path.join(ROOT, "processed", f"triggered_n{n:.1f}_L{L:.0f}.npz")
        np.savez_compressed(out, **rec)
        print(f"FOCUS n={n} L={L}: generated {N}, triggered {mtrig.sum()} -> {out}")
        return

    N = CFG["n_muons"]
    ns = CFG["n_values"]; Ls = CFG["layer_sep_values"]

    summary = []   # rows
    os.makedirs(os.path.join(ROOT, "processed"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "raw"), exist_ok=True)

    for n in ns:
        for L in Ls:
            r = run_one(n, L, N, rng, slab_min, slab_max)
            M, H, exc, inc = patterns(r["hits"])
            ngen = N
            n_trig = int((M >= 2).sum())
            row = {"n": n, "L": L, "ngen": ngen, "n_trigger_ge2": n_trig,
                   "M_counts": {f"M{k}": int((M == k).sum()) for k in range(5)}}
            # topology fractions among M==2 (exclusive) and inclusive given M>=2
            top_exc = {}; top_inc_slab = {}
            for t in TOPO:
                top_exc[t] = int(exc[t].sum())
                top_inc_slab[t] = (inc[t] & (M >= 2)).sum()
            row["topology_M2_counts"] = top_exc
            row["topology_inclusive_ge2_counts"] = {t: int(v) for t, v in top_inc_slab.items()}
            # P(slab crossed | topology) inclusive & exclusive (given M>=2 trigger)
            ps = {}
            for t in TOPO:
                m_inc = inc[t] & (M >= 2)
                m_exc = exc[t]
                ps[t] = {"P_slab_inc": float(r["hslab"][m_inc].mean()) if m_inc.sum() else float("nan"),
                         "P_slab_exc": float(r["hslab"][m_exc].mean()) if m_exc.sum() else float("nan"),
                         "n_inc": int(m_inc.sum()), "n_exc": int(m_exc.sum())}
            row["slab_cross"] = ps
            summary.append(row)

            # save a record sample for figures (nominal L only; keep all n)
            if abs(L - 10.0) < 1e-6:
                keep = rng.choice(N, size=min(args.sample, N), replace=False)
                rec = {
                    "theta": r["theta"][keep], "phi": r["phi"][keep],
                    "M": M[keep], "hslab": r["hslab"][keep], "pslab": r["pslab"][keep],
                    "sx": r["sx"][keep], "sy": r["sy"][keep],
                    "H": H[keep],
                    "path0": r["paths"]["0"][keep], "path1": r["paths"]["1"][keep],
                    "path2": r["paths"]["2"][keep], "path3": r["paths"]["3"][keep],
                }
                for t in TOPO:
                    rec[f"exc_{t}"] = exc[t][keep]; rec[f"inc_{t}"] = inc[t][keep]
                np.savez_compressed(os.path.join(ROOT, "processed", f"records_n{n:.1f}_L10.npz"), **rec)
            print(f"n={n} L={L}: trig(M>=2)={n_trig}/{N}={n_trig/N:.5f}  "
                  f"M2={row['M_counts']['M2']} M3={row['M_counts']['M3']} M4={row['M_counts']['M4']}  "
                  f"topo(M2) 01={top_exc['01']} 23={top_exc['23']} 02={top_exc['02']} "
                  f"13={top_exc['13']} 03={top_exc['03']} 12={top_exc['12']}")

    np.save(os.path.join(ROOT, "processed", "summary.npy"), np.array(summary, dtype=object), allow_pickle=True)
    import json
    with open(os.path.join(ROOT, "processed", "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\nSaved summary -> processed/summary.json ; records -> processed/records_n*_L10.npz")


if __name__ == "__main__":
    main()
