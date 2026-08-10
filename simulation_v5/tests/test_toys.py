#!/usr/bin/env python3
"""test_toys.py -- unit tests for v5 toy models.

Run:  python -m pytest simulation_v5/tests/test_toys.py -v
  or:  python -m unittest simulation_v5.tests.test_toys

Each test has an analytic / constructive prediction so a regression (like the
v4 correlated bug that gave same-layer=0) fails loudly.
"""
import os, sys
import numpy as np
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)            # simulation_v5/
REPO = os.path.dirname(ROOT)            # simu_template/
sys.path.insert(0, REPO)

from simulation_v5 import geometry as G
from simulation_v5 import toys as T
from simulation_v5 import generator as GEN


def beam_through(ch, n, rng, zplane=10.0, theta_deg=0.0):
    """Construct n rays aimed at block `ch` centre, near-vertical (hits whole column)."""
    boxes = G.block_boxes()
    bmin, bmax = boxes[ch]
    cx = 0.5 * (bmin[0] + bmax[0]); cy = 0.5 * (bmin[1] + bmax[1])
    x = cx + rng.uniform(-G.HX * 0.6, G.HX * 0.6, n)
    y = cy + rng.uniform(-G.HY * 0.6, G.HY * 0.6, n)
    P0 = np.stack([x, y, np.full(n, zplane)], axis=1)
    th = np.deg2rad(theta_deg); cT = np.cos(th); sT = np.sin(th)
    d = np.tile([sT, 0.0, -cT], (n, 1))
    return P0, d


def horizontal_upper_beam(n, rng, direction=+1):
    """Horizontal rays in the upper layer (z=+L/2) from the gap going +/-x.

    direction=+1 => hit Ch0 only (upper-right); -1 => hit Ch1 only (upper-left).
    """
    z = G.LSEP / 2.0
    x0 = np.zeros(n)
    y0 = rng.uniform(-G.HY * 0.6, G.HY * 0.6, n)
    P0 = np.stack([x0, y0, np.full(n, z)], axis=1)
    d = np.tile([float(direction), 0.0, 0.0], (n, 1))
    return P0, d


class TestSingleMuon(unittest.TestCase):
    def test_M3_M4_zero(self):
        rng = np.random.default_rng(1)
        s = GEN.draw_unbiased(2_000_000, n=2.0, rng=rng)
        M = s["M"]
        self.assertEqual(int((M == 3).sum()), 0)
        self.assertEqual(int((M == 4).sum()), 0)

    def test_topology_normalisation(self):
        # use IS sampler (concentrates near detector) to get same-layer stats
        rng = np.random.default_rng(2)
        s = GEN.sample_single(2_000_000, n=2.0, rng=rng)
        w = s["w"]
        H = s["H"]; M = s["M"]
        m2 = M == 2; W2 = w[m2].sum()
        tf = {}
        for t in G.TOPO:
            a, b = G.TOP_CH[t]; ia = G.ALLCH.index(a); ib = G.ALLCH.index(b)
            sel = m2 & H[:, ia] & H[:, ib]
            tf[t] = w[sel].sum() / W2
        self.assertAlmostEqual(sum(tf.values()), 1.0, places=2)
        sl = tf["01"] + tf["23"]
        self.assertGreater(sl, 0.02, "IS sampler must recover same-layer ~6%")
        self.assertLess(sl, 0.15)


