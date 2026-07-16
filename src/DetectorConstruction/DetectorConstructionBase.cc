/*
 * DetectorConstructionBase.cc
 *
 * Implementation of the abstract base class for detector construction.
 *
 * Created on: 2024
 * Author: Claude Code (Refactoring)
 */

#include "DetectorConstruction/DetectorConstructionBase.hh"
#include "DetectorConstruction/MaterialManager.hh"

#include "G4Box.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

#include <stdexcept>

DetectorConstructionBase::DetectorConstructionBase(const char* config_path)
    : fConfigPath(config_path),
      fWorldPhysical(nullptr),
      fWorldLogical(nullptr)
{
    fLogger = create_logger("DetectorConstructionBase");

    // Initialize MaterialManager with the configuration
    if (!MaterialManager::Instance()->BuildEverything(config_path)) {
        fLogger->error("Failed to build materials from config: {}", config_path);
        throw std::runtime_error(
            "DetectorConstructionBase: MaterialManager::BuildEverything failed for " +
            std::string(config_path));
    }
}

G4VPhysicalVolume* DetectorConstructionBase::Construct()
{
    fLogger->info("Building detector geometry...");

    // Step 1: Build world volume
    auto [worldPhysical, worldLogical] = BuildWorldVolume();
    fWorldPhysical = worldPhysical;
    fWorldLogical = worldLogical;

    // Step 2: Delegate detector-specific construction to subclass
    G4VPhysicalVolume* result = ConstructDetector(fWorldLogical);

    // NOTE: Sensitive detectors are now registered in ConstructSDandField()
    // which is called AFTER Construct() by G4RunManager. This is the correct
    // GEANT4 lifecycle for SD registration.

    fLogger->info("Detector geometry construction complete.");

    return result;
}

void DetectorConstructionBase::ConstructSDandField()
{
    fLogger->info("Registering sensitive detectors via ConstructSDandField()...");

    // CRITICAL FIX: This is the CORRECT place to register sensitive detectors
    // in GEANT4. The G4RunManager calls this method AFTER Construct() completes.
    // Previously, we called BuildSensitiveDetectors() in Construct(), which was
    // too early in the GEANT4 lifecycle and caused zero hits.
    BuildSensitiveDetectors();

    fLogger->info("Sensitive detector registration complete.");
}

std::pair<G4VPhysicalVolume*, G4LogicalVolume*> DetectorConstructionBase::BuildWorldVolume()
{
    fLogger->info("Building world volume...");

    // World size: 10m x 10m x 10m box
    G4double world_size = 10.0 * m;

    G4Box* solidWorld = new G4Box(
        "World_Solid",
        0.5 * world_size,
        0.5 * world_size,
        0.5 * world_size
    );

    // CRITICAL FIX: Use G4_AIR with optical properties instead of Vacuum
    // Vacuum lacks RINDEX, causing Geant4 to kill optical photons at boundaries
    G4Material* matWorld = G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR");

    fLogger->info("  World material: G4_AIR (with RINDEX for optical physics)");

    G4LogicalVolume* logicWorld = new G4LogicalVolume(
        solidWorld,
        matWorld,
        "World"
    );

    G4VPhysicalVolume* physWorld = new G4PVPlacement(
        nullptr,                // no rotation
        G4ThreeVector(),        // at (0,0,0)
        logicWorld,             // logical volume
        "World",                // name
        nullptr,                // mother volume (none for world)
        false,                  // no boolean operation
        0,                      // copy number
        false                   // overlaps checking
    );

    return {physWorld, logicWorld};
}
