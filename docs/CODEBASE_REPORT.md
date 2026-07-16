# SimuTemplate — Codebase Report

> **Purpose:** a dense, self-contained map of the `simu_template` codebase. An
> AI agent (or new developer) should read **this file** to understand the whole
> project, then only open specific source files when implementing a change.
> Read this *before* `AGENTS.md` / `README.md` when you need depth.
>
> All paths are relative to `simu_template/`. Line numbers are stable references
> into the current tree.

---

## 0. TL;DR

`simu_template` is a **Geant4 + ROOT simulation skeleton** with a pluggable
detector framework. To simulate a *new* detector you normally change **one
class** (a `DetectorConstructionBase` subclass) + register it in the factory +
edit `config.yaml`. The simulation core (actions, physics, output, materials,
3-D export) is reused unchanged.

- **Executable:** `SimuTemplate` (built in `build/`)
- **Entry point:** `main.cc`
- **Input:** a YAML config (`config/config.yaml`) + a particle JSON (`data/*.json`)
- **Output:** one ROOT file containing `Simu` (event data), `GeometryModel`
  (full detector → 3-D map), and `ConfigFile` (embedded YAML).
- **Stack:** C++17, Geant4 10.6, ROOT 6, yaml-cpp, spdlog, nlohmann_json.

---

## 1. Layered architecture

```
                     ┌─────────────────────────────────────────────┐
  main.cc ──────────▶│  Geant4 RunManager (orchestration)           │
                     └─────────────────────────────────────────────┘
                          │            │              │            │
            ┌─────────────┘            │              │            └──────────────┐
            ▼                          ▼              ▼                           ▼
   DetectorConstructionBase    PhysicsList     ActionInitialization        OutputManager
   (abstract; subclass         (EM+optical     ├─ PrimaryGeneratorAction   (ROOT I/O, singleton)
    per detector)              +hadronic)      ├─ RunAction                ▲
   ├─ DetectorFactory                          ├─ EventAction              │ writes via
   ├─ MaterialManager                          └─ SteppingAction           │  GetSiPMHits/
   └─ GeometryExporter (3-D)                                              │  GetVoxelTruth/...
                                                                          │
   ┌────────────────────────────────────────────────────────────────────────┘
   │ SensitiveDetectors (ProcessHits) ──► push hits into OutputManager
   └────────────────────────────────────────────────────────────────
```

Five cooperating layers:

| Layer              | Dir (incl / src)                          | Role |
|--------------------|-------------------------------------------|------|
| **Entry / build**  | `main.cc`, `CMakeLists.txt`, `src/CMakeLists.txt` | CLI, wiring, build |
| **Detector**       | `DetectorConstruction/`                   | Geometry, materials, sensitive detectors, 3-D export |
| **Simulation core**| `Action/`, `PhysicsList/`                 | Run/event/stepping hooks + particle generation + physics |
| **Output**         | `Record/`                                 | ROOT trees & data structures |
| **Utilities**      | `Util/`                                   | Logging (spdlog), Singleton (CRTP) |

---

## 2. Module deep dive

### 2.1 `main.cc` — entry point
- Parses args: `SimuTemplate [config.yaml] [output.root]` (no args ⇒ GUI).
- Loads YAML config (`YAML::LoadFile`) and the particle JSON (`nlohmann::json`).
- Calls `OutputManager::Instance()->Book(output, config)` (creates ROOT file +
  `Simu` tree + embeds config as `ConfigFile`).
- Reads `Detector.type` from config; `DetectorFactory::Create()` builds it.
- Registers detector → `PhysicsList` → `ActionInitialization` on the run manager.
- GUI branch: opens `G4VisExecutive`, runs `config/vis.mac` or `config/vis_cube.mac`.
- Batch branch: `runManager->BeamOn(n_events)` then `OutputManager::Save()`.
- `resolve_config_path()` (main.cc:40) lets the exe run from repo root or `build/`.

### 2.2 `DetectorConstruction/` — the reusable framework + examples

