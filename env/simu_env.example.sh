#!/bin/bash
# ==============================================================================
# env/simu_env.example.sh -- TEMPLATE site environment for SimuTemplate.
# ------------------------------------------------------------------------------
# SimuTemplate needs a C++17 compiler plus, visible to CMake:
#   * Geant4  >= 10.6   (provides Geant4Config.cmake)
#   * ROOT    >= 6      (provides ROOTConfig.cmake)
#   * yaml-cpp, spdlog, nlohmann_json
#
# HOW TO USE (non-INPAC clusters):
#   1. Copy this file:  cp env/simu_env.example.sh env/<yoursite>.sh
#   2. Edit it to source your site's Geant4+ROOT setup (modules, lmod, spack,
#      cvmfs, conda, ...) and export the three CMake hint variables below.
#   3. Activate it once per shell / job:
#        export SIMU_ENV=$PWD/env/<yoursite>.sh
#      The job wrappers (jobs/run_*_wrapper.sh) source $SIMU_ENV automatically;
#      HTCondor .sub files use `getenv = True`, so it propagates to workers.
#
# Leave Geant4_DIR / ROOT_DIR / CMAKE_PREFIX_PATH UNSET only if CMake's
# find_package can already locate Geant4 and ROOT on your system (e.g. they
# are on a standard prefix); otherwise point them at the dirs containing the
# respective *Config.cmake files.
# ==============================================================================
set +u  # many site env scripts reference unbound vars during activation

# --- TODO: source YOUR site's Geant4+ROOT environment -----------------------
# Example (LCG view on CVMFS):
#   source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh
# Example (environment modules):
#   module load geant4/10.6.3 root/6.xx gcc/9.x
# ----------------------------------------------------------------------------

# --- CMake hints (edit to match your install) -------------------------------
# export Geant4_DIR=/path/to/lib/Geant4-10.6.3      # contains Geant4Config.cmake
# export ROOT_DIR=/path/to/root/cmake               # contains ROOTConfig.cmake
# export CMAKE_PREFIX_PATH=/path/to/prefix          # for yaml-cpp/spdlog/json

set -u
