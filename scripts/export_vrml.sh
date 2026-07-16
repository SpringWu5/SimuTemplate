#!/bin/bash
# ==============================================================================
# VRML Export Script - Export MuonCube geometry without GUI
# ==============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/build"

echo "======================================================================"
echo "MuonCube VRML Export Script"
echo "======================================================================"
echo ""

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    echo "ERROR: Build directory not found: $BUILD_DIR"
    echo "Please run: mkdir -p $BUILD_DIR && cd $BUILD_DIR && cmake .."
    exit 1
fi

# Check if SLabSimu executable exists
if [ ! -f "$BUILD_DIR/SimuTemplate" ]; then
    echo "ERROR: SLabSimu executable not found in $BUILD_DIR"
    echo "Please compile the project first"
    exit 1
fi

echo "Changing to build directory: $BUILD_DIR"
cd "$BUILD_DIR"

echo ""
echo "Running simulation in VRML export mode..."
echo "Output file will be: $BUILD_DIR/g4_00.wrl"
echo ""
echo "Note: This will open a GUI window. Wait for the event to complete,"
echo "      then type 'exit' at the GUI prompt."
echo ""

# Run SLabSimu with the batch VRML export macro
# Using input redirection to feed commands to the program
cat << 'EOF' | ./SLabSimu
/vis/verbose errors
/vis/open VRML2FILE
/run/initialize
/vis/drawVolume
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
/tracking/storeTrajectory 1
/vis/scene/add/trajectories smooth
/vis/modeling/trajectories/create/drawByParticleID
/vis/modeling/trajectories/drawByParticleID-0/set opticalphoton yellow
/vis/modeling/trajectories/drawByParticleID-0/set e- blue
/vis/scene/add/axes
/vis/scene/add/scale
/vis/viewer/set/viewpointThetaPhi 60 45
/vis/viewer/set/autoRefresh true
/vis/viewer/flush
/gun/particle e-
/gun/energy 500 MeV
/gun/position 0 0 0 mm
/gun/direction 0 0 1
/run/beamOn 1
/vis/viewer/flush
/control/sleep 1
echo "Checking for .wrl file:"
/control/shell ls -lh g4*.wrl 2>/dev/null || echo "No .wrl file yet"
exit
EOF

echo ""
echo "======================================================================"
echo "Export complete! Checking for output file..."
echo "======================================================================"

# Check if VRML file was created
if [ -f "g4_00.wrl" ]; then
    FILE_SIZE=$(ls -lh g4_00.wrl | awk '{print $5}')
    echo "SUCCESS: VRML file created!"
    echo "  File: $BUILD_DIR/g4_00.wrl"
    echo "  Size: $FILE_SIZE"
    echo ""
    echo "To download to your local computer, run:"
    echo "  scp YOUR_USER@cluster:$BUILD_DIR/g4_00.wrl ."
    echo ""
    echo "To view the file:"
    echo "  - macOS: open g4_00.wrl"
    echo "  - Linux: freewrl g4_00.wrl or blender g4_00.wrl"
    echo "  - Windows: Open with Cortona3D or Blender"
    echo "  - Online: Upload to https://www.web3d.org/x3d/vrml/editors/viewers"
else
    echo "ERROR: VRML file (g4_00.wrl) was not created!"
    echo ""
    echo "Checking for any .wrl files:"
    ls -lh *.wrl 2>/dev/null || echo "No .wrl files found"
    echo ""
    echo "Please check the log output above for errors."
fi

echo "======================================================================"