#### `DetectorConstructionBase` (`include/.../DetectorConstructionBase.hh`)
Abstract base implementing `G4VUserDetectorConstruction`. **This is the contract
new detectors implement.**
- `Construct()` is `final` (DetectorConstructionBase.cc:30): builds the world
  box (10 m G4_AIR with RINDEX — critical for optical photons), then calls the
  pure-virtual `ConstructDetector(worldLogical)`.
- `ConstructSDandField()` is `final` (DetectorConstructionBase.cc:51): calls the
  pure-virtual `BuildSensitiveDetectors()`. **SDs MUST be attached here**, *not*
  in `Construct()` — attaching earlier yields zero hits (a recurring Geant4 footgun).
- Constructor inits `MaterialManager::Instance()->BuildEverything(config_path)`.
- Protected helpers/members available to subclasses: `fLogger`, `fConfigPath`,
  `fWorldPhysical`, `fWorldLogical`, `BuildWorldVolume()`.

#### `DetectorFactory` (`DetectorFactory.cc`)
Runtime selection by lowercase string:
- `"muonslab"`/`"slab"` → `SLabBuilder`
- `"muoncube"`/`"cube"` → `MuonCubeConstruction`
- else → throws. **Add your own detector's `else if` here** (DetectorFactory.cc:31).

#### `MaterialManager` (`MaterialManager.hh` / `.cc`)
Singleton (`Singleton<MaterialManager>`), YAML-driven.
- `BuildEverything(yaml)` → `LoadYAML()` (reads `Geometry.SLab.*` and
  `Property.sea_optical_property.path_file`) → `BuildElement()` →
  `BuildOpticalProperties()` → `BuildMaterial()`.
- Builds: `G4_AIR`(+optics), `Vacuum`, `Water`/sea water, glass, epoxy, gel,
  `SiPM`, `plScintillator`, `ESR`, `Tape`, `Battery`, **`SP101`** (plastic
  scintillator, spectrum loaded from `config/SP101.txt`), **`BCF92_Core`** &
  **`BCF92_Clad`** (WLS fiber).
- `GetMaterial(name)` throws if missing. `GetSLabGeometry()` / `GetSipmProperty()`
  expose parsed config.
- **Gotcha:** it reads SLab-specific nodes from YAML; if you strip the SLab
  example, keep those nodes or relax `LoadYAML()`.

#### `GeometryExporter` (`GeometryExporter.hh` / `.cc`) — ★ detector → 3-D model
Generic, detector-agnostic. `Export(world, rootFile, "GeometryModel")` recursively
walks the *entire* physical-volume tree (`Traverse()`, GeometryExporter.cc:42) and
fills **one ROOT row per placed volume**: `Name, PhysName, CopyNo, Material,
X,Y,Z` (global centre, mm), `DX,DY,DZ` (bounding-box extents, mm), `Depth`.
- Writes into the *currently open* ROOT `gDirectory` (owned by `OutputManager`);
  does **not** open/close the file.
- Called automatically from `RunAction::EndOfRunAction()` — any new detector is
  exported with zero extra code.

#### Example detectors (references — safe to delete once you have your own)
- **`SLabBuilder`** (`SLabBuilder.cc:223`): 4-layer scintillator slabs. Attaches
  `SLabSensitiveDetector("Slab")` to the scintillator logical volume.
- **`MuonCubeConstruction`** (`MuonCubeConstruction.cc`): 8×8×4 voxel array with
  WLS fibers + pixelated SiPMs. Attaches **two** SDs:
  - `MuonCubeSiPMSensitiveDetector("MuonCube/SiPM")` → `fLogicSiPMUnit` (cc:565)
  - `SLabSensitiveDetector("MuonCube")` → `fLogicScintillator` (cc:589) — reuses
    the SLab SD as the **generic voxel-truth recorder**.
  - Voxel ID scheme: `layer*1000 + row*100 + col` (`EncodeVoxelID`, hh:137).
- **`SipmBuilder`**: builds an SiPM logical volume + attaches
  `SipmSensitiveDetector("SiPM")` (SipmBuilder.cc:38).
