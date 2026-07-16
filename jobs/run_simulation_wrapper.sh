#!/bin/bash
# ==============================================================================
# run_simulation_wrapper.sh
# ------------------------------------------------------------------------------
# HTCondor worker-node wrapper for SimuTemplate.
#
# Sets up the INPAC software environment, then runs the Geant4 simulation.
# Paths are resolved relative to THIS script so the job is portable: it works
# from the login node and from any worker node that shares the /lustre FS.
#
# Usage (manual test):
#   bash jobs/run_simulation_wrapper.sh <config.yaml> <output.root> [extra_args...]
#
# HTCondor .sub passes these as Arguments.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
BUILD_DIR="$PROJECT_DIR/build"
EXEC="$BUILD_DIR/SimuTemplate"

echo "=== SimuTemplate job starting on $(hostname) ==="
date

# 1. Source the software environment (CRITICAL - do this first).
#    Provides Geant4, ROOT, Python3, GCC and all G4 data paths.
#    NOTE: source with nounset temporarily OFF — conda activation references
#    unbound vars (e.g. PS1) which would abort under `set -u`.
set +u
if [ -f ~mocen/hailing.env ]; then
    # shellcheck disable=SC1090
    source ~mocen/hailing.env
    # The conda env provides geant4-config / root-config on PATH:
    export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:${PATH}
else
    echo "WARNING: ~mocen/hailing.env not found, falling back to CVMFS LCG view"
    source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
fi
set -u

# 2. Parse arguments
CONFIG_FILE="${1:?missing config.yaml}"
OUTPUT_FILE="${2:?missing output.root}"
shift 2 || true
EXTRA_ARGS="$*"

echo "Project : $PROJECT_DIR"
echo "Config  : $CONFIG_FILE"
echo "Output  : $OUTPUT_FILE"
echo "Extra   : $EXTRA_ARGS"

# 3. Build the executable if it is missing (defensive; usually pre-built).
if [ ! -x "$EXEC" ]; then
    echo "Executable not found, building..."
    mkdir -p "$BUILD_DIR"
    cmake -S "$PROJECT_DIR" -B "$BUILD_DIR" \
          -DGeant4_DIR=/lustre/collider/mocen/software/condaenv/hailing/lib/Geant4-10.6.3 \
          -DROOT_DIR=/lustre/collider/mocen/software/condaenv/hailing/cmake \
          -DCMAKE_PREFIX_PATH=/lustre/collider/mocen/software/condaenv/hailing
    cmake --build "$BUILD_DIR" -j"$(nproc)"
fi

# 4. Run the simulation
cd "$BUILD_DIR"
exec ./SimuTemplate "$CONFIG_FILE" "$OUTPUT_FILE" $EXTRA_ARGS
