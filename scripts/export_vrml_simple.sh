#!/bin/bash
# ==============================================================================
# Simple VRML Export - Uses batch mode with inlined commands
# ==============================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/build"

echo "======================================================================"
echo "MuonCube VRML Export (Simple Batch Mode)"
echo "======================================================================"

if [ ! -d "$BUILD_DIR" ]; then
    echo "ERROR: Build directory not found"
    exit 1
fi

cd "$BUILD_DIR"

echo "Running in batch mode (no GUI window)..."
echo "Output: $BUILD_DIR/g4_00.wrl"
echo ""

# Create a temporary macro file
cat > /tmp/vrml_export.mac << 'EOFMACRO'
# VRML Export Macro
/vis/open VRML2FILE
/run/initialize
/vis/drawVolume

# Apply colors
/vis/geometry/set/visibility World 0
/vis/geometry/set/visibility VoxelWrapper 1
/vis/geometry/set/colour VoxelWrapper 0.9 0.9 0.9 0.05
/vis/geometry/set/forceSolid VoxelWrapper 1
/vis/geometry/set/visibility Voxel 1
/vis/geometry/set/colour Voxel 0.3 0.5 1.0 0.25
/vis/geometry/set/forceSolid Voxel 1
/vis/geometry/set/visibility Scintillator 1
/vis/geometry/set/colour Scintillator 0.4 0.6 1.0 0.3
/vis/geometry/set/forceSolid Scintillator 1
/vis/geometry/set/visibility FiberCore_Z 1
/vis/geometry/set/colour FiberCore_Z 0.2 0.8 0.2 0.8
/vis/geometry/set/forceSolid FiberCore_Z 1
/vis/geometry/set/visibility FiberClad_Z 1
/vis/geometry/set/colour FiberClad_Z 0.6 0.9 0.6 0.3
/vis/geometry/set/forceSolid FiberClad_Z 1
/vis/geometry/set/visibility FiberCore_X 1
/vis/geometry/set/colour FiberCore_X 0.9 0.2 0.2 0.8
/vis/geometry/set/forceSolid FiberCore_X 1
/vis/geometry/set/visibility FiberClad_X 1
/vis/geometry/set/colour FiberClad_X 0.95 0.6 0.6 0.3
/vis/geometry/set/forceSolid FiberClad_X 1
/vis/geometry/set/visibility FiberCore_Y 1
/vis/geometry/set/colour FiberCore_Y 0.8 0.2 0.8 0.8
/vis/geometry/set/forceSolid FiberCore_Y 1
/vis/geometry/set/visibility FiberClad_Y 1
/vis/geometry/set/colour FiberClad_Y 0.9 0.6 0.9 0.3
/vis/geometry/set/forceSolid FiberClad_Y 1
/vis/geometry/set/visibility SiPMUnit 1
/vis/geometry/set/colour SiPMUnit 1.0 0.9 0.2 0.9
/vis/geometry/set/forceSolid SiPMUnit 1

# Trajectories
/tracking/storeTrajectory 1
/vis/scene/add/trajectories smooth
/vis/modeling/trajectories/create/drawByParticleID
/vis/modeling/trajectories/drawByParticleID-0/set e- blue
/vis/scene/add/axes
/vis/scene/add/scale
/vis/viewer/set/viewpointThetaPhi 60 45
/vis/viewer/set/autoRefresh true
/vis/viewer/flush

# Particle gun and run
/gun/particle e-
/gun/energy 500 MeV
/gun/position 0 0 0 mm
/gun/direction 0 0 1
/run/beamOn 1
/vis/viewer/flush
EOFMACRO

# Use batch mode by providing config file
# But this won't execute vis commands...
# So we need to pipe commands instead

echo "Method 1: Pipe commands to SLabSimu (GUI mode with auto-exit)"
echo "-------------------------------------------------------------------"

