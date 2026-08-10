#!/usr/bin/env python3
"""
is_engine.py -- importance-sampling cosmic generator for topology acceptance.

Reference plane = z=0 (slab mid). Every detector-crossing muon crosses z=0, so
we sample the impact point (xi,yi) uniformly on [-R,R]^2 at z=0 (high
efficiency: every sample is near the detector) and draw (theta,phi) from a
proposal that enhances the rare same-layer region (large theta, phi near +-x).
The generation-plane origin (z=zplane) is back-projected; the track is
propagated with the vectorised axis-aligned ray-box.

Strict per-event weight:  w = w_theta * w_phi   (position proposal == target).
  target p_theta (conv. B, flat-detector flux) = (n+1) cos^n(theta)
  target p_theta (conv. A, direction-normal)   = (n+2) cos^(n+1)(theta)
  proposal q_theta = mT*p_theta_B + (1-mT)*Unif[th_lo,th_hi]
  target p_phi = 1/(2pi) ; proposal q_phi = mP/(2pi) + (1-mP)*g(phi)
      g(phi) = 0.5*[WNorm(phi;0,sig)+WNorm(phi;pi,sig)]
ESS = (sum w)^2 / sum(w^2).
"""
import numpy as np

TH_LO = np.deg2rad(70.0); TH_HI = np.deg2rad(89.0)


def wrapped_normal(phi, mu, sig):
    z = (phi - mu + np.pi) % (2 * np.pi) - np.pi
    p = 0.0
    for k in range(-2, 3):
        p += np.exp(-0.5 * ((phi - mu + 2 * np.pi * k) / sig) ** 2) / (np.sqrt(2 * np.pi) * sig)
    return p


def block_boxes(gap, L, hx, hy, hz, dx=0.0, dy=0.0):
    xR = gap / 2.0 + hx; xL = -gap / 2.0 - hx; zU = L / 2.0; zL = -L / 2.0
    o = {}
    for nm, cx, cz in [("0", xR, zU), ("1", xL, zU), ("2", xR, zL), ("3", xL, zL)]:
        o[nm] = (np.array([cx + dx - hx, -hy + dy, cz - hz]),
                 np.array([cx + dx + hx, +hy + dy, cz + hz]))
    return o


def ray_box(P0, d, bmin, bmax):
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (bmin - P0) / d; t2 = (bmax - P0) / d
    tmin = np.minimum(t1, t2); tmax = np.maximum(t1, t2)
    te = np.max(tmin, axis=1); tx = np.min(tmax, axis=1)
    hit = (te < tx) & (tx > 0); te = np.clip(te, 0, None)
    return hit, np.where(hit, tx - te, 0.0)


