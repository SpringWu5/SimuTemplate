#!/usr/bin/env python3
"""generator.py -- corrected cosmic single-muon generator for v5.

Inherits the audit-validated importance sampler from v4/is_engine, wrapped
into a clean v5 API. Two entry points:

  sample_single(N, n, rng, **kw)  -> dict of arrays (geometry-level hits,
                                     paths, theta, phi, weights, slab crossing)
  draw_unbiased(N, n, rng, ...)   -> same but with proposal==target (w==1):
                                     proper cos^n(theta), uniform phi, large
                                     generation plane (z=10, HW=250/300).

Convention B (flat-detector flux): p(theta) = (n+1) cos^n(theta), theta from +z.
"""
import numpy as np
from . import geometry as G


def _wrapped_normal_vec(phi, mu, sig):
    out = np.zeros_like(phi)
    for k in range(-2, 3):
        out += np.exp(-0.5 * ((phi - mu + 2 * np.pi * k) / sig) ** 2) / (np.sqrt(2 * np.pi) * sig)
    return out


def sample_single(N, n=2.0, rng=None, R=10.0, zplane=10.0, HW=300.0,
                  mT=0.7, mP=0.7, sig_phi=np.deg2rad(20.0),
                  conv="B", mX=0.6, mY=0.6, XB1=20.0, XB2=45.0, sig_y=5.0,
                  gap=G.GAP, lsep=G.LSEP, align_dx=None):
    """Importance-sampled single muon. align_dx = {ch: dx_shift} for alignment study.

    Returns dict: P0, d, theta, phi, w, hits, paths, hslab, pslab, M, H, exc.
    """
    if rng is None:
        rng = np.random.default_rng()
    TH_LO = np.deg2rad(70.0); TH_HI = np.deg2rad(89.0)
    # theta proposal
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
    # phi proposal
    up = rng.random(N); from_uni = up < mP
    phi_uni = rng.uniform(0, 2 * np.pi, N)
    near = rng.choice([0.0, np.pi], N)
    phi_conc = (near + rng.normal(0, sig_phi, N)) % (2 * np.pi)
    phi = np.where(from_uni, phi_uni, phi_conc)
    g = 0.5 * (_wrapped_normal_vec(phi, 0.0, sig_phi) + _wrapped_normal_vec(phi, np.pi, sig_phi))
    q_phi = mP / (2 * np.pi) + (1 - mP) * g
    w_phi = (1.0 / (2 * np.pi)) / np.where(q_phi > 0, q_phi, 1e-30)
    # position proposal
    p_uni = 1.0 / (2 * HW)
    ux = rng.random(N); x_band = ux < mX
    x0_uni = rng.uniform(-HW, HW, N)
    side = rng.choice([XB1, -XB1], N)
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
    sT, cT = np.sin(theta), np.cos(theta)
    dvec = np.stack([sT * np.cos(phi), sT * np.sin(phi), -cT], axis=1)
    P0 = np.stack([x0, y0, np.full(N, zplane)], axis=1)

    if align_dx is not None:
        boxes = {}
        base = G.block_boxes(gap=gap, lsep=lsep)
        for nm, (bmin, bmax) in base.items():
            dx = align_dx.get(nm, 0.0)
            boxes[nm] = (bmin + np.array([dx, 0, 0]), bmax + np.array([dx, 0, 0]))
    else:
        boxes = G.block_boxes(gap=gap, lsep=lsep)
    hits, paths, hslab, pslab = G.propagate(P0, dvec, boxes)
    H = G.hit_matrix(hits); M, exc = G.patterns(H)
    return dict(P0=P0, d=dvec, theta=theta, phi=phi, w=w,
                hits=hits, paths=paths, hslab=hslab, pslab=pslab,
                M=M, H=H, exc=exc, boxes=boxes)


def draw_unbiased(N, n=2.0, rng=None, HW=250.0, zplane=10.0,
                  gap=G.GAP, lsep=G.LSEP, align_dx=None):
    if rng is None:
        rng = np.random.default_rng()
    cosT = rng.random(N) ** (1.0 / (n + 1.0)); theta = np.arccos(cosT)
    phi = rng.uniform(0, 2 * np.pi, N)
    sT, cT = np.sin(theta), np.cos(theta)
    dvec = np.stack([sT * np.cos(phi), sT * np.sin(phi), -cT], axis=1)
    x0 = rng.uniform(-HW, HW, N); y0 = rng.uniform(-HW, HW, N)
    P0 = np.stack([x0, y0, np.full(N, zplane)], axis=1)
    if align_dx is not None:
        boxes = {}
        for nm, (bmin, bmax) in G.block_boxes(gap=gap, lsep=lsep).items():
            dx = align_dx.get(nm, 0.0)
            boxes[nm] = (bmin + np.array([dx, 0, 0]), bmax + np.array([dx, 0, 0]))
    else:
        boxes = G.block_boxes(gap=gap, lsep=lsep)
    hits, paths, hslab, pslab = G.propagate(P0, dvec, boxes)
    H = G.hit_matrix(hits); M, exc = G.patterns(H)
    return dict(P0=P0, d=dvec, theta=theta, phi=phi,
                hits=hits, paths=paths, hslab=hslab, pslab=pslab,
                M=M, H=H, exc=exc, boxes=boxes)


def resample_triggered(is_sample, N_out, rng, Mmin=2):
    """Importance-resample triggered events by weight -> unweighted sample.

    Returns an unweighted event dict (w=1) of N_out triggered single muons,
    representing the TRUE cosmic-triggered population (same-layer ~6.6%).
    Toy models (correlated/fake) are then applied by simple counting.
    """
    s = is_sample
    w = s["w"]; M = s["M"]
    sel = M >= Mmin
    idx = np.where(sel)[0]
    ww = w[idx].clip(min=0)
    ww = ww / ww.sum()
    pick = rng.choice(idx, size=N_out, replace=True, p=ww)
    out = dict(w=np.ones(N_out))
    for key in ("P0", "d", "theta", "phi", "hslab", "pslab"):
        out[key] = s[key][pick]
    # rebuild per-channel arrays for picked events
    H = s["H"][pick]
    hits = {c: H[:, i] for i, c in enumerate(G.ALLCH)}
    paths = {c: s["paths"][c][pick] for c in G.ALLCH}
    out["hits"] = hits; out["paths"] = paths
    out["H"] = H
    M2, exc = G.patterns(H); out["M"] = M2; out["exc"] = exc
    out["boxes"] = s["boxes"]
    return out
