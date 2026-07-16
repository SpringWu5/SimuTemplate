# SimuTemplate

A reusable Geant4 + ROOT simulation template, extracted from the
MuonSLab / MuonCube codebase. It provides:

1. **A complete simulation skeleton** — main entry point, user actions,
   physics list, materials, and ROOT output — driven by a YAML config.
2. **A detector framework** — an abstract base class + runtime factory so you
   plug in *your own* detector geometry without touching the simulation core.
3. **Detector → 3D-model conversion** — two independent, reusable mechanisms:
   - `GeometryExporter` (generic): walks *any* Geant4 geometry tree and writes a
     flat ROOT table of every volume's position / size / material.
   - VRML export (`scripts/export_vrml*.sh` + `macros/*.mac`): renders the live
     Geant4 geometry into a `.wrl` 3D model openable in Blender / viewers.

Two example detectors (`MuonSLab`, `MuonCube`) ship as **references** so the
template compiles and runs out of the box. Replace them with your own.

---

## 1. Directory layout

```
simu_template/
├── main.cc                  # Entry point: parses args, wires run manager
├── CMakeLists.txt           # Top-level build (project = SimuTemplate)
├── AGENTS.md                # Onboarding doc for AI agents (read first)
├── include/  &  src/        # Reusable framework + example detectors
│   ├── Util/                # Logger (spdlog), Singleton (CRTP)        [framework]
│   ├── PhysicsList/         # EM+optical+hadronic physics              [framework]
│   ├── Action/              # Run/Event/Stepping/PrimaryGenerator      [framework]
│   ├── Record/              # ROOT output: Hits/Muons/SiPM/Voxel/Map   [framework]
│   └── DetectorConstruction/
│       ├── DetectorConstructionBase.{hh,cc}   # abstract base          [framework]
│       ├── DetectorFactory.{hh,cc}            # runtime selection       [framework]
│       ├── MaterialManager.{hh,cc}            # YAML-driven materials   [framework]
│       ├── GeometryExporter.{hh,cc}           # generic 3D-model export [framework]
│       ├── SLabBuilder.{hh,cc}                # ── example detector ──
│       ├── SipmBuilder.{hh,cc}                # ── example (SiPM helper)
│       ├── MuonCubeConstruction.{hh,cc}       # ── example detector ──
│       ├── MuonCubeGeometryExporter.{hh,cc}   # ── example (specialised map)
│       └── SensitiveDetectors/                # ── example SDs ──
├── config/                  # config.yaml + spectra/PDE/optical data + vis macros
├── data/                    # sample particle JSON (muons.json)
├── macros/                  # Geant4 macros incl. VRML/geometry export
├── scripts/                 # export_vrml.sh, export_vrml_simple.sh, inspect_output.py
├── jobs/                    # HTCondor wrappers + .sub templates (+ logs/)
└── docs/                    # CODEBASE_REPORT.md (read first), INPAC_GUIDE.md, CLUSTER_OPERATIONS.md
```

Files marked **[framework]** are reusable as-is. Files under `DetectorConstruction/`
that are *not* the four framework classes are example detectors — keep them as
references or delete once you have your own.

---

## 2. Build & run

> INPAC cluster: source the environment first.
> ```bash
> source ~mocen/hailing.env
> export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:$PATH
> ```

```bash
cd simu_template
cmake -S . -B build \
      -DGeant4_DIR=/lustre/collider/mocen/software/condaenv/hailing/lib/Geant4-10.6.3 \
      -DROOT_DIR=/lustre/collider/mocen/software/condaenv/hailing/cmake \
      -DCMAKE_PREFIX_PATH=/lustre/collider/mocen/software/condaenv/hailing
cmake --build build -j8
```

Run (batch):
```bash
cd build
./SimuTemplate ../config/config.yaml output.root
```
Run (interactive GUI):
```bash
cd build
./SimuTemplate        # opens visualisation with config/vis*.mac
```

