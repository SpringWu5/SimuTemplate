# Experiment Report — Small Scintillator Block vs Slab SiPM Yield

**Branch:** `spring-sipm-test`
**Date:** 2026-08-07
**Status:** complete

## 1. Objective & physical motivation

In the real detector a small scintillator block sits directly **on top of a slab
SiPM** as a light-yield booster. We compare, for a muon striking right above one
slab SiPM, how much light the **block's own SiPM** collects versus the **slab
SiPM under it** (and the other slab SiPMs). Two independent simulations, same
materials (EJ-200 `Scint`, ESR R=0.95, SiPM n=1.5), 6×6 mm active area, **no PDE**
(raw photons; true PE ≈ ×0.40).

## 2. Setup

- **Block (standalone):** 2×3×3 cm, 1 SiPM (6 mm) on a 2×3 side face (+Y),
  muon 1 GeV vertical through the 2×3 top → crosses **3 cm**. 300 muons.
- **Slab (standalone, sipm-test geometry):** 20×20×2 cm, 8 SiPMs (6 mm) on the
  edges. Muon 1 GeV vertical, restricted to the **2×3 cm footprint above the
  +X/+5 cm SiPM (channel 0)**: x∈[7,10] cm, y∈[4,6] cm → crosses **2 cm**.
  300 muons. This footprint is exactly where the block would sit.

## 3. Results (300 muons each, no PDE)

| Quantity | ph/mu | ph/MeV | Edep (MeV) |
|---|---|---|---|
| **Block SiPM** (3 cm path) | **605** | 105 | 5.74 |
| **Slab under-SiPM** (ch0, 2 cm) | **475** | **123** | 3.86 |
| Slab other-7 SiPMs (avg) | 5.6 | 1.4 | 3.86 |
| Slab all-8 SiPMs (avg) | 64.2 | 16.6 | 3.86 |

Figures: `figures/block_01_photons_per_muon.png`, `block_02_per_mev.png`,
`block_03_histogram.png`.

## 4. Findings

1. **Block gives more absolute signal: 605 vs 475 ph/mu (+27%)** — but this comes
   *entirely from extra material*: the block is 3 cm thick vs the slab's 2 cm
   (deposit 5.74 vs 3.86 MeV, +49%).
2. **Per deposited MeV, the slab SiPM under the muon is actually more efficient:
   123 vs 105 ph/MeV.** The block's face-coupled SiPM does **not** out-collect the
   slab edge SiPM that sits right under the muon; it is ~15 % lower per MeV.
   (The slab SiPM is on the edge immediately below the production point, so light
   has a very short path to it; the block's SiPM collects light spread through the
   full 3 cm height.)
3. **The other 7 slab SiPMs are negligible (~5.6 ph/mu)** for a muon above one
   SiPM; the slab average (64 ph/mu) is dominated by the single under-muon SiPM.
4. **True photoelectrons** (×PDE 0.40): block ≈ **242 PE/mu**, slab under-SiPM ≈
   **190 PE/mu**.

## 5. Conclusion

For a muon directly above a slab SiPM, **that slab SiPM already collects very
efficiently (~123 ph/MeV)**. Adding a 3 cm block on top increases the **absolute**
signal (+27 %, from 475→605 ph/mu) purely by adding 1 cm of scintillator — **not**
by improving light collection (the block's per-MeV efficiency, 105, is slightly
lower). So the block is a "more-material" booster, not a "better-coupling" one;
whether it is worth the mechanical complexity depends on whether the extra ~27 %
light (or ~130 PE) is needed for the physics threshold.

## 6. Caveats

- Two **standalone** simulations (block not physically stacked on the slab); in
  reality the muon traverses block (3 cm) **then** slab (2 cm), so a stacked
  geometry would give the block's light + the slab's light together.
- No PDE; numbers are raw photons. True PE ≈ ×0.40.
- 1 GeV vertical muons; ESR reflectivity assumed 0.95.
- Block face-SiPM dead rim treated as reflective ESR.

## 7. Reproduce

```bash
export SIMU_ENV=$PWD/env/inpac.sh && source "$SIMU_ENV"
cmake --build build -j8
# data/muons_block.json (2x3 top), data/muons_slab_undersipm.json (over ch0)
condor_submit <jobs for config_blocktest.yaml & config_sipmtest_c1_undersipm.yaml>
python3 scripts/analyze_block_vs_slab.py \
    --block build/output_block.root --slab build/output_slab_undersipm.root
```

## 8. Artifacts added

- `BlockSiPMTest` detector (`src/.../BlockSiPMTest.cc/.hh`, key `blocktest`)
- `config/config_blocktest.yaml`, `config/config_sipmtest_c1_undersipm.yaml`
- `data/muons_block.json`, `data/muons_slab_undersipm.json`
- `scripts/analyze_block_vs_slab.py`, this report + `figures/block_*.png`
