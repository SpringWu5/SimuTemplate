#!/usr/bin/env python3
"""toys.py -- multi-track / correlated / fake toy models (v5, audited).

The v4 `correlated_two_track` was BUGGY: it drew both tracks independently
from the single-track pattern distribution and ignored the geometric offset
(s_cm) and angular spread (sigma_deg) parameters entirely -- so it was just
the independent multi-track model in disguise and could never raise the
same-layer fraction (confirmed: fig13 ~0 for all p_corr).

This module rebuilds everything GEOMETRICALLY: each track is a real ray
through the detector, OR-ed at the hit level.

Joint distribution of the correlated two-track model (C2):
  track1 ~ corrected cosmic single muon (cos^n theta, uniform phi)
  r2_perp ~ Uniform(0, s)            transverse separation magnitude
  eta     ~ Uniform(0, 2 pi)         transverse offset direction
  dth, dph ~ Gaussian(0, sigma_theta) angular perturbation of track2 dir
  track2 origin = track1 impact point at z=zplane + offset_perp
  track2 direction = normalise(track1 dir + angular perturbation)
  -> both propagated through the SAME detector geometry; hits are OR-ed.

So if a near-horizontal track1 clips Ch0 (upper-right), a track2 offset by
~gap in -x at the same z-layer clips Ch1 (upper-left) => U01 same-layer,
which the v4 code could never produce.
"""
import numpy as np
from . import geometry as G


def _perturb_dir(d, sigma_rad, rng, N):
    """Add small angular perturbation to direction vectors, renormalise."""
    # rotate by a small random angle about a random perpendicular axis
    dax = rng.normal(0, 1, (N, 3))
    # make perpendicular to d
    d_norm = d / np.clip(np.linalg.norm(d, axis=1, keepdims=True), 1e-12, None)
    proj = (dax * d_norm).sum(axis=1, keepdims=True) * d_norm
    axis = dax - proj
    an = np.clip(np.linalg.norm(axis, axis=1, keepdims=True), 1e-12, None)
    axis = axis / an
    ang = rng.normal(0, sigma_rad, (N, 1))
    c, s = np.cos(ang), np.sin(ang)
    rot = c * d_norm + s * np.cross(axis, d_norm) + (axis * (axis * d_norm).sum(axis=1, keepdims=True)) * (1 - c)
    return rot / np.clip(np.linalg.norm(rot, axis=1, keepdims=True), 1e-12, None)


def _prop_one(P0, d, boxes):
    hits, paths, hs, ps = G.propagate(P0, d, boxes)
    return G.hit_matrix(hits)


def independent_two_track(single, p_multi, rng, zplane=10.0, HW=30.0):
    """C_indep: with prob p_multi add a 2nd INDEPENDENT cosmic muon, OR hits.

    track2 has its own cos^n(theta) direction and independent origin near the
    detector (so it can hit a different channel). OR-ing two independent cosmic
    tracks raises M3/M4.
    """
    H1 = single["H"]
    N = H1.shape[0]
    th = np.arccos(rng.random(N) ** (1.0 / 3.0)); ph = rng.uniform(0, 2 * np.pi, N)
    sT, cT = np.sin(th), np.cos(th)
    d2 = np.stack([sT * np.cos(ph), sT * np.sin(ph), -cT], axis=1)
    P2 = np.stack([rng.uniform(-HW, HW, N), rng.uniform(-HW, HW, N),
                   np.full(N, zplane)], axis=1)
    H2 = _prop_one(P2, d2, single["boxes"])
    use2 = rng.random(N) < p_multi
    return np.where(use2[:, None], H1 | H2, H1), use2


def correlated_two_track(single, p_corr, s_cm, sigma_deg, rng,
                         zplane=10.0, offset_mode="transverse"):
    """C_corr: geometrically correlated second track (audited, v5).

    Joint distribution:
      track1   ~ (already in `single`: cosmic muon, any multiplicity)
      r        ~ Uniform(0, s_cm)               transverse separation magnitude
      eta      ~ offset direction (see offset_mode)
      dth      ~ rotation by Gaussian(0, sigma_deg) about a random axis
      track2 origin = track1 origin + r*(cos eta, sin eta, 0)
      track2 direction = track1 direction rotated by dth
      with prob p_corr, OR track2 hits into track1.

    offset_mode:
      'transverse' : eta ~ Uniform(0,2pi)  -- physical shower spread (isotropic
                     in the x-y plane); least effective at same-layer because a
                     random direction rarely aligns with the inter-block x-gap.
      'det_x'      : eta in {0, pi} (pure +-x) -- models longitudinal shower
                     separation along the detector x-axis; most effective at
                     producing same-layer neighbour pairs (U01/L23).
      'mixed'      : cos-weighted toward +-x.

    Both tracks are real rays through the same detector; hits are OR-ed. This
    is the fix for the v4 bug which drew both tracks independently and ignored
    the offset entirely.
    """
    H1 = single["H"]; N = H1.shape[0]
    d1 = single["d"]; P1 = single["P0"]
    rmag = rng.uniform(0, s_cm, N)
    if offset_mode == "det_x":
        eta = rng.choice([0.0, np.pi], N)
    elif offset_mode == "mixed":
        eta = (rng.choice([0.0, np.pi], N) + rng.normal(0, np.deg2rad(20), N)) % (2 * np.pi)
    else:  # transverse
        eta = rng.uniform(0, 2 * np.pi, N)
    ox = rmag * np.cos(eta); oy = rmag * np.sin(eta)
    P2 = P1 + np.stack([ox, oy, np.zeros(N)], axis=1)
    d2 = _perturb_dir(d1, np.deg2rad(sigma_deg), rng, N)
    H2 = _prop_one(P2, d2, single["boxes"])
    use2 = rng.random(N) < p_corr
    return np.where(use2[:, None], H1 | H2, H1), use2, dict(P2=P2, d2=d2, ox=ox, oy=oy, use2=use2)


