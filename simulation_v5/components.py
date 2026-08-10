#!/usr/bin/env python3
"""components.py -- physically-defined mixture components (v5).

Each component Ck predicts observables:
  p_topo[6]   P(topology | M2)               (six exclusive topologies)
  p_M3, p_M4  P(M3|M>=2), P(M4|M>=2)
  p_panel[t]  P(panel M8 | topology t)       (conditional; hardware-level later)

Components are NOT the vague v4 "single/corr/fake". They are:
  C1 single cosmic muon              (from IS-resampled triggered sample)
  C2 correlated multi-particle       (geometric two-track, real rays)
  C3 one slab-crossing particle +    (S2 mechanism for same-layer M8)
     additional small hit/secondary
  C4 small-electronics crosstalk     (F2: same-layer neighbour copy)
  F1 random trigger-bit fake         (uniform topology)
  F3 physical secondary-like         (real ray, plastic Edep, may miss slab)
"""
import numpy as np
from . import geometry as G
from . import toys as T


def topo_vector(H, w=None):
    """[N,4] hit matrix -> 6-vector of P(topo|M2) + (p_M3,p_M4)."""
    c = T.H_to_counts(H, w=w)
    v = np.array([c["tf"][t] for t in G.TOPO])
    return v, c["mf"]["M3"], c["mf"]["M4"]


def component_single(sample):
    """C1: single cosmic muon. sample = resampled triggered (unweighted)."""
    v, m3, m4 = topo_vector(sample["H"])
    return dict(name="C1_single", p_topo=v, p_M3=m3, p_M4=m4,
                p_panel={t: 0.0 for t in G.TOPO})  # filled later by panel model


def component_correlated(sample, p_corr, s_cm, sigma_deg, offset_mode="transverse",
                         rng=None, panel_fn=None):
    """C2: correlated two/multi-particle (geometric)."""
    if rng is None:
        rng = np.random.default_rng(0)
    H, _, info = T.correlated_two_track(sample, p_corr, s_cm, sigma_deg, rng,
                                        offset_mode=offset_mode)
    v, m3, m4 = topo_vector(H)
    p_panel = {t: 0.0 for t in G.TOPO}
    return dict(name="C2_corr", p_topo=v, p_M3=m3, p_M4=m4, p_panel=p_panel, H=H, info=info)


def component_fake_uniform():
    """F1: random trigger-bit fake -> uniform 1/6 topology, M3/M4 nonzero."""
    v = np.full(6, 1 / 6)
    # rough M3/M4 for uniform random bits with p~0.5
    return dict(name="F1_fake_random", p_topo=v,
                p_M3=0.0, p_M4=0.0, p_panel={t: 0.0 for t in G.TOPO})


def component_fake_secondary(sample, p_sec, s_cm, rng=None):
    """F3: physical secondary-like (real ray, plastic Edep, usually misses slab)."""
    if rng is None:
        rng = np.random.default_rng(0)
    H, info = T.fake_secondary_geom(sample, p_sec, s_cm, rng)
    v, m3, m4 = topo_vector(H)
    return dict(name="F3_secondary", p_topo=v, p_M3=m3, p_M4=m4,
                p_panel={t: 0.0 for t in G.TOPO}, H=H, info=info)


def component_electronics_copy(sample, p_copy, rng=None):
    """C4/F2: same-layer electronics crosstalk. If a channel fires, its same-layer
    neighbour copies with prob p_copy (broad amplitude ratio in response model)."""
    if rng is None:
        rng = np.random.default_rng(0)
    H = sample["H"].copy()
    N = H.shape[0]
    for ch, neigh in T.SAME_LAYER_NEIGH.items():
        ci = G.ALLCH.index(ch); ni = G.ALLCH.index(neigh)
        fires = H[:, ci] & (rng.random(N) < p_copy)
        H[fires, ni] = True
    v, m3, m4 = topo_vector(H)
    return dict(name="C4_xtalk", p_topo=v, p_M3=m3, p_M4=m4,
                p_panel={t: 0.0 for t in G.TOPO}, H=H)


def stack_topo(comp_list):
    """List of component dicts -> (C,6) array of topology vectors."""
    return np.array([c["p_topo"] for c in comp_list])
