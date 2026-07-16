# Cluster Operations Guide (SimuTemplate)

Operational protocols for building, running, and submitting SimuTemplate jobs
on the INPAC (SJTU) cluster. **Read before any compilation, simulation, or
analysis.**

> Companion: `docs/INPAC_GUIDE.md` (cluster connection & filesystem policy).

---

## 1. Environment setup (MANDATORY)

Before **any** compile / simulation / analysis, activate a software environment
that provides Geant4 (>=10.6), ROOT (>=6), Python 3 (with
numpy/matplotlib/uproot/awkward/scipy), GCC, yaml-cpp, spdlog, nlohmann_json,
and all Geant4 data paths.

The build/run system is driven by a single env-var hook, `SIMU_ENV`, which
points at a site env script under `env/`. That script activates the software
**and** exports the CMake hints (`Geant4_DIR`, `ROOT_DIR`, `CMAKE_PREFIX_PATH`),
so no cluster-specific path ever appears in build commands or job wrappers.

```bash
export SIMU_ENV=$PWD/env/inpac.sh         # SJTU INPAC (bundled)
# export SIMU_ENV=$PWD/env/<yoursite>.sh  # other clusters (copy simu_env.example.sh)
source "$SIMU_ENV"
```

The job wrappers (`jobs/run_*_wrapper.sh`) source the env automatically, in this
order: `$SIMU_ENV` → bundled `env/inpac.sh` → CVMFS LCG view fallback. The
HTCondor `.sub` files set `getenv = True`, so `SIMU_ENV` propagates to worker
nodes — set it once in your submit shell.

CVMFS-only fallback (no `SIMU_ENV`, no `env/inpac.sh`):
```bash
source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
```

---

## 2. Build

```bash
cd /lustre/YOUR_GROUP/YOUR_USERNAME/simu_template
export SIMU_ENV=$PWD/env/inpac.sh   # or env/<yoursite>.sh
source "$SIMU_ENV"                  # exports Geant4_DIR/ROOT_DIR/CMAKE_PREFIX_PATH

cmake -S . -B build                 # hints come from the env, no site paths
cmake --build build -j8
```

Executable: `build/SimuTemplate`

---

## 3. Execution mode — decision tree

| Task                            | Events / size      | Mode              |
|---------------------------------|--------------------|-------------------|
| Compile check                   | —                  | Login node        |
| Quick simulation                | < 1,000 events     | Login node        |
| Quick analysis / single file    | small ROOT file    | Login node        |
| **Production simulation**       | > 1,000 events     | **HTCondor job**  |
| Large-scale analysis            | many files         | **HTCondor job**  |
| Long-running (> 30 min)         | any                | **HTCondor job**  |
| High memory (> 8 GB)            | any                | **HTCondor job**  |

**Move to a job if:** OOM kill, runtime > 30 min, sluggish node, or other users
complain.

### 3.1 Login node

```bash
cd build
./SimuTemplate ../config/config.yaml output.root        # batch
./SimuTemplate                                            # GUI (vis.mac)
```

### 3.2 HTCondor job

Ready-made templates live in `jobs/`:

```
jobs/
├── run_simulation_wrapper.sh   # env + build(if missing) + run SimuTemplate
├── run_analysis_wrapper.sh     # env + run a python analysis script
├── simulation.sub              # condor submit file (sim)
├── analysis.sub                # condor submit file (analysis)
└── logs/                       # job stdout/stderr (auto-created)
```

Submit:
```bash
condor_submit jobs/simulation.sub
# Submitting job(s).
# 1 job(s) submitted to cluster <ID>.
```

Edit `jobs/simulation.sub` to change the config / output / resource requests.
All paths are resolved from `PROJECT_ROOT` (one line to change if the project
moves). The wrappers source the environment themselves, so jobs are self-contained.

---

## 4. Job management cheat-sheet

```bash
condor_submit <file.sub>          # submit
condor_q                          # list your jobs
condor_q <cluster_id>             # specific job
condor_q -hold                    # show held jobs + reasons
condor_history <cluster_id>       # completed jobs

condor_rm   <cluster_id>          # kill
condor_hold <cluster_id>          # pause
condor_release <cluster_id>       # resume held job

# Logs (after/at run):
tail -f jobs/logs/<id>.err        # error stream
tail -f jobs/logs/<id>.out        # stdout
tail -f jobs/logs/<id>.log        # condor log
```

Status codes: `R`=running, `I`=idle, `H`=held, `C`=completed.

---

## 5. Common pitfalls

| Symptom                          | Cause                          | Fix                                          |
|----------------------------------|--------------------------------|----------------------------------------------|
| `SimuTemplate: command not found`| not in build dir / not built   | wrapper `cd build`; or build first           |
| `ImportError: uproot`            | env not sourced                | `source "$SIMU_ENV"` at top of script            |
| `G4ENSDFSTATEDATA not set`       | env incomplete                 | use a complete env script (env/inpac.sh or your site) |
| Job stuck in `I` (idle)          | cluster busy / request too big | reduce `request_cpus` or wait                |
| Job goes `H` (held)              | execution error                | read `jobs/logs/<id>.err`                    |
| No output file                   | bad path / permissions         | use absolute paths; check write perms        |
| Output file not found by condor  | relative path in `.sub`        | all `.sub` paths MUST be absolute            |
| Wrapper aborts on `PS1: unbound variable` | `set -u` + conda activation | source env with `set +u` … `set -u` (already handled in `jobs/*.sh`) |

---

## 6. Full workflow example (5000-event production + analysis)

```bash
# One-time setup
export SIMU_ENV=$PWD/env/inpac.sh   # or env/<yoursite>.sh
source "$SIMU_ENV"
cd /lustre/YOUR_GROUP/YOUR_USERNAME/simu_template

# Fresh build
cmake --build build -j8

# Set event count + detector in config/config.yaml, then submit
condor_submit jobs/simulation.sub

# Wait / monitor
watch -n 30 condor_q

# When done, inspect on the login node (fast) ...
python3 scripts/inspect_output.py build/output.root \
    --plot-output artifacts/overview.png

# ... or submit a heavier analysis as its own job
condor_submit jobs/analysis.sub
```
