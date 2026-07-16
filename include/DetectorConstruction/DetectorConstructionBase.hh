/*
 * DetectorConstructionBase.hh
 *
 * Abstract base class for detector construction.
 * Supports factory pattern for runtime detector selection (MuonSLab / MuonCube).
 *
 * Created on: 2024
 * Author: Claude Code (Refactoring)
 */

#ifndef DETECTORCONSTRUCTION_BASE_HH
#define DETECTORCONSTRUCTION_BASE_HH

#include "G4VUserDetectorConstruction.hh"
#include "G4VPhysicalVolume.hh"
#include "G4LogicalVolume.hh"
#include "G4String.hh"
#include "Util/Logger.hh"

#include <memory>

class MaterialManager;

/**
 * @brief Abstract base class for all detector constructions
 *
 * This class provides a common interface for building different detector
 * geometries (MuonSLab, MuonCube, etc.) using the factory pattern.
 *
 * Subclasses must implement:
 * - ConstructDetector(): Build the detector-specific geometry
 * - BuildSensitiveDetectors(): Setup sensitive detector regions
 */
class DetectorConstructionBase : public G4VUserDetectorConstruction
{
public:
    /**
     * @brief Constructor
     * @param config_path Path to the YAML configuration file
     */
    explicit DetectorConstructionBase(const char* config_path);

    /**
     * @brief Virtual destructor for proper cleanup
     */
    virtual ~DetectorConstructionBase() = default;

    /**
     * @brief Main construction method called by G4RunManager
     *
     * This method creates the world volume and delegates detector-specific
     * construction to the pure virtual ConstructDetector() method.
     *
     * @return Pointer to the world physical volume
     */
    virtual G4VPhysicalVolume* Construct() override final;

    /**
     * @brief GEANT4 method for sensitive detector and field setup
     *
     * This method is called AFTER geometry construction to register
     * sensitive detectors. Overrides G4VUserDetectorConstruction method.
     */
    virtual void ConstructSDandField() override final;

protected:
    /**
     * @brief Pure virtual method for detector-specific geometry construction
     *
     * Subclasses implement this to build their specific geometry within
     * the provided world volume.
     *
     * @param worldLogical The logical volume of the world
     * @return Pointer to the world physical volume (for consistency checking)
     */
    virtual G4VPhysicalVolume* ConstructDetector(G4LogicalVolume* worldLogical) = 0;

    /**
     * @brief Pure virtual method for setting up sensitive detectors
     *
     * Called after geometry construction to attach sensitive detectors
     * to the appropriate logical volumes.
     */
    virtual void BuildSensitiveDetectors() = 0;

    /**
     * @brief Build the world volume
     *
     * Creates a vacuum-filled world box of standard size.
     *
     * @return Pair of world physical and logical volumes
     */
    std::pair<G4VPhysicalVolume*, G4LogicalVolume*> BuildWorldVolume();

    // Protected members accessible to derived classes
    std::shared_ptr<spdlog::logger> fLogger;
    const char* fConfigPath;
    G4VPhysicalVolume* fWorldPhysical;
    G4LogicalVolume* fWorldLogical;
};

#endif // DETECTORCONSTRUCTION_BASE_HH
