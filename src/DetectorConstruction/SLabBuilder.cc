/*
 * SLabBuilder.cc
 *
 * MuonSLab detector construction implementation.
 * Refactored to extend DetectorConstructionBase.
 *
 * Created on: 2024.09.28
 * Author: Weilun Huang
 * Refactored: 2024 (Claude Code)
 */

#include "DetectorConstruction/SLabBuilder.hh"
#include "DetectorConstruction/SipmBuilder.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "DetectorConstruction/SensitiveDetectors/SLabSensitiveDetector.hh"

#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4Sphere.hh"
#include "G4Element.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4PVPlacement.hh"
#include "G4ThreeVector.hh"
#include "G4RotationMatrix.hh"
#include "G4Box.hh"
#include "G4SubtractionSolid.hh"
#include "G4NistManager.hh"

SLabBuilder::SLabBuilder(const char* config_path)
    : DetectorConstructionBase(config_path),
      fLogicScint(nullptr),
      fLogicESR(nullptr),
      fLogicTape(nullptr),
      fLogicBattery(nullptr),
      fSolidSlabScint(nullptr),
      fSolidSlabESR(nullptr),
      fSolidSlabTape(nullptr),
      fSolidBattery(nullptr)
{
    // Logger is already created by base class, update name for this class
    fLogger = create_logger("SLabBuilder");
}

vector<G4Transform3D> SLabBuilder::GetTransformsForSiPMs()
{
    vector<G4Transform3D> transforms;
    const auto& geoSlab = MaterialManager::Instance()->GetSLabGeometry();

    G4RotationMatrix rotation_matrix;
    double position_x = 0, position_y = 0;

    // Transforms to place SiPMs on the scintillator X faces
    rotation_matrix.rotateY(90 * deg);
    position_x = geoSlab.Scintxlength / 2 + geoSlab.SiPMzlength / 2;
    // Loop over left and right faces
    for (auto& sign_x : {-1, 1}) {
        // Loop over 3 SiPMs on each face
        for (int i = 0; i < 3; i++) {
            position_y = geoSlab.Scintylength / 4 * (i - 1);
            transforms.push_back(G4Transform3D(rotation_matrix, G4ThreeVector(sign_x * position_x, position_y, 0)));
        }
    }

    // Transforms to place SiPMs on the scintillator Y faces
    rotation_matrix.set(0, 0, 0);
    rotation_matrix.rotateX(90 * deg);
    position_y = geoSlab.Scintylength / 2 + geoSlab.SiPMzlength / 2;
    // Loop over top and bottom faces
    for (auto& sign_y : {-1, 1}) {
        // Loop over 3 SiPMs on each face
        for (int i = 0; i < 3; i++) {
            position_x = geoSlab.Scintxlength / 4 * (i - 1);
            transforms.push_back(G4Transform3D(rotation_matrix, G4ThreeVector(position_x, sign_y * position_y, 0)));
        }
    }

    return transforms;
}

G4VPhysicalVolume* SLabBuilder::ConstructDetector(G4LogicalVolume* worldLogical)
{
    fLogger->info("Building MuonSLab detector...");

    // Build solid geometries
    BuildSolid();

    // Get materials
    auto matScint = MaterialManager::Instance()->GetMaterial("Scint");
    auto matESR = MaterialManager::Instance()->GetMaterial("ESR");
    auto matTape = MaterialManager::Instance()->GetMaterial("Tape");
    auto matBattery = MaterialManager::Instance()->GetMaterial("Battery");

    // Create logical volumes
    fLogicScint = new G4LogicalVolume(fSolidSlabScint, matScint, "Scint");
    fLogicESR = new G4LogicalVolume(fSolidSlabESR, matESR, "ESR");
    fLogicTape = new G4LogicalVolume(fSolidSlabTape, matTape, "Tape");
    fLogicBattery = new G4LogicalVolume(fSolidBattery, matBattery, "Battery");

    // Build optical surfaces
    BuildSurface();

    // Place battery
    new G4PVPlacement(0,
                      G4ThreeVector(0, 0, -40.8 * mm),
                      fLogicBattery,
                      "Battery",
                      worldLogical,
                      false,
                      0,
                      false);

    // Place scintillator slabs
    const auto& geoSlab = MaterialManager::Instance()->GetSLabGeometry();
    const double total_thickness = geoSlab.Scintzlength + geoSlab.ESRthickness + geoSlab.Tapethickness;

    for (int i = 0; i < geoSlab.numberOfSlabs; i++) {
        new G4PVPlacement(0,
                          G4ThreeVector(0, 0, geoSlab.slabOffsets[i] + total_thickness * (i - 1)),
                          fLogicScint,
                          "Scint",
                          worldLogical,
                          false,
                          i,
                          false);
    }

    // Build and place SiPMs
    SipmBuilder sipm = SipmBuilder();
    sipm.Build();
    auto logicSipm = sipm.GetLogicVolume();

    vector<G4Transform3D> transforms = GetTransformsForSiPMs();
    for (long unsigned int i = 0; i < transforms.size(); i++) {
        G4ThreeVector sipmPosition = transforms[i].getTranslation();

        for (int j = 0; j < geoSlab.numberOfSlabs; j++) {
            G4ThreeVector slabPosition(0, 0, geoSlab.slabOffsets[j] + total_thickness * (j - 1));
            G4ThreeVector finalPosition = slabPosition + sipmPosition;

            G4RotationMatrix rotMatrix = transforms[i].getRotation();

            new G4PVPlacement(G4Transform3D(rotMatrix, finalPosition),
                              logicSipm,
                              "SiPM",
                              worldLogical,
                              false,
                              i * geoSlab.numberOfSlabs + j,
                              true);
        }
    }

    fLogger->info("MuonSLab detector construction complete!");

    return fWorldPhysical;
}