- **`MuonCubeGeometryExporter`**: a *specialised* exporter that decodes the
  MuonCube SiPM copy-number scheme into channel IDs. Kept as an example of a
  custom sensor map (contrast with the generic `GeometryExporter`).

#### `SensitiveDetectors/` — the data producers
| SD class | Attached to (examples) | Fills (into OutputManager) |
|----------|------------------------|----------------------------|
| `SLabSensitiveDetector` | scintillator/voxel volumes (both SLab & MuonCube) | `VoxelTruthHit` (truth) **and** legacy `fSLabHits` |
| `MuonCubeSiPMSensitiveDetector` | `SiPMUnit` | `SiPMHit` (Det_ID, Time, Wavelength); kills photon after hit |
| `SipmSensitiveDetector` | legacy SiPM | legacy `fHits` (`SiPM_Old*`) |

Key: **`SLabSensitiveDetector` is detector-agnostic** — any scintillator volume
whose copy number is a voxel ID gets correct truth recording. Reuse it for new
scintillator-based detectors.

> Pattern for attaching an SD (every builder follows this):
> ```cpp
> auto* sd = new MySD("name");
> G4SDManager::GetSDMpointer()->AddNewDetector(sd);  // register with manager
> logicalVol->SetSensitiveDetector(sd);              // attach to volume
> ```
> Must run inside `BuildSensitiveDetectors()` (i.e. `ConstructSDandField`).

### 2.3 `Action/` — simulation hooks
- **`ActionInitialization::Build()`** (ActionInitialization.cc:15): constructs
  `PrimaryGeneratorAction`, `RunAction`, `EventAction`, `SteppingAction` per
  worker thread. (Re-)inits logging.
- **`PrimaryGeneratorAction`** (PrimaryGeneratorAction.cc:27): pulls the next
  particle from the JSON list (`fNextMuonIndex` cycles), builds `G4PrimaryVertex`
  (units: cm / ns / **MeV**), and fills `OutputManager::GetMuons()`.
- **`RunAction`** (RunAction.cc):
  - `BeginOfRunAction`: enables random-seed storage; resolves the world volume
    via `G4TransportationManager`; logs tracked particle types.
  - `EndOfRunAction`: logs particle/photon stats, then calls
    **`GeometryExporter::Export()`** to write the `GeometryModel` tree.
- **`EventAction`** (EventAction.cc):
  - `BeginOfEventAction`: captures **global primary truth** scalars
    (PDG, energy, vertex XYZ, momentum, time) into OutputManager; resets stats.
  - `EndOfEventAction`: logs summaries; calls `OutputManager::EndOfEvent()`
    (Fill `Simu` tree + reset per-event buffers).
- **`SteppingAction`** (SteppingAction.cc): **statistics/logging only** — counts
  particles & Cerenkov/Scintillation/WLS photons per event, writes photon CSV.
  Does **not** push hits into OutputManager (SDs do that). Large sections of
  per-step debug printing are commented out for production.

### 2.4 `PhysicsList/` (`PhysicsList.cc`)
`G4VModularPhysicsList`. Registers: `G4EmStandardPhysics_option4`,
`G4EmExtraPhysics`, decay (+ radioactive), `G4HadronElasticPhysicsHP`,
`G4HadronPhysicsShielding`, `G4StoppingPhysics`, ion physics, and **optical
physics** (`G4OpticalPhysics` — scintillation, WLS, Cerenkov; secondaries tracked
first). Default production cut 0.7 mm; tighter cuts on γ/e±/p. `MilliQ*Physics`
files are present but commented out.
> To change physics, edit only `PhysicsList.cc` — no other code cares.

### 2.5 `Record/` — ROOT data model & I/O
- **`OutputManager`** (`Singleton<OutputManager>`, `OutputManager.hh`): owns the
  `TFile` + `Simu` `TTree` + all hit collections.
  - `Book(file, config)`: creates file, embeds config, creates `Simu` tree, books
    all branches (OutputManager.cc:46).
  - `EndOfEvent()`: `Fill()` + reset buffers.
  - `Save()`: `Write()` + `Close()`; nulls pointers to avoid double-free.
  - Getters used by SDs/actions: `GetMuons/GetSLabHits/GetHits/GetSiPMHits/
    GetVoxelTruth`; primary-truth setters (`SetPrimaryPDG`, …).
