#!/bin/bash
# ==============================================================================
# run_analysis_wrapper.sh
# ------------------------------------------------------------------------------
# HTCondor worker-node wrapper for running a Python analysis script on the
# simulation output. Reuses the same environment as the simulation wrapper.
#
# Usage:
#   bash jobs/run_analysis_wrapper.sh <script.py> <input.root> [extra_args...]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Source the software environment (same resolution order as the simulation
# wrapper): $SIMU_ENV -> bundled env/inpac.sh -> CVMFS LCG view fallback.
# Source with nounset temporarily OFF (site env scripts may reference unbound
# vars like PS1 that abort under `set -u`).
set +u
if [ -n "${SIMU_ENV:-}" ] && [ -f "${SIMU_ENV}" ]; then
    # shellcheck disable=SC1090
    source "${SIMU_ENV}"
elif [ -f "$PROJECT_DIR/env/inpac.sh" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/env/inpac.sh"
else
    source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
fi
set -u

ANALYSIS_SCRIPT="${1:?missing analysis script}"
INPUT_FILE="${2:?missing input file}"
shift 2 || true
EXTRA_ARGS="$*"

echo "=== SimuTemplate analysis job starting on $(hostname) ==="
date
echo "Script : $ANALYSIS_SCRIPT"
echo "Input  : $INPUT_FILE"
echo "Extra  : $EXTRA_ARGS"

cd "$PROJECT_DIR"
exec python3 "$ANALYSIS_SCRIPT" "$INPUT_FILE" $EXTRA_ARGS