(
    echo "/vis/open VRML2FILE"
    echo "/run/initialize"
    echo "/vis/drawVolume"
    echo "/vis/geometry/set/visibility World 0"
    echo "/vis/geometry/set/visibility VoxelWrapper 1"
    echo "/vis/geometry/set/colour VoxelWrapper 0.9 0.9 0.9 0.05"
    echo "/vis/geometry/set/forceSolid VoxelWrapper 1"
    echo "/vis/geometry/set/visibility Voxel 1"
    echo "/vis/geometry/set/colour Voxel 0.3 0.5 1.0 0.25"
    echo "/vis/geometry/set/forceSolid Voxel 1"
    echo "/vis/geometry/set/visibility Scintillator 1"
    echo "/vis/geometry/set/colour Scintillator 0.4 0.6 1.0 0.3"
    echo "/vis/geometry/set/forceSolid Scintillator 1"
    echo "/vis/geometry/set/visibility FiberCore_Z 1"
    echo "/vis/geometry/set/colour FiberCore_Z 0.2 0.8 0.2 0.8"
    echo "/vis/geometry/set/forceSolid FiberCore_Z 1"
    echo "/vis/geometry/set/visibility FiberClad_Z 1"
    echo "/vis/geometry/set/colour FiberClad_Z 0.6 0.9 0.6 0.3"
    echo "/vis/geometry/set/forceSolid FiberClad_Z 1"
    echo "/vis/geometry/set/visibility FiberCore_X 1"
    echo "/vis/geometry/set/colour FiberCore_X 0.9 0.2 0.2 0.8"
    echo "/vis/geometry/set/forceSolid FiberCore_X 1"
    echo "/vis/geometry/set/visibility FiberClad_X 1"
    echo "/vis/geometry/set/colour FiberClad_X 0.95 0.6 0.6 0.3"
    echo "/vis/geometry/set/forceSolid FiberClad_X 1"
    echo "/vis/geometry/set/visibility FiberCore_Y 1"
    echo "/vis/geometry/set/colour FiberCore_Y 0.8 0.2 0.8 0.8"
    echo "/vis/geometry/set/forceSolid FiberCore_Y 1"
    echo "/vis/geometry/set/visibility FiberClad_Y 1"
    echo "/vis/geometry/set/colour FiberClad_Y 0.9 0.6 0.9 0.3"
    echo "/vis/geometry/set/forceSolid FiberClad_Y 1"
    echo "/vis/geometry/set/visibility SiPMUnit 1"
    echo "/vis/geometry/set/colour SiPMUnit 1.0 0.9 0.2 0.9"
    echo "/vis/geometry/set/forceSolid SiPMUnit 1"
    echo "/tracking/storeTrajectory 1"
    echo "/vis/scene/add/trajectories smooth"
    echo "/vis/modeling/trajectories/create/drawByParticleID"
    echo "/vis/modeling/trajectories/drawByParticleID-0/set e- blue"
    echo "/vis/scene/add/axes"
    echo "/vis/scene/add/scale"
    echo "/vis/viewer/set/viewpointThetaPhi 60 45"
    echo "/vis/viewer/set/autoRefresh true"
    echo "/vis/viewer/flush"
    echo "/gun/particle e-"
    echo "/gun/energy 500 MeV"
    echo "/gun/position 0 0 0 mm"
    echo "/gun/direction 0 0 1"
    echo "/run/beamOn 1"
    echo "/vis/viewer/flush"
    echo "echo 'VRML export complete, checking file:'"
    echo "/control/shell ls -lh g4*.wrl 2>/dev/null || echo 'No .wrl file'"
    echo "exit"
) | ./SimuTemplate 2>&1 | tee vrml_export.log

echo ""
echo "======================================================================"
echo "Checking output..."
echo "======================================================================"

if [ -f "g4_00.wrl" ]; then
    echo "SUCCESS: g4_00.wrl created!"
    ls -lh g4_00.wrl
    echo ""
    echo "Download with:"
    echo "  scp $BUILD_DIR/g4_00.wrl ."
else
    echo "FAILED: No g4_00.wrl file found"
    echo ""
    echo "Checking log for errors:"
    grep -i "error\|exception\|failed" vrml_export.log | tail -20
fi

echo "======================================================================"

# Cleanup
rm -f /tmp/vrml_export.mac
