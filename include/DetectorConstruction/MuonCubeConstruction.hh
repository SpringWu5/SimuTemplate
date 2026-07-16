/*
 * MuonCubeConstruction.hh
 *
 * MuonCube detector construction - 8x8x4 pixelated voxel array.
 * Phase 2.3 Debug: Pixelated SiPM readout with optical photon detection.
 *
 * Created on: 2024
 * Author: Claude Code
 */

#ifndef MUONCUBE_CONSTRUCTION_HH
#define MUONCUBE_CONSTRUCTION_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"

#include "G4LogicalVolume.hh"
#include "G4VSolid.hh"

#include <vector>

/**
 * @brief MuonCube detector construction - Phase 2.3 Debug
 *
 * Builds an 8x8x4 pixelated scintillator voxel array with WLS fiber readout
 * and pixelated SiPM optical photon detection.
 *
 * Phase 2.2 Specifications (VoxelWrapper Design):
 * - Voxel size: 25mm x 25mm x 25mm scintillator with 3 orthogonal holes
 * - Wrapper: 25.1mm x 25.1mm x 25.1mm AIR container
 * - Fibers: BCF-92 WLS fibers (Core R=0.95mm, Clad R=1.00mm)
 *   - Z-Fiber: Vertical at (0,0,0)
 *   - X-Fiber: Along X at (0,-3mm,0)
 *   - Y-Fiber: Along Y at (-3mm,0,0)
 * - Array dimensions: 8(X) x 8(Y) x 4(Z) = 256 voxels
 * - Pitch: 25.1mm (wrapper size)
 * - Material: SP101 plastic scintillator with TiO2 coating
 *
 * Phase 2.3 Debug Specifications (Pixelated SiPM Readout):
 * - SiPM unit: 3x3x1 mm silicon pixel
 * - Z-SiPMs: 128 units (8x8x2) at Z+ and Z- boundaries
 * - X-SiPMs: 64 units (8x4x2) at X+ and X- boundaries with Y offset -3mm
 * - Y-SiPMs: 64 units (8x4x2) at Y+ and Y- boundaries with X offset -3mm
 * - Total: 256 pixelated SiPM units for optical photon detection
 *
 * Voxel ID encoding: ID = layer*1000 + row*100 + col
 * where layer = Z index (0-3), row = Y index (0-7), col = X index (0-7)
 */
class MuonCubeConstruction : public DetectorConstructionBase
{
public:
    /**
     * @brief Constructor
     * @param config_path Path to the YAML configuration file
     */
    explicit MuonCubeConstruction(const char* config_path);

    /**
     * @brief Virtual destructor
     */
    virtual ~MuonCubeConstruction() = default;

protected:
    /**
     * @brief Construct the MuonCube detector geometry
     * @param worldLogical The world logical volume to place detector in
     * @return The world physical volume
     */
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;

    /**
     * @brief Setup sensitive detectors for the voxel array
     */
    virtual void BuildSensitiveDetectors() override;

private:
    /**
     * @brief Load MuonCube geometry parameters from config
     */
    void LoadGeometryParameters();

    // Phase 2.2: VoxelWrapper Design Methods

    /**
     * @brief Construct scintillator with 3 orthogonal holes
     * @return Logical volume of the scintillator
     */
    G4LogicalVolume* ConstructScintillator();

    /**
     * @brief Construct reflector shell with TiO2 coating and fiber cutouts
     * @return Logical volume of the reflector shell
     */
    G4LogicalVolume* ConstructReflector();

    /**
     * @brief Construct WLS fiber (core + cladding)
     * @param fiberName Name suffix for the fiber (e.g., "X", "Y", "Z")
     * @param halfLength Half-length of the fiber (default: wrapperSize/2)
     * @return Pair of (coreLogical, cladLogical)
     */
    std::pair<G4LogicalVolume*, G4LogicalVolume*> ConstructFiber(const G4String& fiberName,
                                                                  G4double halfLength = -1.0);

    /**
     * @brief Build the complete voxel wrapper (AIR) containing scintillator + fibers
     */
    void BuildVoxelWrapper();

    /**
     * @brief Place all voxel wrappers in the array
     * @param worldLogical The world logical volume
     */
    void PlaceVoxelArray(G4LogicalVolume* worldLogical);

    // Phase 2.3: Pixelated SiPM Methods

    /**
     * @brief Build pixelated SiPM units at fiber ends
     *
     * Creates 3x3x1mm SiPM units placed at the end of each fiber
     * at the detector array boundaries.
     */
    void ConstructPixelatedSiPMs();

    /**
     * @brief Attach SiPM sensitive detector to all pixelated SiPM units
     */
    void AttachSiPMSensitiveDetectors();

    /**
     * @brief Encode voxel position into unique CopyNumber
     * @param layer Z layer index (0-3)
     * @param row Y row index (0-7)
     * @param col X column index (0-7)
     * @return Unique copy number: layer*1000 + row*100 + col
     */
    inline int EncodeVoxelID(int layer, int row, int col) const {
        return layer * 1000 + row * 100 + col;
    }

    /**
     * @brief Decode voxel ID back to indices
     * @param copyNumber The encoded voxel ID
     * @param layer Output: Z layer index
     * @param row Output: Y row index
     * @param col Output: X column index
     */
    static void DecodeVoxelID(int copyNumber, int& layer, int& row, int& col) {
        layer = copyNumber / 1000;
        row = (copyNumber % 1000) / 100;
        col = copyNumber % 100;
    }

    // Geometry parameters (loaded from config)
    double fVoxelSize;      // Size of each cubic scintillator (default: 25mm)
    double fWrapperSize;    // Size of wrapper (voxel + gap, default: 25.1mm)
    double fFiberRadius;    // Fiber cladding radius (default: 1.0mm)
    double fCoreRadius;     // Fiber core radius (default: 0.95mm)
    double fHoleRadius;     // Scintillator hole radius (default: 1.05mm)
    int fArrayX;            // Number of voxels in X (default: 8)
    int fArrayY;            // Number of voxels in Y (default: 8)
    int fArrayZ;            // Number of layers in Z (default: 4)
    double fGap;            // Gap between voxels (default: 0.1mm)
    std::string fMaterial;  // Scintillator material name (default: "SP101")

    // Phase 2.2 Geometry objects
    G4LogicalVolume* fLogicVoxelWrapper;     // AIR wrapper
    G4LogicalVolume* fLogicScintillator;     // SP101 with holes
    G4LogicalVolume* fLogicFiberCore;        // BCF92_Core
    G4LogicalVolume* fLogicFiberClad;        // BCF92_Clad

    // Phase 2.3: Pixelated SiPM Logical Volume
    G4LogicalVolume* fLogicSiPMUnit;         // Single 3x3x1mm SiPM unit
};

#endif // MUONCUBE_CONSTRUCTION_HH