- **Data structures** (each `BookBranches(tree[, prefix])` + `Reset()` + `Add…`):
  - `Muons` → branches `muon_*`, `weight_spectrum`.
  - `Hits` (generic; reused with prefixes `SLab` and `SiPM_Old`) → `*Hit_*`.
  - `SiPMHit` (slim) → prefix `SiPM`: `SiPMHit_Det_ID`, `SiPMHit_Time`,
    `SiPMHit_Wavelength`.
  - `VoxelTruthHit` → prefix `Voxel`: ID, Edep, TrackLen, Entry_*, Exit_*.
  - `GeometryMap` → used by the specialised MuonCube exporter (FiberID/Plane/Row…).
  - `McEvent` / `McParticle`: JSON particle schema (units cm/ns/**MeV**).

### 2.6 `Util/`
- `Logger.hh`: spdlog setup (console + timestamped file under `build/log/`),
  photon-statistics CSV, plus `create_logger()` returning the default logger.
- `Singleton.hh`: CRTP Meyers singleton (`Instance()` returns `shared_ptr`).

---

## 3. End-to-end run lifecycle (read this to debug)

```
main()
 ├─ OutputManager::Book()                 # ROOT file + Simu tree created HERE
 ├─ runManager->SetUserInitialization(detector, physics, actions)
 ├─ runManager->Initialize()
 │    ├─ DetectorConstructionBase::Construct()        # world + ConstructDetector()
 │    └─ DetectorConstructionBase::ConstructSDandField()  # BuildSensitiveDetectors()
 ├─ runManager->BeamOn(n)
 │    ├─ ActionInitialization::Build()                # per-worker actions
 │    ├─ RunAction::BeginOfRunAction()                # resolve world volume
 │    └─ for each event:
 │         ├─ PrimaryGeneratorAction::GeneratePrimaries()  # fill Muons
 │         ├─ EventAction::BeginOfEventAction()       # fill Primary_* scalars
 │         ├─ stepping → SD::ProcessHits()            # fill SiPM/Voxel/legacy hits
 │         │            SteppingAction::UserSteppingAction()  # stats only
 │         └─ EventAction::EndOfEventAction()         # OutputManager::EndOfEvent()
 │    └─ RunAction::EndOfRunAction()      # ★ GeometryExporter writes GeometryModel
 └─ OutputManager::Save()                  # Write() + Close()  (file sealed)
```
**Critical ordering:** the geometry export happens *inside* `BeamOn`
(`EndOfRunAction`), so the file is still open — `GeometryExporter` relies on the
active `gDirectory`. `Save()` closes it afterwards. Never open/close the file in
an exporter or SD.

---

## 4. Output ROOT format

| Tree | When written | One row = | Key branches |
|------|--------------|-----------|--------------|
| `Simu` | per event (`EndOfEvent`) | one event | `eventID`; `Primary_{PDG,Energy,X,Y,Z,Px,Py,Pz,Time}`; `muon_{energy,px,py,pz}`, `weight_spectrum`; `Voxel{ID,Edep,TrackLen,Entry_*,Exit_*}`; `SiPMHit_{Det_ID,Time,Wavelength}`; legacy `SLabHit_*`, `SiPM_OldHit_*` |
| `GeometryModel` | once, end of run | one placed volume | `Name, PhysName, CopyNo, Material, X,Y,Z, DX,DY,DZ, Depth` |
| `ConfigFile` | at `Book` | the YAML text | (single `TNamed`) |

Quick inspection: `python3 scripts/inspect_output.py build/output.root`.

---

## 5. Adding a new detector (the main task)

1. **Subclass** `DetectorConstructionBase`; implement
   `ConstructDetector(worldLogical)` (place geometry) and
   `BuildSensitiveDetectors()` (attach SDs).
2. **Register** in `DetectorFactory::Create()` (`DetectorFactory.cc`).
3. **Select** via `config/config.yaml` → `Detector.type: "YourDetector"`.
4. **Materials**: add in `MaterialManager::BuildMaterial()` if needed; read
   detector params from a new YAML node via `MaterialManager::getRootNode()`.
5. **Truth/hits**: reuse `SLabSensitiveDetector` for scintillator truth, or write
   a new SD that pushes into `OutputManager::GetSiPMHits()/GetVoxelTruth()`.
6. The `GeometryModel` 3-D export is automatic. For a custom sensor-ID map,
   model it on `MuonCubeGeometryExporter`.
(See `README.md` §4 for a skeleton and `MuonCubeConstruction` as a full example.)

---

## 6. 3-D model conversion (two mechanisms)
- **Generic table** — `GeometryExporter` (auto). Best for analysis; load with
  `uproot`/pandas. Any detector, no code.
- **VRML `.wrl`** — `scripts/export_vrml.sh` (+ `macros/export_vrml_*.mac`).
  Renders the live geometry for Blender/viewers. Edit volume names/colours in
  the macros to match your detector.

---

## 7. Configuration

`config/config.yaml` (see file for full schema):
- `Run.number_of_events` (`-1` ⇒ all particles in JSON).
- `Particles.particle_file_path` → JSON array of `McEvent`
  (schema in `include/Record/McEvent.hh`; units cm/ns/**MeV**).
- `Detector.type` → factory key.
- `Geometry.SLab.*` → consumed by `MaterialManager::LoadYAML` (keep even if you
  don't use the SLab example, or relax the loader).
- `MuonCube.*` → consumed by `MuonCubeConstruction`.
- `Property.*` → optical-property files (spectra, PDE, sea-water YAML).
Data files referenced (`SP101.txt`, `SiPM_PDE.txt`, `WLS_*.txt`,
`EJ200ScintSpectrum.txt`, `optical_properties.yaml`) live in `config/`.

---

## 8. Build / run / submit (summary — full detail in `docs/CLUSTER_OPERATIONS.md`)

```bash
export SIMU_ENV=$PWD/env/inpac.sh   # or env/<yoursite>.sh; exports CMake hints
source "$SIMU_ENV"
cmake -S . -B build                 # Geant4_DIR/ROOT_DIR come from the env
cmake --build build -j8
./build/SimuTemplate config/config.yaml output.root      # batch
condor_submit jobs/simulation.sub                          # production (HTCondor)
```

---

## 9. Conventions & gotchas
- C++17, Google style, **no `using namespace` in headers**.
- SDs attach in `ConstructSDandField()` only (attaching in `Construct()` ⇒ 0 hits).
- `GeometryExporter`/exporters are guests in `OutputManager`'s file — never
  open/close it.
- World is `G4_AIR` with RINDEX (vacuum kills optical photons at boundaries).
- JSON momentum units are **MeV** (a past bug source); positions cm, time ns.
- `/lustre` is not backed up → use git.
- `SteppingAction` is stats-only; if "hits are missing", the SD (not stepping) is
  where to look.
- `jobs/*.sh` source the env with `set +u`/`set -u` (conda references unbound `PS1`).

---

## 10. File index (quick lookup)

| You need to… | Open |
|--------------|------|
| Understand run wiring / CLI | `main.cc` |
| Add/change a detector | `include/DetectorConstruction/DetectorConstructionBase.hh` + `DetectorFactory.cc` |
| Add materials / read config | `DetectorConstruction/MaterialManager.{hh,cc}` |
| Change physics | `PhysicsList/PhysicsList.cc` |
| Change what's recorded per event | `Record/OutputManager.{hh,cc}` + the relevant `Record/*.hh` + SD |
| Add a sensitive detector | `DetectorConstruction/SensitiveDetectors/*` (mirror `SLabSensitiveDetector`) |
| Inspect/visualise output | `scripts/inspect_output.py`, `scripts/export_vrml.sh`, `macros/*.mac` |
| Run on the cluster | `docs/CLUSTER_OPERATIONS.md`, `jobs/` |
| Cluster policy | `docs/INPAC_GUIDE.md` |
| Agent onboarding (short) | `AGENTS.md` |
