#!/usr/bin/env python3
"""panel_v6.py -- UNIFIED panel forward model, calibrated to Geant4 optical (STEP 2).

Replaces the v5 panel.py which used an uncalibrated Y_slab=400 (~23x too bright)
and a fixed-f_i Poisson that cannot reproduce the Geant4 overdispersion
(F=var/mean~4-7) and zero-photon tail.

Calibration source: Geant4 optical (output_stacked_v4.root, 120 slab-crossed
events). Per-SiPM rate ~1.7-2.4 photons/MeV, overdispersion F~3.7-6.7.

Model per slab-crossing event with Edep e:
  photons_i ~ NegBin(mean = rate_i * e, F = F_i)        per SiPM (overdispersed)
  N_PE_i    ~ Poisson(photons_i * PDE)                  photo-statistics
  amp_i     = gain_i * N_PE_i + noise_i                 electronics
  fires_i   = amp_i > thr_i
  M         = sum(fires)  ; M8 = (M==8)

This MUST reproduce the Geant4 M-distribution to be deemed valid (STEP 3).
"""
import os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_PATH = os.path.join(HERE, "optical_library", "geant4_calibration.json")
with open(CAL_PATH) as f:
    CAL = json.load(f)

NAMES = ["Ch4", "Ch5", "Ch8", "Ch9", "Ch6", "Ch7", "Ch11", "Ch10"]
RATE = np.array([CAL[n]["photons_per_MeV"] for n in NAMES])    # photons/MeV per SiPM
FAC = np.array([CAL[n]["F"] for n in NAMES])                    # overdispersion var/mean


def _nb_sample(mean, F, rng, size=None):
    """Negative Binomial with given mean and overdispersion F=var/mean.
    p = 1/F, n = mean/(F-1). Sample via Gamma-Poisson mixture."""
    p = 1.0 / F
    n = mean / (F - 1.0)
    n = np.clip(n, 1e-6, None)
    lam = rng.gamma(n, (1 - p) / p, size=mean.shape if size is None else size)
    return rng.poisson(lam)


def panel_photons(edep_MeV, rng):
    """[N] slab Edep -> [N,8] raw optical photons (overdispersed, Geant4-calibrated)."""
    N = edep_MeV.shape[0]
    out = np.zeros((N, 8))
    crossed = edep_MeV > 0
    for i in range(8):
        m = np.where(crossed, RATE[i] * edep_MeV, 0.0)
        out[:, i] = _nb_sample(m, FAC[i], rng)
    out[~crossed] = 0
    return out


def panel_pe(edep_MeV, rng, pde=0.40):
    """[N] Edep -> [N,8] PE (PDE photo-statistics on raw photons)."""
    ph = panel_photons(edep_MeV, rng)
    return np.where(ph > 0, rng.poisson(ph * pde), 0.0), ph


def panel_response(edep_MeV, rng, pde=0.40, gain=None, noise_pe=0.5, thr_pe=None):
    """Full response: photons -> PE -> amp -> fired. Returns dict with M, M8, pe, amp."""
    pe, ph = panel_pe(edep_MeV, rng, pde=pde)
    g = np.ones(8) if gain is None else np.asarray(gain)
    amp = g * pe + rng.normal(0, noise_pe, pe.shape)
    thr = np.zeros(8) if thr_pe is None else np.asarray(thr_pe)
    fired = amp > thr[None, :]
    crossed = (edep_MeV > 0)[:, None]
    fired &= crossed
    M = fired.sum(axis=1)
    return dict(pe=pe, photons=ph, amp=amp, fired=fired, M=M, M8=(M == 8),
                crossed=edep_MeV > 0)