def sample(N, n, rng, R=10.0, zplane=10.0, HW=300.0, mT=0.7, mP=0.7, sig_phi=np.deg2rad(20.0),
           conv="B", mX=0.6, mY=0.6, XB1=20.0, XB2=45.0, sig_y=5.0):
    # ---- theta proposal ----
    u = rng.random(N); from_cosn = u < mT
    cosT_c = rng.random(N) ** (1.0 / (n + 1.0)); th_c = np.arccos(cosT_c)
    th_t = rng.uniform(TH_LO, TH_HI, N)
    theta = np.where(from_cosn, th_c, th_t)
    cosT = np.cos(theta)
    pB = (n + 1.0) * cosT ** n
    pA = (n + 2.0) * cosT ** (n + 1.0)
    p_theta = pA if conv == "A" else pB
    qT_tail = 1.0 / (TH_HI - TH_LO)
    in_tail = (theta >= TH_LO) & (theta <= TH_HI)
    q_theta = mT * pB + (1 - mT) * np.where(in_tail, qT_tail, 0.0)
    w_theta = p_theta / np.where(q_theta > 0, q_theta, 1e-30)
    # ---- phi proposal ----
    up = rng.random(N); from_uni = up < mP
    phi_uni = rng.uniform(0, 2 * np.pi, N)
    near = rng.choice([0.0, np.pi], N)
    phi_conc = (near + rng.normal(0, sig_phi, N)) % (2 * np.pi)
    phi = np.where(from_uni, phi_uni, phi_conc)
    g = 0.5 * (wrapped_normal_vec(phi, 0.0, sig_phi) + wrapped_normal_vec(phi, np.pi, sig_phi))
    q_phi = mP / (2 * np.pi) + (1 - mP) * g
    w_phi = (1.0 / (2 * np.pi)) / np.where(q_phi > 0, q_phi, 1e-30)
    # ---- position proposal (concentrate where same-layer muons start) ----
    p_uni = 1.0 / (2 * HW)
    ux = rng.random(N); x_band = ux < mX
    x0_uni = rng.uniform(-HW, HW, N)
    side = rng.choice([XB1, -XB1], N)                 # pick + or - band
    x0_band = side + rng.uniform(0.0, XB2 - XB1, N) * np.sign(side)
    x0 = np.where(x_band, x0_band, x0_uni)
    in_band = (np.abs(x0) >= XB1) & (np.abs(x0) <= XB2)
    qx = mX * np.where(in_band, 1.0 / (2 * (XB2 - XB1)), 0.0) + (1 - mX) * p_uni
    uy = rng.random(N); y_conc = uy < mY
    y0_uni = rng.uniform(-HW, HW, N)
    y0_c = rng.normal(0, sig_y, N)
    y0 = np.where(y_conc, y0_c, y0_uni)
    qy = mY * (np.exp(-0.5 * (y0 / sig_y) ** 2) / (np.sqrt(2 * np.pi) * sig_y)) + (1 - mY) * p_uni
    w_pos = (p_uni * p_uni) / np.where((qx * qy) > 0, qx * qy, 1e-30)
    w = w_theta * w_phi * w_pos
    # ---- direction + origin ----
    sT, cT = np.sin(theta), np.cos(theta)
    dx_, dy_, dz_ = sT * np.cos(phi), sT * np.sin(phi), -cT
    P0 = np.stack([x0, y0, np.full(N, zplane)], axis=1)
    dvec = np.stack([dx_, dy_, dz_], axis=1)
    return P0, dvec, theta, phi, w


def wrapped_normal_vec(phi, mu, sig):
    out = np.zeros_like(phi)
    for k in range(-2, 3):
        out += np.exp(-0.5 * ((phi - mu + 2 * np.pi * k) / sig) ** 2) / (np.sqrt(2 * np.pi) * sig)
    return out


def propagate(P0, d, boxes, slab_min, slab_max):
    hits = {}; paths = {}
    for nm, (bmin, bmax) in boxes.items():
        h, p = ray_box(P0, d, bmin, bmax); hits[nm] = h; paths[nm] = p
    hs, ps = ray_box(P0, d, slab_min, slab_max)
    return hits, paths, hs, ps


TOPO = ["01", "23", "02", "13", "03", "12"]
TOP_CH = {"01": ("0", "1"), "23": ("2", "3"), "02": ("0", "2"), "13": ("1", "3"), "03": ("0", "3"), "12": ("1", "2")}
ALLCH = ["0", "1", "2", "3"]


def patterns(hits):
    H = np.stack([hits[c] for c in ALLCH], axis=1); M = H.sum(axis=1)
    exc = {}; inc = {}
    for t in TOPO:
        a, b = TOP_CH[t]; ia = ALLCH.index(a); ib = ALLCH.index(b)
        both = H[:, ia] & H[:, ib]; inc[t] = both; exc[t] = both & (M == 2)
    return M, H, exc, inc


def weighted_fracs(w, M, exc):
    """P(T|M2) weighted + ESS per topology."""
    m2 = (M == 2)
    W2 = w[m2].sum()
    out = {}
    for t in TOPO:
        sel = m2 & exc[t]
        ws = w[sel]
        f = ws.sum() / W2 if W2 > 0 else 0.0
        ess = (ws.sum() ** 2 / (ws ** 2).sum()) if ws.size else 0.0
        relerr = (1.0 / np.sqrt(ess)) if ess > 0 else np.inf
        out[t] = (f, ess, relerr, int(sel.sum()))
    return out
