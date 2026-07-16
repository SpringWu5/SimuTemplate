/*
 * SLabBuilder.hh
 *
 * MuonSLab detector construction - 4-layer scintillator slab geometry.
 * Refactored to extend DetectorConstructionBase for factory pattern support.
 *
 * Created on: 2024.09.28
 * Author: Weilun Huang
 * Refactored: 2024 (Claude Code)
 */

#ifndef SLABBUILDER_HH
#define SLABBUILDER_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"

#include "G4LogicalVolume.hh"
#include "G4VSolid.hh"
#include "G4Transform3D.hh"
#include "vector"

using std::vector;

/**
 * @brief MuonSLab detector construction
 *
 * Builds a 4-layer scintillator slab detector with SiPMs.
 * Configuration is read from config.yaml under Geometry.SLab section.
 *
 * Geometry:
 * - 4 scintillator slabs (configurable via config)
 * - 12 SiPMs per slab (3 per side on X and Y faces)
 * - ESR reflector and tape wrapping
 */
class SLabBuilder : public DetectorConstructionBase
{
public:
    /**
     * @brief Constructor
     * @param config_path Path to the YAML configuration file
     */
    explicit SLabBuilder(const char* config_path);

    /**
     * @brief Virtual destructor
     */
    virtual ~SLabBuilder() = default;

protected:
    /**
     * @brief Construct the MuonSLab detector geometry
     * @param worldLogical The world logical volume to place detector in
     * @return The world physical volume
     */
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) override;

    /**
     * @brief Setup sensitive detectors for the scintillator slabs
     */
    virtual void BuildSensitiveDetectors() override;

private:
    /**
     * @brief Calculate transform matrices for SiPM placement
     * @return Vector of transforms for each SiPM position
     */
    vector<G4Transform3D> GetTransformsForSiPMs();

    /**
     * @brief Build solid geometry for slabs, ESR, tape
     */
    void BuildSolid();

    /**
     * @brief Build optical surfaces for materials
     */
    void BuildSurface();

    // Logical volumes
    G4LogicalVolume* fLogicScint;
    G4LogicalVolume* fLogicESR;
    G4LogicalVolume* fLogicTape;
    G4LogicalVolume* fLogicBattery;

    // Solid shapes
    G4VSolid* fSolidSlabScint;
    G4VSolid* fSolidSlabESR;
    G4VSolid* fSolidSlabTape;
    G4VSolid* fSolidBattery;
};

#endif // SLABBUILDER_HH
