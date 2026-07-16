/*
 * DetectorFactory.hh
 *
 * Factory class for creating detector constructions at runtime.
 * Supports: MuonSLab, MuonCube
 *
 * Created on: 2024
 * Author: Claude Code (Refactoring)
 */

#ifndef DETECTOR_FACTORY_HH
#define DETECTOR_FACTORY_HH

#include "DetectorConstruction/DetectorConstructionBase.hh"
#include "G4String.hh"

#include <memory>

/**
 * @brief Factory class for creating detector constructions
 *
 * This factory enables runtime selection of detector geometry
 * based on configuration file settings.
 *
 * Usage:
 *   auto detector = DetectorFactory::Create("MuonCube", config_path);
 *   runManager->SetUserInitialization(detector);
 *
 * Supported detector types:
 *   - "MuonSLab": 4-layer large scintillator slab detector
 *   - "MuonCube": 8x8x4 pixelated voxel array detector
 */
class DetectorFactory
{
public:
    /**
     * @brief Create a detector construction based on type string
     *
     * @param detectorType The type of detector to create ("MuonSLab" or "MuonCube")
     * @param config_path Path to the YAML configuration file
     * @return Pointer to the created detector construction (ownership transferred)
     *
     * @throws std::runtime_error if detector type is not recognized
     */
    static DetectorConstructionBase* Create(const G4String& detectorType,
                                             const char* config_path);

    /**
     * @brief Get list of supported detector types
     * @return Vector of supported detector type names
     */
    static std::vector<G4String> GetSupportedTypes();

private:
    // Static factory - no instances
    DetectorFactory() = delete;
};

#endif // DETECTOR_FACTORY_HH
