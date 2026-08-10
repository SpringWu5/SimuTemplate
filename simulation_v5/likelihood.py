#!/usr/bin/env python3
"""likelihood.py -- multinomial mixture fitter for six-topology data (v5).

The v4 mixture was BUGGY: it minimised sum((mix-data)^2 / data_fraction) where
the denominator was a fraction (~0.1) instead of the multinomial variance, so
chi2 was artificially ~0.2 while the bar plot visibly mismatched. This module
rebuilds the fit from scratch with a correct likelihood.

Data vector: event COUNTS  N = (01,23,02,13,03,12) = (78,57,52,25,25,18).
Model:       p_i(theta) = sum_c f_c * p_{c,i}     (f_c >= 0, sum f_c = 1)
Likelihood:  Multinomial  logL = sum_i N_i log p_i
Objective:   -2 log L  (Wilks: Delta(-2logL) ~ chi2_{dof})

Diagnostics on the best fit:
  predicted counts  mu_i = Ntot * p_i
  pulls             (mu_i - N_i)/sqrt(mu_i)
  Pearson chi2      sum (N_i-mu_i)^2/mu_i
  deviance G        2 sum N_i log(N_i/mu_i)     (G-test)
If the reported -2logL looks good but pulls/G-test are large => BUG (v4 symptom).
"""
import numpy as np
from . import geometry as G

TOPO = G.TOPO
DATA_COUNTS = np.array([78, 57, 52, 25, 25, 18], dtype=float)
NTOT = DATA_COUNTS.sum()


def neg2logL_multinomial(frac, comp_fracs, N=DATA_COUNTS, eps=1e-12):
    """frac: (C,) component weights; comp_fracs: (C,6) per-component topology fractions.
    Returns -2 * sum_i N_i log( sum_c frac_c * comp_{c,i} )."""
    p = frac @ comp_fracs                      # (6,)
    p = np.clip(p, eps, None)
    p = p / p.sum()                            # renormalise (guard)
    return -2.0 * np.sum(N * np.log(p))


def predicted_counts(frac, comp_fracs, Ntot=NTOT):
    p = frac @ comp_fracs; p = p / p.sum()
    return Ntot * p, p


def diagnostics(frac, comp_fracs, N=DATA_COUNTS):
    mu, p = predicted_counts(frac, comp_fracs, N.sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        pull = (mu - N) / np.sqrt(np.where(mu > 0, mu, 1))
    pearson = np.sum((N - mu) ** 2 / np.where(mu > 0, mu, 1))
    nz = N > 0
    deviance_G = 2.0 * np.sum(N[nz] * np.log(N[nz] / mu[nz]))
    n2ll = -2.0 * np.sum(N[nz] * np.log(p[nz]))
    return dict(pred=mu, frac=p, pull=pull, pearson=pearson,
                deviance_G=deviance_G, neg2logL=n2ll)


def fit_grid(comp_fracs, ngrid=41, N=DATA_COUNTS):
    """Exhaustive simplex grid search over (C-1)-simplex. Returns best dict +
    full -2logL array + grid points (for ternary/profile plots)."""
    C = comp_fracs.shape[0]
    assert C == 3, "fit_grid supports 3 components (ternary); use fit_general for more"
    fs = np.linspace(0, 1, ngrid)
    pts = []; n2 = []
    for i, fa in enumerate(fs):
        for j, fb in enumerate(fs):
            fc = 1 - fa - fb
            if fc < -1e-9:
                continue
            fc = max(fc, 0.0)
            frac = np.array([fa, fb, fc])
            pts.append(frac)
            n2.append(neg2logL_multinomial(frac, comp_fracs, N))
    pts = np.array(pts); n2 = np.array(n2)
    k = np.argmin(n2)
    best_frac = pts[k]
    diag = diagnostics(best_frac, comp_fracs, N)
    return dict(best=best_frac, n2=n2, pts=pts,
                best_n2ll=diag["neg2logL"], diag=diag)


def confidence_interval_1d(comp_fracs, best_frac, comp_idx, N=DATA_COUNTS, ngrid=200):
    """Profile likelihood 1sigma/2sigma CL on f_{comp_idx} by profiling others.
    Returns (fs, n2ll_profile, lo1, hi1, lo2, hi2)."""
    C = comp_fracs.shape[0]
    fs = np.linspace(0, 1, ngrid)
    prof = np.full(ngrid, np.inf)
    for i, fval in enumerate(fs):
        # scan remaining components on a simplex slice
        rest = np.linspace(0, 1, 80); best = np.inf
        for r in rest:
            frac = np.zeros(C); frac[comp_idx] = fval
            others = [x for x in range(C) if x != comp_idx]
            rem = 1 - fval
            if C == 3:
                frac[others[0]] = rem * r; frac[others[1]] = rem * (1 - r)
                if frac[others[1]] < -1e-9:
                    continue
                frac = np.clip(frac, 0, None); frac /= frac.sum()
                v = neg2logL_multinomial(frac, comp_fracs, N)
                if v < best:
                    best = v
        prof[i] = best
    prof -= prof.min()
    # 1sigma: Delta(-2logL) <= 3.84 (chi2_1); 2sigma: <= 5.99 ... use 1-param profile
    lo1 = fs[prof <= 3.84].min(); hi1 = fs[prof <= 3.84].max()
    lo2 = fs[prof <= 5.99].min() if np.any(prof <= 5.99) else 0.0
    hi2 = fs[prof <= 5.99].max() if np.any(prof <= 5.99) else 1.0
    return fs, prof, lo1, hi1, lo2, hi2


def fit_general(comp_fracs, N=DATA_COUNTS, ngrid=21):
    """Simplex grid for C>3 components (coarser). Returns best frac + diag."""
    C = comp_fracs.shape[0]
    from itertools import product
    grids = [np.linspace(0, 1, ngrid) for _ in range(C - 1)]
    best = (np.inf, None)
    for combo in product(*grids):
        if sum(combo) > 1 + 1e-9:
            continue
        frac = np.array(list(combo) + [max(1 - sum(combo), 0.0)])
        v = neg2logL_multinomial(frac, comp_fracs, N)
        if v < best[0]:
            best = (v, frac)
    return dict(best=best[1], diag=diagnostics(best[1], comp_fracs, N), best_n2ll=best[0])


def bootstrap_components(comp_samples, N=DATA_COUNTS, nboot=400, rng=None):
    """Bootstrap CI on best-fit fractions. comp_samples: list of (B,6) arrays of
    bootstrap-resampled component fraction vectors. Returns per-component
    lo/hi at 68% from refitting each bootstrap replicate."""
    if rng is None:
        rng = np.random.default_rng(0)
    B = comp_samples[0].shape[0]; C = len(comp_samples)
    fits = np.zeros((nboot, C))
    for b in range(nboot):
        comp_fracs = np.array([comp_samples[c][rng.integers(B)] for c in range(C)])
        r = fit_grid(comp_fracs, ngrid=21, N=N)
        fits[b] = r["best"]
    lo = np.percentile(fits, 16, axis=0); hi = np.percentile(fits, 84, axis=0)
    return dict(fits=fits, lo=lo, hi=hi, median=np.median(fits, axis=0))
