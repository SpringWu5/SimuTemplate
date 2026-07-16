# Cluster Operations Guide (SimuTemplate)

Operational protocols for building, running, and submitting SimuTemplate jobs
on the INPAC (SJTU) cluster. **Read before any compilation, simulation, or
analysis.**

> Companion: `docs/INPAC_GUIDE.md` (cluster connection & filesystem policy).

---

## 1. Environment setup (MANDATORY)

Before **any** compile / simulation / analysis, source the environment. It
provides Geant4, ROOT, Python 3 (numpy/matplotlib/uproot/awkward/scipy), GCC,
and all Geant4 data paths.

```bash
source ~mocen/hailing.env
export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:$PATH
```

Fallback (if `hailing.env` is unavailable):
```bash
source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
```

Key locations in the conda env (`/lustre/collider/mocen/software/condaenv/hailing`):
- `bin/geant4-config`, `bin/root-config`
- `lib/Geant4-10.6.3`  → pass as `-DGeant4_DIR`
- `cmake`               → pass as `-DROOT_DIR`

---

## 2. Build

```bash
cd /lustre/YOUR_GROUP/YOUR_USERNAME/simu_template
source ~mocen/hailing.env
export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:$PATH

cmake -S . -B build \
      -DGeant4_DIR=/lustre/collider/mocen/software/condaenv/hailing/lib/Geant4-10.6.3 \
      -DROOT_DIR=/lustre/collider/mocen/software/condaenv/hailing/cmake \
      -DCMAKE_PREFIX_PATH=/lustre/collider/mocen/software/condaenv/hailing
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
| `ImportError: uproot`            | env not sourced                | `source ~mocen/hailing.env` at top of script |
| `G4ENSDFSTATEDATA not set`       | env incomplete                 | use `hailing.env`                            |
| Job stuck in `I` (idle)          | cluster busy / request too big | reduce `request_cpus` or wait                |
| Job goes `H` (held)              | execution error                | read `jobs/logs/<id>.err`                    |
| No output file                   | bad path / permissions         | use absolute paths; check write perms        |
| Output file not found by condor  | relative path in `.sub`        | all `.sub` paths MUST be absolute            |
| Wrapper aborts on `PS1: unbound variable` | `set -u` + conda activation | source env with `set +u` … `set -u` (already handled in `jobs/*.sh`) |

---

## 6. Full workflow example (5000-event production + analysis)

```bash
# One-time setup
source ~mocen/hailing.env
export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:$PATH
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
