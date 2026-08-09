#!/usr/bin/env python3
"""
gen_stacked_muons.py -- produce Geant4 primary-muon JSONs for the stacked run.

O1 (muons_stacked.json) : real cosmic triggered tracks (n=2, L=10, gap=10) from
   the acceptance MC -- muons that geometrically fire >=2 small scints. Vertex on
   the generation plane (z=60 cm), momentum = unit direction x 3 GeV.
O0 (muons_stacked_o0.json): vertical muons over the +x/+5cm slab SiPM (Ch4),
   to reproduce the standalone slab local-SiPM baseline (~475 ph).
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import acceptance_mc as am

ROOT = "/lustre/neutrino/wujiacheng/simu_template"


def write_json(path, events):
    json.dump(events, open(path, "w"))
    print(f"wrote {path}: {len(events)} events")


def ev(eid, x, y, z, dx, dy, dz, E=3000.0):
    return {"event_id": eid, "particles_in": [], "particles_out": [],
            "particles_at_detector": [{"pdgid": 13, "x": x, "y": y, "z": z, "t": 0.0,
                                       "px": dx * E, "py": dy * E, "pz": dz * E}],
            "weights": {"volume": 1, "spectrum": 1.0, "interaction": 1, "survival": 1, "total": 1.0}}


def gen_O1(n=2.0, L=10.0, N=30_000_000, want=300, seed=101):
    rng = np.random.default_rng(seed)
    slab_min = np.array([-am.SLAB["hx"], -am.SLAB["hy"], -am.SLAB["hz"]])
    slab_max = np.array([+am.SLAB["hx"], +am.SLAB["hy"], +am.SLAB["hz"]])
    r = am.run_one(n, L, N, rng, slab_min, slab_max)
    M, H, exc, inc = am.patterns(r["hits"])
    idx = np.where(M >= 2)[0]
    pick = rng.choice(idx, size=min(want, len(idx)), replace=False)
    zplane = am.ZPLAN
    evs = []
    for k, i in enumerate(pick):
        dx, dy, dz = r["d"][i]
        evs.append(ev(k, r["P0"][i, 0], r["P0"][i, 1], zplane, dx, dy, dz))
    return evs


def gen_O0(n_ev=60, seed=7):
    rng = np.random.default_rng(seed)
    evs = []
    for k in range(n_ev):
        x = rng.uniform(7.0, 10.0)   # over +x edge, 3 cm inward
        y = rng.uniform(4.0, 6.0)    # +/-1 cm about the +5 cm SiPM (Ch4)
        evs.append(ev(k, x, y, 1.2, 0.0, 0.0, -1.0))
    return evs


if __name__ == "__main__":
    e1 = gen_O1()
    write_json(os.path.join(ROOT, "data", "muons_stacked.json"), e1)
    e0 = gen_O0()
    write_json(os.path.join(ROOT, "data", "muons_stacked_o0.json"), e0)
    # quick summary of O1 geometry
    import numpy as np
    pz = np.array([ev["particles_at_detector"][0]["pz"] for ev in e1])
    print(f"O1: {len(e1)} triggered cosmic tracks; |pz| mean={np.mean(np.abs(pz)):.0f} MeV")
