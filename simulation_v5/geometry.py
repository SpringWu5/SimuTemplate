#!/usr/bin/env python3
"""geometry.py -- detector constants + vectorised ray-box primitives (v5).

Detector layout (matches is_engine block_boxes):
  Ch0 = upper-right  (+x, +z)    Ch1 = upper-left  (-x, +z)
  Ch2 = lower-right  (+x, -z)    Ch3 = lower-left  (-x, -z)
  slab = central plate, x,y in [-10,10], z in [-1,1].

Coordinate convention: +z is "up" (upper layer at +L/2). Muons travel
downward (d_z < 0). theta = angle from +z axis (vertical), phi = azimuth.

All length units: cm.
"""
import numpy as np

# ---- detector geometry ----
GAP = 10.0      # x-separation between left/right small blocks (centre-to-centre)
LSEP = 10.0     # z-separation between upper/lower layers (centre-to-centre)
HX = 1.0        # small block half-x
HY = 1.5        # small block half-y
HZ = 1.5        # small block half-z
SLAB_X = 10.0   # slab half-x
SLAB_Y = 10.0   # slab half-y
SLAB_Z = 1.0    # slab half-z
SLAB_MIN = np.array([-SLAB_X, -SLAB_Y, -SLAB_Z])
SLAB_MAX = np.array([+SLAB_X, +SLAB_Y, +SLAB_Z])

ALLCH = ["0", "1", "2", "3"]
TOPO = ["01", "23", "02", "13", "03", "12"]
TOP_CH = {"01": ("0", "1"), "23": ("2", "3"), "02": ("0", "2"),
          "13": ("1", "3"), "03": ("0", "3"), "12": ("1", "2")}

# channel bit mask in 4-bit pattern (Ch0=MSB)
CH_BIT = {"0": 8, "1": 4, "2": 2, "3": 1}
# topology -> 4-bit exclusive pattern
TOPO_BIT = {t: CH_BIT[a] | CH_BIT[b] for t, (a, b) in TOP_CH.items()}
# which topologies are same-layer (both upper / both lower)
SAME_LAYER = ["01", "23"]
CROSS_LAYER = ["02", "13", "03", "12"]


def block_boxes(gap=GAP, lsep=LSEP, hx=HX, hy=HY, hz=HZ, dx=0.0, dy=0.0):
    """Return {ch: (bmin, bmax)} for the 4 small blocks, optional per-call shift."""
    xR = gap / 2.0 + hx; xL = -gap / 2.0 - hx
    zU = lsep / 2.0; zL = -lsep / 2.0
    boxes = {}
    for nm, cx, cz in [("0", xR, zU), ("1", xL, zU), ("2", xR, zL), ("3", xL, zL)]:
        boxes[nm] = (np.array([cx + dx - hx, -hy + dy, cz - hz]),
                     np.array([cx + dx + hx, +hy + dy, cz + hz]))
    return boxes


def ray_box(P0, d, bmin, bmax):
    """Vectorised slab-method ray-AABB. Returns (hit[N], path[N])."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (bmin - P0) / d; t2 = (bmax - P0) / d
    tmin = np.minimum(t1, t2); tmax = np.maximum(t1, t2)
    te = np.max(tmin, axis=1); tx = np.min(tmax, axis=1)
    hit = (te < tx) & (tx > 0)
    te = np.clip(te, 0, None)
    return hit, np.where(hit, tx - te, 0.0)


def propagate(P0, d, boxes, slab_min=SLAB_MIN, slab_max=SLAB_MAX):
    """Propagate rays through all 4 small blocks + slab. Returns dict + slab flags."""
    hits = {}; paths = {}
    for nm, (bmin, bmax) in boxes.items():
        h, p = ray_box(P0, d, bmin, bmax); hits[nm] = h; paths[nm] = p
    hs, ps = ray_box(P0, d, slab_min, slab_max)
    return hits, paths, hs, ps


def hit_matrix(hits):
    """[N,4] boolean hit matrix in channel order 0,1,2,3."""
    return np.stack([hits[c] for c in ALLCH], axis=1)


def patterns(H):
    """From [N,4] hit matrix -> multiplicity M[N], exclusive-topo masks dict."""
    M = H.sum(axis=1)
    exc = {}
    for t in TOPO:
        a, b = TOP_CH[t]; ia = ALLCH.index(a); ib = ALLCH.index(b)
        both = H[:, ia] & H[:, ib]
        exc[t] = both & (M == 2)
    return M, exc


def pattern_to_bits(p):
    """Integer 0..15 -> {ch: bool} dict."""
    return {c: bool(p & CH_BIT[c]) for c in ALLCH}


def bits_to_int(hitdict):
    """{ch: bool} -> int."""
    return sum(CH_BIT[c] for c in ALLCH if hitdict[c])


def topo_counts_from_patterns(patt_arr):
    """Given array of int patterns (0..15), return {topo: count} exclusive M2 + M-dist."""
    out = {t: 0 for t in TOPO}
    mcount = {2: 0, 3: 0, 4: 0}
    for p in patt_arr:
        nb = bin(int(p)).count("1")
        if nb in mcount:
            mcount[nb] += 1
        if nb == 2:
            for t in TOPO:
                if int(p) == TOPO_BIT[t]:
                    out[t] += 1
                    break
    return out, mcount