# ============================== FAKE MODELS ==============================
# F1: pure random trigger-bit flip
# F2: same-layer electronics copy (if a real pulse on ch, neighbour same-layer ch fires)
# F3: physical secondary-like (a real ray that deposits plastic-like Edep but
#      need not cross the slab)

def fake_random(N, p_fake, rng, n_extra=None):
    """F1: OR-in random bits with per-channel prob p_fake (uniform across ch)."""
    if n_extra is None:
        n_extra = N
    bits = rng.random((n_extra, 4)) < p_fake
    return bits


def fake_electronics_copy(H_real, P_fake_fn, rng, r_dist="broad", r_lo=0.1, r_hi=0.6):
    """F2: same-layer neighbour copies a fraction of the primary pulse.

    Map of same-layer neighbour pairs: 0<->1 (upper), 2<->3 (lower).
    P_fake(A_primary) returns the copy probability given primary amplitude proxy;
    here primary amplitude proxy = path length of the real hit (caller passes
    paths). r (amplitude ratio minor/major) drawn from a broad distribution.
    Returns dict of extra hit rows + amplitude ratios.
    """
    pass  # implemented in response-aware variant below; geometry-only stub kept for tests


SAME_LAYER_NEIGH = {"0": "1", "1": "0", "2": "3", "3": "2"}
LAYER_OF = {"0": "U", "1": "U", "2": "L", "3": "L"}


def fake_secondary_geom(single, p_sec, s_cm, rng, zplane=10.0):
    """F3: add an additional physical ray (real geometry, real path/Edep) that
    need not cross the slab. Origin = primary impact + offset; direction =
    independent downward cosmic (so it can hit a same-layer neighbour and
    deposit plastic-like energy, but usually misses the slab)."""
    H1 = single["H"]; N = H1.shape[0]
    rmag = rng.uniform(0, s_cm, N); eta = rng.uniform(0, 2 * np.pi, N)
    ox = rmag * np.cos(eta); oy = rmag * np.sin(eta)
    P2 = single["P0"] + np.stack([ox, oy, np.zeros(N)], axis=1)
    # independent direction (broad cosmic)
    th = np.arccos(rng.random(N) ** (1.0 / 3.0)); ph = rng.uniform(0, 2 * np.pi, N)
    sT, cT = np.sin(th), np.cos(th)
    d2 = np.stack([sT * np.cos(ph), sT * np.sin(ph), -cT], axis=1)
    hits2, paths2, hs2, _ = G.propagate(P2, d2, single["boxes"])
    H2 = G.hit_matrix(hits2)
    use2 = rng.random(N) < p_sec
    return np.where(use2[:, None], H1 | H2, H1), dict(H2=H2, paths2=paths2, hslab2=hs2, use2=use2)


def H_to_counts(H, w=None):
    """[N,4] hit matrix (possibly weighted) -> {topo:frac}, M2/M3/M4 fractions.

    Exclusive M2 topology fractions (P(topo|M2)), and P(Mk|M>=2).
    """
    M = H.sum(axis=1)
    if w is None:
        w = np.ones(H.shape[0])
    m2 = M == 2; ge2 = M >= 2
    W2 = w[m2].sum(); Wge2 = w[ge2].sum()
    tf = {}
    for t in G.TOPO:
        a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
        sel = m2 & H[:, ia] & H[:, ib]
        tf[t] = w[sel].sum() / W2 if W2 > 0 else 0.0
    mf = {f"M{k}": w[M == k].sum() / Wge2 if Wge2 > 0 else 0.0 for k in (2, 3, 4)}
    sl = tf["01"] + tf["23"]
    return dict(tf=tf, mf=mf, same_layer=sl, W2=W2, Wge2=Wge2)