void SLabBuilder::BuildSolid()
{
    const auto& geoSlab = MaterialManager::Instance()->GetSLabGeometry();

    fSolidSlabScint = new G4Box("Slab",
                                geoSlab.Scintxlength / 2,
                                geoSlab.Scintylength / 2,
                                geoSlab.Scintzlength / 2);

    fSolidSlabESR = new G4Box("ESRshape",
                              (geoSlab.Scintxlength + geoSlab.ESRthickness) / 2,
                              (geoSlab.Scintylength + geoSlab.ESRthickness) / 2,
                              (geoSlab.Scintzlength + geoSlab.ESRthickness) / 2);

    fSolidSlabTape = new G4Box("Tape",
                               (geoSlab.Scintxlength + geoSlab.ESRthickness + geoSlab.Tapethickness) / 2,
                               (geoSlab.Scintylength + geoSlab.ESRthickness + geoSlab.Tapethickness) / 2,
                               (geoSlab.Scintzlength + geoSlab.ESRthickness + geoSlab.Tapethickness) / 2);

    fSolidBattery = new G4Box("Battery",
                              geoSlab.Batteryxlength / 2,
                              geoSlab.Batteryylength / 2,
                              geoSlab.Batteryzlength / 2);

    fSolidSlabTape = new G4SubtractionSolid("Tape",
                                            fSolidSlabTape,
                                            fSolidSlabESR,
                                            0,
                                            G4ThreeVector(0, 0, 0));

    fSolidSlabESR = new G4SubtractionSolid("ESR",
                                           fSolidSlabESR,
                                           fSolidSlabScint,
                                           0,
                                           G4ThreeVector(0, 0, 0));

    G4Box* sipmoccupied = new G4Box("SiPMoccupied",
                                    geoSlab.SiPMxlength / 2,
                                    geoSlab.SiPMylength / 2,
                                    geoSlab.SiPMzlength / 2);

    // Subtract SiPMs from ESR and Tape
    vector<G4Transform3D> transforms = GetTransformsForSiPMs();
    for (auto& transform : transforms) {
        fSolidSlabESR = new G4SubtractionSolid("ESR",
                                               fSolidSlabESR,
                                               sipmoccupied,
                                               transform);

        fSolidSlabTape = new G4SubtractionSolid("Tape",
                                                fSolidSlabTape,
                                                sipmoccupied,
                                                transform);
    }
}

void SLabBuilder::BuildSurface()
{
    // Create optical surface for scintillator
    G4OpticalSurface* opScintSurface = new G4OpticalSurface("ScintSurface", glisur, polished, dielectric_dielectric);
    new G4LogicalSkinSurface("Scint", fLogicScint, opScintSurface);
}

void SLabBuilder::BuildSensitiveDetectors()
{
    SLabSensitiveDetector* slabSensitiveDetector = new SLabSensitiveDetector("Slab");
    G4SDManager::GetSDMpointer()->AddNewDetector(slabSensitiveDetector);
    fLogicScint->SetSensitiveDetector(slabSensitiveDetector);

    fLogger->info("Sensitive detectors registered for MuonSLab.");
}
