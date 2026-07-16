# AGENTS.md — Guide for AI agents working on SimuTemplate

You are an autonomous engineer operating on a **reusable Geant4 + ROOT
simulation template**. This file orients you. Read it first.

## What this is
A simulation skeleton + a detector framework + a "detector → 3D model"
converter, extracted from the MuonSLab/MuonCube codebase so new detectors can
be added without rewriting the simulation core. Two example detectors
(`MuonSLab`, `MuonCube`) ship as references.

**For architectural depth**, read **`docs/CODEBASE_REPORT.md`** — it is a dense
map of every module, the run lifecycle, the data flow (who fills which ROOT
branch), and a file lookup index. Read it instead of opening source files one by
one; it tells you exactly which file to open for any given task.

**Before running anything**, read `docs/CLUSTER_OPERATIONS.md` and
`docs/INPAC_GUIDE.md` for the mandatory environment + cluster protocols.

## Mental model of the code
- **Simulation core (do not need to touch to add a detector):**
  `main.cc` → `Action/` (run/event/stepping/generator) → `PhysicsList/` →
  `Record/` (ROOT output via `OutputManager`) → `Util/` (logging, singleton).
- **Detector framework (extend here):**
  `DetectorConstruction/DetectorConstructionBase` (abstract) +
  `DetectorFactory` (runtime selection by `config.yaml:Detector.type`) +
  `MaterialManager` (YAML-driven materials).
- **3D-model conversion (reusable, detector-agnostic):**
  `DetectorConstruction/GeometryExporter` walks *any* geometry tree and writes
  a `GeometryModel` ROOT table (auto-called from `RunAction`). VRML export via
  `scripts/export_vrml*.sh` + `macros/*.mac`.

## Build & run (login node)
```bash
source ~mocen/hailing.env
export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:$PATH
cd /lustre/YOUR_GROUP/YOUR_USERNAME/simu_template
cmake -S . -B build -DGeant4_DIR=/lustre/collider/mocen/software/condaenv/hailing/lib/Geant4-10.6.3 \
      -DROOT_DIR=/lustre/collider/mocen/software/condaenv/hailing/cmake \
      -DCMAKE_PREFIX_PATH=/lustre/collider/mocen/software/condaenv/hailing
cmake --build build -j8
cd build && ./SimuTemplate ../config/config.yaml output.root
```
Inspect output: `python3 scripts/inspect_output.py output.root`

## Production runs
Use HTCondor (see `docs/CLUSTER_OPERATIONS.md` §3.2): `condor_submit jobs/simulation.sub`.
Templates in `jobs/` are self-contained (they source the env and build if needed).

## How to add a detector (most common task)
1. Subclass `DetectorConstructionBase`; implement `ConstructDetector()` (build
   geometry inside the provided world) and `BuildSensitiveDetectors()`.
2. Register it in `src/DetectorConstruction/DetectorFactory.cc`.
3. Set `Detector.type` in `config/config.yaml`.
4. Add materials in `MaterialManager::BuildMaterial()` if needed.
See `README.md` §4 for a code skeleton. Mirror `MuonCubeConstruction` /
`SLabBuilder` as working examples.

## Conventions / gotchas
- C++17, Google style, **no `using namespace` in headers**.
- Sensitive detectors are registered in `ConstructSDandField()` (after
  `Construct()`); do not attach them inside `Construct()`.
- `GeometryExporter` writes into the ROOT file owned by `OutputManager`; do not
  open/close the file in the exporter.
- Primaries come from a JSON file (`config.yaml:Particles.particle_file_path`);
  schema in `include/Record/McEvent.hh` (units: cm / ns / MeV).
- `/lustre` is **not backed up** — use git.
- Keep the template compiling; run a quick build + smoke test after edits.
