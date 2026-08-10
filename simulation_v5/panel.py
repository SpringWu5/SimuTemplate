#!/usr/bin/env python3
"""panel.py -- slab/panel SiPM response model (v5 STEP 9).

The slab is read out by 8 SiPM (Ch4..Ch11). A slab-crossing muon produces
scintillation light shared among the 8 SiPM. M8 = all 8 channels above an
offline threshold (coherent score). The v4 result used raw-photon thresholds;
here we add PDE photo-statistics + per-SiPM Poisson + electronics noise so the
M8 threshold maps to PE/electronics units.

  Edep_slab   = dEdx * rho * path_slab            (path up to 2*SLAB_Z=2cm)
  N_gamma     = Poson(Y_slab * Edep_slab)
  N_PE_i      ~ Poisson(N_gamma * pde * f_i)      (f_i = light-sharing frac, sum~1)
  fires_i     = N_PE_i + noise > thr_sipm
  M8          = all 8 fire  (coherent: min PE across 8 > thr)
"""
import numpy as np
from . import geometry as G
from .response import DEDX, RHO, landau_edep

N_SIPM = 8
# light-sharing fractions f4..f11 (from v4 optical: ~0.10-0.14, normalised)
F_SHARE = np.array([0.143, 0.143, 0.135, 0.137, 0.115, 0.100, 0.119, 0.110])
F_SHARE = F_SHARE / F_SHARE.sum()


def slab_edep(pslab, rng):
    return np.where(pslab > 0, landau_edep(np.where(pslab > 0, pslab, 1e-3), rng), 0.0)


def panel_pe(pslab, rng, Y_slab=400.0, pde=0.40):
    """Return [N,8] PE matrix for slab-crossing events (0 where no crossing)."""
    e = slab_edep(pslab, rng)
    N = pslab.shape[0]
    ngam = np.where(pslab > 0, rng.poisson(Y_slab * e), 0.0)
    pe = np.zeros((N, N_SIPM))
    for i in range(N_SIPM):
        pe[:, i] = np.where(pslab > 0, rng.poisson(ngam * pde * F_SHARE[i]), 0.0)
    return pe, e


def m8_mask(pe, thr_pe, noise=3.0, rng=None):
    """M8 = all 8 SiPM above thr_pe (after noise). Returns [N] bool + per-SiPM fired."""
    if rng is None:
        rng = np.random.default_rng(0)
    N = pe.shape[0]
    amp = pe + rng.normal(0, noise, pe.shape)
    fired = amp > thr_pe
    m8 = fired.all(axis=1)
    return m8, fired


def coherent_score(pe):
    """Total PE across 8 (proxy for offline coherent score)."""
    return pe.sum(axis=1)