class TestCorrelatedRaisesSameLayer(unittest.TestCase):
    """THE critical regression test: forcing track2 onto the same-layer
    neighbour MUST raise same-layer fraction. v4 returned 0 (bug)."""

    def test_forced_neighbour_same_layer(self):
        """Constructive test: track1 hits Ch0 (upper-right) only, track2 hits
        Ch1 (upper-left) only => OR must be U01 ~1. (v4 returned 0.)"""
        rng = np.random.default_rng(7)
        P1, d1 = horizontal_upper_beam(20000, rng, direction=+1)   # Ch0
        P2, d2 = horizontal_upper_beam(20000, rng, direction=-1)   # Ch1
        boxes = G.block_boxes()
        H1 = G.hit_matrix(G.propagate(P1, d1, boxes)[0])
        H2 = G.hit_matrix(G.propagate(P2, d2, boxes)[0])
        H = H1 | H2
        M = H.sum(axis=1)
        u01 = np.mean((H[:, 0]) & (H[:, 1]) & (M == 2))
        self.assertGreater(u01, 0.95, "forced same-layer neighbour must give U01~1")

    def test_correlated_pcorr_monotonic(self):
        """With det_x offset (along the inter-block gap), same-layer must rise
        above the single baseline as p_corr increases (v4 was flat ~0)."""
        iss = GEN.sample_single(4_000_000, n=2.0, rng=np.random.default_rng(3))
        s = GEN.resample_triggered(iss, 300_000, np.random.default_rng(33), Mmin=1)
        sl = []
        for pc in [0.0, 0.3, 0.6, 1.0]:
            Hc, _, _ = T.correlated_two_track(
                s, p_corr=pc, s_cm=12.0, sigma_deg=3.0,
                rng=np.random.default_rng(31 + int(pc * 10)), offset_mode="det_x")
            sl.append(T.H_to_counts(Hc)["same_layer"])
        self.assertGreater(max(sl[1:]), sl[0] + 0.05, "det_x corr must raise same-layer")

    def test_correlated_offset_matters(self):
        """s_cm=0 must NOT raise same-layer; s_cm~gap with det_x does."""
        iss = GEN.sample_single(3_000_000, n=2.0, rng=np.random.default_rng(4))
        s = GEN.resample_triggered(iss, 300_000, np.random.default_rng(43), Mmin=1)
        H0, _, _ = T.correlated_two_track(s, 1.0, 0.0, 1.0, np.random.default_rng(41))
        H1, _, _ = T.correlated_two_track(s, 1.0, 12.0, 3.0, np.random.default_rng(42),
                                          offset_mode="det_x")
        sl0 = T.H_to_counts(H0)["same_layer"]
        sl1 = T.H_to_counts(H1)["same_layer"]
        self.assertLessEqual(sl0, sl1 + 0.02)
        self.assertGreater(sl1, sl0 + 0.05, "gap-sized det_x offset must raise same-layer")


class TestIndependentTwoTrack(unittest.TestCase):
    def test_raises_M3_M4(self):
        iss = GEN.sample_single(3_000_000, n=2.0, rng=np.random.default_rng(5))
        s = GEN.resample_triggered(iss, 300_000, np.random.default_rng(53))
        c_single = T.H_to_counts(s["H"])
        Hc, _ = T.independent_two_track(s, p_multi=1.0, rng=np.random.default_rng(50))
        Mc = Hc.sum(axis=1)
        c_multi = T.H_to_counts(Hc)
        self.assertGreater(int((Mc == 3).sum()), 0, "independent 2-track must produce M3")
        self.assertGreater(int((Mc == 4).sum()), 0, "independent 2-track must produce M4")
        self.assertGreater(c_multi["mf"]["M3"], c_single["mf"]["M3"])


class TestFakeModels(unittest.TestCase):
    def test_F1_random_produces_all_topologies(self):
        rng = np.random.default_rng(6)
        bits = T.fake_random(200_000, 0.3, rng)
        c = T.H_to_counts(bits)
        # all six topologies get nonzero fraction; M3/M4 present
        for t in G.TOPO:
            self.assertGreater(c["tf"][t], 1e-4)
        self.assertGreater(c["mf"]["M3"], 0.05)

    def test_F1_uniform_topology(self):
        rng = np.random.default_rng(8)
        bits = T.fake_random(500_000, 0.5, rng)
        c = T.H_to_counts(bits)
        # uniform random bits => each M2 topology ~1/6
        for t in G.TOPO:
            self.assertAlmostEqual(c["tf"][t], 1 / 6, places=2)


class TestAnalyticOR(unittest.TestCase):
    def test_two_single_hit_or(self):
        """OR of pattern {Ch0} and {Ch2} => M2=1, and OR of {Ch0},{Ch0}=>M1."""
        # construct explicitly
        H = np.zeros((4, 4), dtype=bool)
        H[0] = [1, 0, 0, 0]; H[1] = [0, 1, 0, 0]; H[2] = [1, 1, 0, 0]; H[3] = [1, 0, 1, 0]
        c = T.H_to_counts(H)
        # among M2 rows: {0,1}=U01 and {0,2}=T02 => each 1/2
        self.assertAlmostEqual(c["tf"]["01"], 0.5)
        self.assertAlmostEqual(c["tf"]["02"], 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
