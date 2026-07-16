/*
 * DetectorFactory.cc
 *
 * Implementation of the detector factory for runtime detector selection.
 *
 * Created on: 2024
 * Author: Claude Code (Refactoring)
 */

#include "DetectorConstruction/DetectorFactory.hh"
#include "DetectorConstruction/SLabBuilder.hh"
#include "DetectorConstruction/MuonCubeConstruction.hh"

#include "Util/Logger.hh"
#include "spdlog/spdlog.h"

#include <stdexcept>
#include <algorithm>

DetectorConstructionBase* DetectorFactory::Create(const G4String& detectorType,
                                                   const char* config_path)
{
    auto logger = create_logger("DetectorFactory");

    logger->info("Creating detector of type: {}", detectorType.c_str());

    // Convert to lowercase for case-insensitive comparison
    G4String typeLower = detectorType;
    std::transform(typeLower.begin(), typeLower.end(), typeLower.begin(), ::tolower);

    if (typeLower == "muonslab" || typeLower == "slab") {
        logger->info("Instantiating MuonSLab detector (4-layer slab geometry)");
        return new SLabBuilder(config_path);
    }
    else if (typeLower == "muoncube" || typeLower == "cube") {
        logger->info("Instantiating MuonCube detector (8x8x4 voxel array)");
        return new MuonCubeConstruction(config_path);
    }
    else {
        logger->error("Unknown detector type: {}", detectorType.c_str());
        logger->error("Supported types: MuonSLab, MuonCube");

        throw std::runtime_error(
            "DetectorFactory: Unknown detector type '" + std::string(detectorType.c_str()) +
            "'. Supported types: MuonSLab, MuonCube"
        );
    }
}

std::vector<G4String> DetectorFactory::GetSupportedTypes()
{
    return {"MuonSLab", "MuonCube"};
}