Output ROOT file contains:
| Tree            | Contents                                                  |
|-----------------|-----------------------------------------------------------|
| `Simu`          | Per-event hits / muons / SiPM / voxel-truth (your data)   |
| `GeometryModel` | One row per placed volume: name, material, XYZ, size, depth |
| `ConfigFile`    | The YAML config embedded as text                          |

---

## 3. Convert the detector into a 3D model

### 3a. Generic geometry table (recommended for analysis)
Happens **automatically** at end of run via `GeometryExporter` (called from
`RunAction::EndOfRunAction`). No detector-specific code needed — it traverses
the whole volume tree.

```python
import uproot
df = uproot.open("output.root")["GeometryModel"].arrays(library="pd")
# columns: Name, PhysName, CopyNo, Material, X, Y, Z, DX, DY, DZ, Depth
print(df[df.Name == "Scintillator"][["X","Y","Z","DX","DY","DZ"]])
```

### 3b. VRML 3D model (.wrl) for Blender / external viewers
```bash
bash scripts/export_vrml.sh        # produces build/g4_00.wrl
# or run a macro directly in the GUI:
#   /control/execute ../macros/export_vrml_clean.mac
```
Edit the volume names/colours in `macros/export_vrml_*.mac` to match your
detector. The VRML driver works for *any* Geant4 geometry.

---

## 4. Adding your own detector

The factory pattern means the simulation core never changes — you only add a
detector class and register it.

1. **Create the builder** by subclassing `DetectorConstructionBase`
   (`include/DetectorConstruction/DetectorConstructionBase.hh`).
   Implement the two pure-virtual methods:
   ```cpp
   class MyDetector : public DetectorConstructionBase {
   public:
       explicit MyDetector(const char* config_path)
           : DetectorConstructionBase(config_path) {}
   protected:
       G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;
       void BuildSensitiveDetectors() override;
   };
   ```
   - `ConstructDetector`: build solids, logical volumes, place them in `worldLogical`.
   - `BuildSensitiveDetectors`: attach your `G4VSensitiveDetector` to logical volumes.
   The world volume + materials (via `MaterialManager`) are already set up for you.

2. **Register it in the factory** — edit
   `src/DetectorConstruction/DetectorFactory.cc`:
   ```cpp
   #include "DetectorConstruction/MyDetector.hh"
   ...
   else if (typeLower == "mydetector") {
       return new MyDetector(config_path);
   }
   ```

3. **Select it in config** — `config/config.yaml`:
   ```yaml
   Detector:
     type: "MyDetector"
   ```
   Add any detector-specific geometry keys under a new YAML node and read them
   inside your builder via `MaterialManager::Instance()->getRootNode()`.

4. *(Optional)* Add new materials in `MaterialManager::BuildMaterial()`.

5. *(Optional)* For a custom sensor-position map (beyond the generic
   `GeometryExporter`), model it on `MuonCubeGeometryExporter` — e.g. to decode
   a detector-specific copy-number scheme into meaningful channel IDs.

### Particle input
Primaries come from a JSON file (`Particles.particle_file_path` in config).
See `data/muons.json` for the schema (an array of `McEvent` objects; see
`include/Record/McEvent.hh`). Units: cm for position, ns for time, MeV for
momentum.

---

## 5. Dependencies

- Geant4 ≥ 10.6 (UI/vis, optical physics)
- ROOT ≥ 6.24
- yaml-cpp, spdlog, nlohmann_json (all provided by the INPAC conda env)

---

## 6. Note on the example detectors

`MuonCubeConstruction` and `SLabBuilder` demonstrate the full pattern: reading
geometry from config, building complex solids, wiring optical surfaces, and
attaching sensitive detectors. They also pull in materials (SP101 scintillator,
BCF-92 WLS fiber, etc.) built by `MaterialManager`. Treat them as living
documentation; they are not required once your own detector is registered.
