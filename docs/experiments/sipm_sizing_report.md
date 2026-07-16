# Experiment Report — Single-Slab SiPM Sizing Study

**Branch:** `spring-sipm-test`
**Date:** 2026-07-16
**Status:** complete

## 1. Objective

Quantify how the choice of readout SiPM affects light collection on a single
scintillator slab, in order to guide the SiPM selection for the real detector.
Three "unit SiPM" forms are compared when placed at the same eight readout
sites around one slab.

## 2. Configurations (the three "unit SiPMs")

| ID | Unit SiPM | Active area / site | Total active area | Channels |
|----|-----------|--------------------|-------------------|----------|
| **C1** | single 7×7 mm (active 6×6 mm) | 36 mm² | 36 mm² | 8 |
| **C2** | single 4×4 mm (active 3×3 mm) | 9 mm²  | 9 mm²  | 8 |
| **C3** | 2×2 array of 4×4 mm (active 3×3 mm, 1 mm gap, 9×9 mm footprint) | 4×9 = 36 mm² | 36 mm² | 32 |

C1 and C3 share the **same total active area (36 mm²)** — they isolate
*concentrated vs distributed* active area. C2 (¼ the area) is the area-scaling
baseline.

## 3. Setup

- **Slab:** single EJ-200 scintillator, 20 × 20 × 2 cm (material `Scint`,
  yield 10 000 ph/MeV, n = 1.58, Birks 0.126 mm/MeV).
- **Readout:** 8 unit-SiPM sites around the perimeter — 2 per edge at
  y = ±5 cm (±X edges) / x = ±5 cm (±Y edges). Slab surface polished
  dielectric; all non-window area wrapped in a reflective ESR shell
  (R = 0.95); only the active-area windows let light out.
- **Particle source:** 1 GeV vertical μ⁻ scanned over a 5 × 5 (x,y) grid
  (±8/±4/0 cm), 10 muons per point → **250 events / config**.
- **Recording (no PDE applied — pure geometric collection):** per photon
  hitting an active area → `(channel, arrival time, wavelength)`; per event →
  muon position (`Primary_X/Y`) and slab Edep (`VoxelEdep`). Channel ID encodes
  `edge·1000 + pos·100 + cell`.

Runs were submitted to HTCondor (3 jobs, ExitCode 0).

## 4. Results

| Metric | C1 (6 mm) | C2 (3 mm) | C3 (2×2 array) |
|---|---|---|---|
| Events | 250 | 250 | 250 |
| Mean collected photons / event | **119.3** | 30.3 | **121.0** |
| Collected photons / MeV | **31.2** | 7.8 | **31.1** |
| Collection efficiency (active / produced) | 0.31 % | 0.08 % | 0.31 % |
| Site-response CV (8 SiPMs, lower = more uniform) | 0.038 | 0.026 | 0.043 |
| Per-edge mean [+X,−X,+Y,−Y] | 14.8/14.8/14.8/15.4 | 3.8/3.9/3.7/3.8 | 15.1/15.6/14.3/15.4 |

### Figures
- `figures/01_light_yield.png` — mean collected photons/event per config
- `figures/02_efficiency.png` — geometric collection efficiency
- `figures/03_per_site.png` — per-SiPM response (8 sites) — symmetry
- `figures/04_uniformity.png` — collected photons vs muon (x,y) heatmaps
- `figures/05_attenuation.png` — response vs distance to nearest SiPM
- `figures/06_wavelength.png` — photon wavelength spectrum at SiPM
- `figures/07_time.png` — photon arrival-time spectrum at SiPM
- `figures/08_array_split.png` — C3 intra-array (4 sub-cell) light share

## 5. Findings

1. **Light collection scales with active area.** C2 (9 mm²) collects
   30.3 ph/event ≈ exactly ¼ of C1 (119.3), matching the 4× area ratio.
2. **Equal area ⇒ equal light.** C1 and C3 (both 36 mm²) are statistically
   identical (119 vs 121 ph/event, 31.2 vs 31.1 ph/MeV). Distributing the
   active area into a 2×2 array does **not** gain light over a single 6 mm SiPM.
3. **The 8-site readout is highly symmetric.** Per-edge means are balanced to
   within a few percent and the site-response CV is 2.6–4.3 % for all configs.
   C3 is marginally less uniform (CV 0.043) due to the 1 mm inactive gaps.
4. **Absolute collection is low (~0.3 %).** With small windows on a large
   hermetic slab, light is trapped and mostly absorbed before reaching a window;
   the relevant figure of merit for signal size is **photons/MeV ≈ 31 (C1/C3)
   vs 7.8 (C2)**.

## 6. SiPM selection recommendation

- **C1 (single 6×6 mm) is the recommended choice.** It delivers the same light
  as the 2×2 array (C3) while using **8 channels instead of 32** — simpler,
  cheaper readout and cabling for identical signal.
- **C2 (single 3×3 mm) is too small** — ¼ the signal (≈ 8 ph/MeV) likely
  insufficient for clean MIP detection.
- **C3 (2×2 array) only if** sub-site position resolution or channel redundancy
  is required; it costs 4× the readout channels for no light gain and slightly
  worse uniformity.

## 7. Caveats / limitations

- **No PDE applied.** Numbers are geometric (ideal 100 %). Real
  photoelectrons = collected × ⟨PDE(λ)⟩; since C1≈C3 with similar spectra, PDE
  will not change the ranking. Folding in a measured PDE is the natural next
  step (the recorded per-photon wavelength enables this offline).
- **Dead rim treated as reflective ESR** (slightly optimistic for C1/C2); a
  purely absorbing rim would lower their yield a few %.
- **Single muon species/energy/angle** (1 GeV vertical). A realistic cosmic
  spectrum and oblique tracks can be run with the same geometry.
- **ESR reflectivity assumed 0.95.**
- Statistical precision: ~4 % per site (250 events); means are stable.

## 8. Reproduce

```bash
export SIMU_ENV=$PWD/env/inpac.sh && source "$SIMU_ENV"
cmake --build build -j8          # builds SingleSlabSiPMTest (detector "sipmtest")
# data/muons_sipmtest.json is the 5x5x10 scan sample
condor_submit <jobs for config_sipmtest_c{1,2,3}.yaml>   # or run on a login node
python3 scripts/analyze_sipmtest.py \
    --c1 build/output_sipmtest_c1.root \
    --c2 build/output_sipmtest_c2.root \
    --c3 build/output_sipmtest_c3.root --out artifacts/sipmtest
```

## 9. Artifacts added on this branch

- `src/DetectorConstruction/SingleSlabSiPMTest.cc/.hh` + registered in
  `DetectorFactory` (detector key `sipmtest`)
- `src/.../SensitiveDetectors/SingleSlabSiPMSensitiveDetector.cc/.hh`
- `config/config_sipmtest_c{1,2,3}.yaml`, `data/muons_sipmtest.json`
- `scripts/analyze_sipmtest.py`
- This report + `docs/experiments/figures/*.png`
