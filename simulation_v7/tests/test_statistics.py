#!/usr/bin/env python3
"""test_statistics.py -- unit tests for stats_v7 (STEP 1 statistics audit).

Validates against analytic truth:
  - dof_absolute matches K-C formula.
  - Under the TRUE model, Pearson p-values are ~Uniform(0,1) (calibration).
  - grid_fit recovers input fractions on toy data.
  - ppc_quantiles covers the truth.
"""
import os, sys, unittest
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT); sys.path.insert(0, REPO)
from simulation_v7 import stats_v7 as S


class TestDOF(unittest.TestCase):
    def test_dof_formula(self):
        # 6 bins, 2 components -> dof = 6-1-(2-1) = 4
        comp = np.array([[0.5, 0.3, 0.1, 0.05, 0.03, 0.02],
                         [0.1, 0.1, 0.2, 0.2, 0.2, 0.2]])
        N = np.array([30, 20, 15, 12, 10, 8], dtype=float)
        self.assertEqual(S.dof_absolute(comp, N), 4)

    def test_dof_zero_populated_bin(self):
        # if a component has a zero column, K_eff drops
        comp = np.array([[0.5, 0.5, 0.0, 0.0],
                         [0.4, 0.4, 0.2, 0.0]])
        N = np.array([40, 40, 10, 0], dtype=float)
        # K_eff (mean>0) = 3 -> dof = 3-1-1 = 1
        self.assertEqual(S.dof_absolute(comp, N), 1)


class TestPvalueCalibration(unittest.TestCase):
    """Under the TRUE model, Pearson p-value must be ~Uniform(0,1)."""

    def test_pvalue_uniform_under_truth(self):
        rng = np.random.default_rng(123)
        p_true = np.array([0.30, 0.22, 0.20, 0.10, 0.10, 0.08])
        comp = p_true[None, :]   # single component = truth
        Ntot = 255
        pvals = []
        for _ in range(2000):
            N = rng.multinomial(Ntot, p_true).astype(float)
            gr = S.gof_report(np.array([1.0]), comp, N)
            pvals.append(gr["pvalue_pearson"])
        pvals = np.array(pvals)
        # mean of Uniform(0,1) = 0.5; check within tolerance
        self.assertAlmostEqual(np.mean(pvals), 0.5, delta=0.04)
        # fraction below 0.05 ~ 0.05 (Type-I rate)
        self.assertAlmostEqual(np.mean(pvals < 0.05), 0.05, delta=0.02)

    def test_pvalue_rejects_wrong_model(self):
        rng = np.random.default_rng(7)
        p_true = np.array([0.30, 0.22, 0.20, 0.10, 0.10, 0.08])
        p_wrong = np.array([0.10, 0.10, 0.20, 0.20, 0.20, 0.20])
        comp_wrong = p_wrong[None, :]
        reject = 0
        for _ in range(500):
            N = rng.multinomial(255, p_true).astype(float)
            gr = S.gof_report(np.array([1.0]), comp_wrong, N)
            if gr["pvalue_pearson"] < 0.01:
                reject += 1
        # wrong model rejected most of the time
        self.assertGreater(reject / 500, 0.8)


class TestFitRecovery(unittest.TestCase):
    def test_recovers_input_fractions(self):
        rng = np.random.default_rng(42)
        c1 = np.array([0.10, 0.05, 0.30, 0.30, 0.15, 0.10])
        c2 = np.array([0.35, 0.30, 0.10, 0.10, 0.10, 0.05])
        f_true = np.array([0.4, 0.6])
        p = f_true @ np.stack([c1, c2])
        N = rng.multinomial(2000, p).astype(float)
        comp = np.stack([c1, c2])
        frac, _ = S.grid_fit(comp, N, ngrid=41)
        self.assertAlmostEqual(frac[0], 0.4, delta=0.05)
        self.assertAlmostEqual(frac[1], 0.6, delta=0.05)


class TestPPC(unittest.TestCase):
    def test_ppc_covers_truth(self):
        rng = np.random.default_rng(9)
        p = np.array([0.3, 0.2, 0.2, 0.15, 0.1, 0.05])
        obs = lambda c: int(np.sum(c[:2]))   # count in first two bins
        q = S.ppc_quantiles(p, 255, 3000, rng, obs)
        true_val = 255 * (p[0] + p[1])
        self.assertLess(q["q95"][0], true_val + 1)
        self.assertGreater(q["q95"][1], true_val - 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
