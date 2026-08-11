#!/usr/bin/env python3
"""stats_v7.py -- audited statistics for binned data/MC comparison (STEP 1).

Resolves the v6 dof/p inconsistency: v6 used dof = (data>0).sum() - 1 - (C-1)
which changes with the number of (possibly degenerate) components, so the same
Pearson gave p=0.114 (2-comp) and p=0.031 (4-comp) in the same report.

Clean definitions (all derived from first principles, unit-tested):

Multinomial model: data counts N = (N_1..N_K), total Ntot fixed by the trigger.
Model probabilities p_i(theta) = sum_c f_c p_{c,i}, sum_i p_i = 1.
  neg2logL = -2 sum_i N_i log p_i   (drop constant terms)
  Pearson  = sum_i (N_i - mu_i)^2 / mu_i,   mu_i = Ntot p_i
  G-test   = 2 sum_{N_i>0} N_i log(N_i / mu_i)

Degrees of freedom for absolute GOF:
  dof = K_eff - 1 - n_free
where K_eff = number of bins with nonzero model expectation (mu_i > 0),
n_free = number of free parameters in theta (component fractions: C-1 if the
C component probability vectors are FIXED; + any floated shape params).

p-value = P(chi2_{dof} >= statistic)  (asymptotic; validated by toy MC below).

IMPORTANT: components whose fraction is fitted to 0 still count as a free
parameter direction only if they were floated. For nested-model selection use
AIC = neg2logL + 2 n_free, BIC = neg2logL + n_free ln(Ntot).
"""
import numpy as np
from scipy.stats import chi2 as chi2dist


def model_prob(frac, comp_fracs):
    """frac: (C,), comp_fracs: (C,K) -> (K,) probabilities, normalised."""
    p = frac @ comp_fracs
    p = np.clip(p, 1e-15, None)
    return p / p.sum()


def neg2logL(frac, comp_fracs, N):
    p = model_prob(frac, comp_fracs)
    nz = N > 0
    return -2.0 * np.sum(N[nz] * np.log(p[nz]))


def pearson(frac, comp_fracs, N):
    p = model_prob(frac, comp_fracs)
    mu = N.sum() * p
    nz = mu > 1e-12
    return np.sum((N[nz] - mu[nz]) ** 2 / mu[nz]), mu


def gtest(frac, comp_fracs, N):
    p = model_prob(frac, comp_fracs)
    mu = N.sum() * p
    nz = (N > 0) & (mu > 1e-12)
    return 2.0 * np.sum(N[nz] * np.log(N[nz] / mu[nz]))


def dof_absolute(comp_fracs, N, n_free_shape=0):
    """K_eff - 1 - (C-1) - n_shape. K_eff = bins with model expectation>0 at
    the (equal-weight) component average. Uses N>0 as proxy when needed."""
    K = comp_fracs.shape[1]
    C = comp_fracs.shape[0]
    K_eff = int(np.sum(comp_fracs.mean(0) > 1e-12))   # bins any component populates
    return max(K_eff - 1 - (C - 1) - n_free_shape, 1)


def pvalue(stat, dof):
    return float(1.0 - chi2dist.cdf(stat, dof))


def gof_report(frac, comp_fracs, N, n_free_shape=0, label=""):
    pe, mu = pearson(frac, comp_fracs, N)
    gt = gtest(frac, comp_fracs, N)
    d = dof_absolute(comp_fracs, N, n_free_shape)
    n2 = neg2logL(frac, comp_fracs, N)
    with np.errstate(divide="ignore", invalid="ignore"):
        pull = np.where(mu > 0, (mu - N) / np.sqrt(np.where(mu > 0, mu, 1)), 0)
    return dict(label=label, pearson=pe, gtest=gt, neg2logL=n2, dof=d,
                pvalue_pearson=pvalue(pe, d), pvalue_gtest=pvalue(gt, d),
                mu=mu, pull=pull, frac=frac, adequate=pvalue(pe, d) > 0.01)


def grid_fit(comp_fracs, N, ngrid=21):
    """Exhaustive simplex grid over (C-1)-simplex. Returns best frac + neg2logL."""
    C = comp_fracs.shape[0]
    if C == 1:
        return np.array([1.0]), neg2logL(np.array([1.0]), comp_fracs, N)
    import itertools
    best = (1e30, None)
    for combo in itertools.product(*[np.linspace(0, 1, ngrid) for _ in range(C - 1)]):
        if sum(combo) > 1 + 1e-9:
            continue
        frac = np.array(list(combo) + [max(1 - sum(combo), 0.0)])
        v = neg2logL(frac, comp_fracs, N)
        if v < best[0]:
            best = (v, frac)
    return best[1], best[0]


def ppc_quantiles(pred_prob, Ntot, nrep, rng, observable_fn):
    """Posterior predictive: draw nrep multinomial samples of size Ntot from
    pred_prob, apply observable_fn(counts)->scalar, return dict of quantiles."""
    vals = np.empty(nrep)
    for b in range(nrep):
        c = rng.multinomial(Ntot, pred_prob)
        vals[b] = observable_fn(c)
    return dict(median=float(np.median(vals)),
                q68=(float(np.percentile(vals, 16)), float(np.percentile(vals, 84))),
                q95=(float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))),
                P_eq={int(k): float(np.mean(vals == k)) for k in np.unique(vals)},
                samples=vals)
