#!/usr/bin/env python3
"""small_v6.py -- small-scintillator forward model with Q calibration (STEP 4).

Extends v5 response.py: path -> Edep(Landau) -> PE(Poisson) -> Q(charge proxy)
-> amplitude -> threshold -> fired. Adds per-channel gain g_i and a global
Edep->Q scale, so the asymmetry can be tested as threshold vs gain vs geometry.

Q calibration: Q_i = g_i * N_PE_i  (linear charge proxy; real hardware has
clipping but we use the unsaturated regime). A MIP vertical crossing gives
Q_MIP = g_i * Poisson(Y * E_MIP_vert).
"""
import numpy as np
from simulation_v5 import geometry as G
from simulation_v5.response import DEDX, RHO, landau_edep, E_MIP_VERT

Y_SMALL = 12.0   # PE/MeV for small scints (v5 calibration)


def small_edep_pe(paths, rng, Y=Y_SMALL):
    """paths: {ch: [N]} -> edep[N,4], npe[N,4]."""
    N = len(paths["0"])
    edep = np.zeros((N, 4)); npe = np.zeros((N, 4))
    for i, ch in enumerate(G.ALLCH):
        p = paths[ch]
        e = np.where(p > 0, landau_edep(np.where(p > 0, p, 1e-3), rng), 0.0)
        edep[:, i] = e
        npe[:, i] = np.where(p > 0, rng.poisson(Y * e), 0.0)
    return edep, npe


def fire_and_Q(npe, rng, gain, thr_pe, noise=2.0, geom_H=None):
    """Apply per-channel gain + threshold. Returns fired[N,4], Q[N,4], amp[N,4]."""
    N = npe.shape[0]
    amp = gain * npe + rng.normal(0, noise, (N, 4))
    fired = (amp > thr_pe)
    if geom_H is not None:
        fired &= geom_H
    Q = gain * npe   # charge proxy (pre-threshold)
    return fired, Q, amp


def asym_params(kind="thr", dx=0.20, base_thr_mip=0.5, gain_rel=None):
    """Build per-channel (gain, thr_pe) for a given asymmetry kind.
    kind='thr': left column threshold +dx; 'gain': left column gain -dx;
    'geom': no electronics asymmetry (geometry handles it)."""
    thr0 = base_thr_mip * E_MIP_VERT * Y_SMALL
    if kind == "thr":
        thr = np.array([thr0, thr0 * (1 + dx), thr0, thr0 * (1 + dx)])
        gain = np.ones(4)
    elif kind == "gain":
        thr = np.full(4, thr0)
        gain = np.array([1.0, 1.0 / (1 + dx), 1.0, 1.0 / (1 + dx)])
    else:
        thr = np.full(4, thr0); gain = np.ones(4)
    if gain_rel is not None:
        gain = gain * np.array(gain_rel)
    return gain, thr
