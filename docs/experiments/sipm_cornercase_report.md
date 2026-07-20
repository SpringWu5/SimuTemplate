# Experiment Report — Corner/Edge Incidence: 6 mm vs 3 mm SiPM

**Branch:** `spring-sipm-test`
**Date:** 2026-07-20
**Status:** complete
**Predecessor:** `sipm_sizing_report.md` (established C1≈C3, C2 = C1/4 on a coarse interior grid)

## 1. Objective

The sizing study averaged over a coarse interior grid. This experiment stress-tests
the **3 mm SiPM at geometrically unfavourable positions** (slab edges and corners)
to answer: does the 3 mm signal degrade *disproportionately* relative to the
6 mm, or is the 1/4-light deficit purely a constant area scaling?

- **H1 (pure area):** C2 = C1/4 everywhere; identical attenuation behaviour.
- **H2 (extra degradation):** C2 falls off faster near edges/corners; dead zones appear.

## 2. Setup

- **Detector / configs:** `SingleSlabSiPMTest` (`sipmtest`), single slab
  20×20×2 cm, 8 unit-SiPM sites (2 per edge at ±5 cm). Only **C1 (6×6 mm active)**
  and **C2 (3×3 mm active)** are compared (C3 ≈ C1 already shown). No PDE applied
  (pure geometric, comparable to the prior study).
- **Muon source:** 1 GeV vertical μ⁻. **11×11 main grid** (x,y ∈ {−10,…,+10} cm,
  step 2 cm, includes the 4 corners) **+ 20 corner-densification points**
  (±9,±9 / ±9.5,±9.5 / ±10,±9 / ±9,±10 / ±9.5,±8 around each corner) →
  **141 positions × 10 = 1410 events / config**.
- Two HTCondor jobs, ExitCode 0.

## 3. Results

| Metric | C1 (6 mm) | C2 (3 mm) |
|---|---|---|
| Events | 1410 | 1410 |
| Mean collected photons / event | 69.1 | 17.5 |
| Collected photons / MeV | 24.0 | 6.1 |
| **C2/C1 overall** | — | **0.253** |
| Catchment attenuation λ (mm) | 58 | 62 |
| Per-position min / p5 / p50 (photons) | 0.1 / 2.9 / 62.0 | 0.0 / 0.4 / 15.9 |
| Position-reconstruction RMS x / y (cm) | 3.8 / 3.7 | 4.0 / 3.9 |

**C2/C1 ratio by region** (constant ⇒ no extra degradation):

| region | C1 (ph/evt) | C2 (ph/evt) | C2/C1 |
|---|---|---|---|
| interior | 83.4 | 21.4 | 0.257 |
| edge | 84.6 | 21.2 | 0.251 |
| corner | 25.4 | 6.3 | **0.247** |

### Figures (`docs/experiments/figures/corner_*.png`)
1. `corner_01_response_maps.png` — collected photons vs (x,y), C1 & C2
2. `corner_02_degradation_ratio.png` — C2/C1 ratio map (≈ 0.25 everywhere)
3. `corner_03_catchment.png` — single-SiPM R(d) + exponential λ
4. `corner_04_regions.png` — interior / edge / corner means
5. `corner_05_percentiles.png` — per-position photon-yield distribution
6. `corner_06_coverage.png` — fraction of positions with signal ≥ T (parameter-free)
7. `corner_07_c1_vs_c2.png` — per-position C1 vs C2 scatter
8. `corner_08_reconstruction.png` — centroid-based position reconstruction

## 4. Findings

1. **H1 confirmed — the 3 mm SiPM does NOT degrade disproportionately.** The
   C2/C1 ratio is 0.247–0.257 across interior, edge and corner — essentially
   constant at the pure-area value (¼). The catchment attenuation length is even
   marginally longer for C2 (62 vs 58 mm, within uncertainty). Distributing or
   shrinking the active area scales the signal uniformly; it does **not** create
   extra position-dependent loss.
2. **Both configs lose ~70 % of their signal at corners** (corner ≈ 0.30 ×
   interior). This is a geometry effect of the edge readout (corners are far from
   all SiPMs), and it hits C1 and C2 equally.
3. **The differentiator is absolute margin, not shape.** Although the *ratio* is
   constant, C2's absolute signal at corners is tiny: per-position p5 = 0.4
   photons (vs C1's 2.9), and the minimum is 0. With any realistic PDE/detection
   threshold, the 3 mm SiPM develops **near-dead corners**, while the 6 mm retains
   a few-photoelectron margin there. The coverage-vs-threshold curve (Fig 6)
   shows C2's usable-area fraction collapsing faster as the threshold rises.
4. **Position resolution slightly favours 6 mm.** Centroid reconstruction
   (calibrated) gives RMS ≈ 3.7–3.8 cm (C1) vs 3.9–4.0 cm (C2). More light →
   modestly better reconstruction; both are limited by the edge-only readout.

## 5. Conclusion for SiPM selection

The 3 mm SiPM is **geometrically well-behaved** (no anomalous corner degradation),
but its ¼-light scaling leaves **insufficient absolute margin at corners** — the
weak-link region of any edge-readout slab. Combined with the prior study
(same light as a 2×2 array at half the channel count), the **6 mm single SiPM
(C1) remains the recommended choice**: it preserves corner margin and slightly
better position resolution at the same per-site channel cost. The 3 mm option is
acceptable **only** if the readout is later re-architected to add SiPMs near
corners, or if the physics goal tolerates corner dead-zones.

## 6. Caveats

- No PDE applied; absolute thresholds should be folded in from a measured
  PDE curve (per-photon wavelengths are recorded). The C2/C1 *ratio* and λ
  conclusions are PDE-independent.
- ESR reflectivity assumed 0.95; dead rim treated as reflective.
- Single muon energy/angle (1 GeV vertical). Oblique tracks would smear the
  catchment curves but not change the constant-ratio conclusion.
- Position reconstruction uses a simple light-weighted centroid calibrated on
  the scan; it reflects readout-geometry limits, not a fundamental limit.

## 7. Reproduce

```bash
export SIMU_ENV=$PWD/env/inpac.sh && source "$SIMU_ENV"
# data/muons_corner.json: 11x11 + corner-densified scan, 1410 events
condor_submit <jobs for config_sipmtest_c{1,2}_corner.yaml>
python3 scripts/analyze_sipm_cornercase.py \
    --c1 build/output_corner_c1.root --c2 build/output_corner_c2.root \
    --out artifacts/corner
```

## 8. Artifacts added

- `data/muons_corner.json`, `config/config_sipmtest_c{1,2}_corner.yaml`
- `scripts/analyze_sipm_cornercase.py`
- this report + `docs/experiments/figures/corner_*.png`
