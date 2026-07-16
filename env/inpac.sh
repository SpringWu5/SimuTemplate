#!/bin/bash
# ==============================================================================
# env/inpac.sh -- SJTU INPAC cluster software environment for SimuTemplate.
# ------------------------------------------------------------------------------
# This is a SITE-SPECIFIC environment script. It bundles everything that is
# particular to the INPAC cluster (shared "hailing" conda env providing
# Geant4 10.6.3, ROOT 6, yaml-cpp, spdlog, nlohmann_json, GCC) and exports the
# CMake hints the build needs.
#
# Usage (picked up automatically by the job wrappers and recommended in docs):
#   export SIMU_ENV=/path/to/simu_template/env/inpac.sh
#   # then build / submit jobs as usual
#
# If your team runs on a different cluster, copy env/simu_env.example.sh to
# env/<yoursite>.sh, edit it, and point SIMU_ENV at it instead.
# ==============================================================================
set +u  # hailing.env / conda activation reference unbound vars (e.g. PS1)

if [ -f ~mocen/hailing.env ]; then
    source ~mocen/hailing.env
    export PATH=/lustre/collider/mocen/software/condaenv/hailing/bin:${PATH}
else
    echo "env/inpac.sh: ~mocen/hailing.env not found; falling back to CVMFS LCG view" >&2
    source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
fi

# CMake hints (consumed by jobs/run_*_wrapper.sh and the documented build).
export Geant4_DIR=/lustre/collider/mocen/software/condaenv/hailing/lib/Geant4-10.6.3
export ROOT_DIR=/lustre/collider/mocen/software/condaenv/hailing/cmake
export CMAKE_PREFIX_PATH=/lustre/collider/mocen/software/condaenv/hailing

set -u
