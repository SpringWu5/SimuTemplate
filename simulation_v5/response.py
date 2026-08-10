#!/usr/bin/env python3
"""response.py -- small-scintillator detector-level forward model (v5 STEP 5).

Closes the biggest v5 gap: track -> path -> Edep -> scintillation photons ->
SiPM PE -> electronics amplitude -> hardware threshold -> trigger hit.

  Edep_i     ~ Landau(mean = dEdx * rho * path_i)     (lognormal approx)
  N_PE_i     ~ Poson(Y_i * Edep_i)                    (Y_i = light yield PE/MeV)
  A_i        = g_i * N_PE_i + noise_i                 (noise ~ Normal(0, sigma_i))
  fired_i    = (A_i > thr_i) AND (Uniform < eff_i)

Per-channel parameters (i=0..3): g_i (relative gain), thr_i (threshold, PE),
sigma_i (noise RMS, PE), eff_i (intrinsic efficiency). Channels are NOT assumed
identical -- this is required to address the observed T02/T13 = 2.1 asymmetry.

Calibration is done in MIP units: a MIP crossing the block vertically deposits
E_MIP = dEdx*rho*(2*HZ). We expose thr_i / E_MIP as the hardware-threshold scan
variable (section 24). Global yield Y sets the absolute PE scale.
"""
import numpy as np
from . import geometry as G

DEDX = 2.0      # MeV/cm, MIP in plastic scintillator
RHO = 1.023     # g/cm^3
E_MIP_VERT = DEDX * RHO * (2 * G.HZ)   # ~6.1 MeV for a vertical crossing


def landau_edep(path_cm, rng, dedx=DEDX, rho=RHO):
    """Lognormal approximation of Landau energy deposition for given path."""
    mean = np.maximum(dedx * rho * path_cm, 1e-3)
    sigma = 0.20 * mean + 0.05
    s2 = np.log1p((sigma / mean) ** 2)
    mu = np.log(mean) - 0.5 * s2
    return rng.lognormal(mu, np.sqrt(np.maximum(s2, 1e-12)))


class SmallResponse:
    """Per-channel small-scintillator response model."""

    def __init__(self, Y=12.0, gain=None, thr_pe=None, noise_pe=2.0, eff=None):
        """Y: global light yield (PE/MeV). Per-channel overrides default to identical."""
        self.Y = Y
        self.gain = np.ones(4) if gain is None else np.asarray(gain, float)
        # threshold default: 0.2 MIP in PE
        thr_default = 0.2 * E_MIP_VERT * Y
        self.thr_pe = np.full(4, thr_default) if thr_pe is None else np.asarray(thr_pe, float)
        self.noise_pe = np.full(4, noise_pe) if np.isscalar(noise_pe) else np.asarray(noise_pe, float)
        self.eff = np.ones(4) if eff is None else np.asarray(eff, float)

    @classmethod
    def from_mip_threshold(cls, thr_mip, Y=12.0, gain=None, noise_pe=2.0, eff=None):
        thr_pe = np.full(4, thr_mip * E_MIP_VERT * Y) if np.isscalar(thr_mip) else np.asarray(thr_mip) * E_MIP_VERT * Y
        return cls(Y=Y, gain=gain, thr_pe=thr_pe, noise_pe=noise_pe, eff=eff)

    def respond(self, sample, rng):
        """Apply response to a geometric sample. Returns fired [N,4], npe [N,4], edep [N,4]."""
        N = sample["H"].shape[0]
        edep = np.zeros((N, 4)); npe = np.zeros((N, 4))
        for i, ch in enumerate(G.ALLCH):
            path = sample["paths"][ch]
            e = np.where(path > 0, landau_edep(np.where(path > 0, path, 1e-3), rng), 0.0)
            edep[:, i] = e
            npe[:, i] = np.where(path > 0, rng.poisson(self.Y * e), 0.0)
        amp = self.gain * npe + rng.normal(0, self.noise_pe, (N, 4))
        fired = (amp > self.thr_pe) & (rng.random((N, 4)) < self.eff)
        # a channel with no geometric hit cannot fire (no scintillation)
        fired &= sample["H"]
        return dict(fired=fired, npe=npe, amp=amp, edep=edep)

    def topology(self, resp):
        """From fired pattern -> exclusive M2 topology fractions + M3/M4 + same-layer."""
        H = resp["fired"]; M = H.sum(axis=1)
        ge2 = M >= 2; m2 = M == 2
        Wge2 = ge2.sum(); W2 = m2.sum()
        tf = {}
        for t in G.TOPO:
            a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
            tf[t] = float(np.sum(m2 & H[:, ia] & H[:, ib]) / W2) if W2 else 0.0
        mf = {f"M{k}": float(np.sum(M == k) / Wge2) if Wge2 else 0.0 for k in (2, 3, 4)}
        sl = tf["01"] + tf["23"]
        return dict(tf=tf, mf=mf, same_layer=sl, n2=W2, nge2=Wge2)
