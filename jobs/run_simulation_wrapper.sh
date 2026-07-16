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
#    Provides Geant4, ROOT, Python3, GCC and all G4 data paths, and exports
#    the CMake hints (Geant4_DIR / ROOT_DIR / CMAKE_PREFIX_PATH).
#    Resolution order:
#      a) $SIMU_ENV            -- per-user/site; point at env/<site>.sh
#      b) bundled SJTU INPAC env (env/inpac.sh)
#      c) CVMFS LCG view fallback
#    NOTE: source with nounset temporarily OFF -- site env scripts may
#    reference unbound vars (e.g. PS1) which would abort under `set -u`.
set +u
if [ -n "${SIMU_ENV:-}" ] && [ -f "${SIMU_ENV}" ]; then
    # shellcheck disable=SC1090
    source "${SIMU_ENV}"
elif [ -f "$PROJECT_DIR/env/inpac.sh" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/env/inpac.sh"
else
    echo "WARNING: SIMU_ENV unset and env/inpac.sh missing; using CVMFS LCG view fallback"
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
    # Geant4/ROOT locations come from the sourced env (Geant4_DIR, ROOT_DIR,
    # CMAKE_PREFIX_PATH). Only pass what is set; otherwise let CMake's
    # find_package auto-detect. (No site-specific paths hardcoded here.)
    EXTRA_CMAKE_ARGS=""
    [ -n "${Geant4_DIR:-}" ]        && EXTRA_CMAKE_ARGS="$EXTRA_CMAKE_ARGS -DGeant4_DIR=${Geant4_DIR}"
    [ -n "${ROOT_DIR:-}" ]          && EXTRA_CMAKE_ARGS="$EXTRA_CMAKE_ARGS -DROOT_DIR=${ROOT_DIR}"
    [ -n "${CMAKE_PREFIX_PATH:-}" ] && EXTRA_CMAKE_ARGS="$EXTRA_CMAKE_ARGS -DCMAKE_PREFIX_PATH=${CMAKE_PREFIX_PATH}"
    # shellcheck disable=SC2086
    cmake -S "$PROJECT_DIR" -B "$BUILD_DIR" $EXTRA_CMAKE_ARGS
    cmake --build "$BUILD_DIR" -j"$(nproc)"
fi

# 4. Run the simulation
cd "$BUILD_DIR"
exec ./SimuTemplate "$CONFIG_FILE" "$OUTPUT_FILE" $EXTRA_ARGS
