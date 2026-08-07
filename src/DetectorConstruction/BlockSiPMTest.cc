#include "DetectorConstruction/BlockSiPMTest.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "DetectorConstruction/SensitiveDetectors/SingleSlabSiPMSensitiveDetector.hh"
#include "DetectorConstruction/SensitiveDetectors/SLabSensitiveDetector.hh"

#include "G4Box.hh"
#include "G4SubtractionSolid.hh"
#include "G4VSolid.hh"
#include "G4PVPlacement.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4SDManager.hh"

#include "yaml-cpp/yaml.h"

BlockSiPMTest::BlockSiPMTest(const char* config_path)
    : DetectorConstructionBase(config_path)
{
    fLogger = create_logger("BlockSiPMTest");
    LoadParameters();
}

void BlockSiPMTest::LoadParameters()
{
    try {
        auto cfg = MaterialManager::Instance()->getRootNode();
        if (cfg["BlockTest"]) {
            auto n = cfg["BlockTest"];
            if (n["bx"])              fBx              = n["bx"].as<double>();       // mm
            if (n["by"])              fBy              = n["by"].as<double>();
            if (n["bz"])              fBz              = n["bz"].as<double>();
            if (n["esr_thickness"])   fESRThick        = n["esr_thickness"].as<double>();
            if (n["active_thickness"])fActiveThick     = n["active_thickness"].as<double>();
            if (n["esr_reflectivity"])fESRReflectivity = n["esr_reflectivity"].as<double>();
            if (n["active_size"])     fActiveSize      = n["active_size"].as<double>();
        }
    } catch (const YAML::Exception& e) {
        fLogger->warn("Failed to read BlockTest config ({}); using defaults", e.what());
    }
    fLogger->info("BlockSiPMTest: block {:.1f} x {:.1f} x {:.1f} mm, SiPM active {:.1f} mm on +Y face, ESR {:.2f} mm (R={:.2f})",
                  fBx, fBy, fBz, fActiveSize, fESRThick, fESRReflectivity);
}

G4VPhysicalVolume* BlockSiPMTest::ConstructDetector(G4LogicalVolume* worldLogical)
{
    fWorldLogical = worldLogical;
    auto matMgr = MaterialManager::Instance();
    G4Material* scintMat = matMgr->GetMaterial("Scint");
    G4Material* esrMat   = matMgr->GetMaterial("ESR");
    G4Material* sipmMat  = matMgr->GetMaterial("SiPM");

    const G4double hx = fBx / 2.0, hy = fBy / 2.0, hz = fBz / 2.0;
    const G4double halfActive = fActiveSize / 2.0;
    const G4double halfThick  = fActiveThick / 2.0;
    const G4double margin     = 0.02 * mm;
    const G4double halfFoot   = halfActive + margin;
    const G4double halfDepth  = fESRThick / 2.0 + margin;

    // --- Scintillator block (axes: X edge-parallel, Y inward, Z vertical) ---
    auto* blockSolid = new G4Box("Block", hx, hy, hz);
    fLogicScint = new G4LogicalVolume(blockSolid, scintMat, "Block");
    new G4PVPlacement(nullptr, G4ThreeVector(), fLogicScint, "Block", worldLogical, false, 0, true);

    auto* scintSurf = new G4OpticalSurface("BlockSurface", glisur, polished, dielectric_dielectric);
    new G4LogicalSkinSurface("BlockSkin", fLogicScint, scintSurf);

    // --- SiPM active area on the +Y face (footprint X x Z, thickness along Y) ---
    auto* activeSolid = new G4Box("BlockSiPMActive", halfActive, halfThick, halfActive);
    fLogicActive = new G4LogicalVolume(activeSolid, sipmMat, "BlockSiPMActive");

    // --- ESR shell (outer - inner) with one window on +Y for the SiPM ---
    auto* shellOuter = new G4Box("BlockESROuter", hx + fESRThick, hy + fESRThick, hz + fESRThick);
    auto* shellInner = new G4Box("BlockESRInner", hx, hy, hz);
    G4VSolid* shell  = new G4SubtractionSolid("BlockESRShell", shellOuter, shellInner);
    // window through the +Y wall
    auto* win = new G4Box("win", halfFoot, halfDepth, halfFoot);
    shell = new G4SubtractionSolid("BlockESRShell", shell, win, nullptr,
                                   G4ThreeVector(0.0, hy + fESRThick / 2.0, 0.0));

    auto* logicESR = new G4LogicalVolume(shell, esrMat, "BlockESRShell");
    auto* esrSurf = new G4OpticalSurface("BlockESRSurface", unified, groundfrontpainted, dielectric_dielectric);
    esrSurf->SetSigmaAlpha(0.1);
    auto* esrProps = new G4MaterialPropertiesTable();
    const int ne = 2;
    G4double eE[ne] = {2.0 * eV, 4.0 * eV};
    G4double eR[ne] = {fESRReflectivity, fESRReflectivity};
    esrProps->AddProperty("REFLECTIVITY", eE, eR, ne);
    esrSurf->SetMaterialPropertiesTable(esrProps);
    new G4LogicalSkinSurface("BlockESRSkin", logicESR, esrSurf);
    new G4PVPlacement(nullptr, G4ThreeVector(), logicESR, "BlockESRShell", worldLogical, false, 0, true);

    // --- Place the SiPM active volume (channel 0), flush on +Y face ---
    new G4PVPlacement(nullptr, G4ThreeVector(0.0, hy + halfThick, 0.0),
                      fLogicActive, "BlockSiPMActive", worldLogical, false, 0, true);

    fLogger->info("BlockSiPMTest geometry complete (1 SiPM, channel 0).");
    return fWorldPhysical;
}

void BlockSiPMTest::BuildSensitiveDetectors()
{
    auto* sdMgr = G4SDManager::GetSDMpointer();

    auto* sipmSD = new SingleSlabSiPMSensitiveDetector("BlockTest/SiPM");
    sdMgr->AddNewDetector(sipmSD);
    if (fLogicActive) fLogicActive->SetSensitiveDetector(sipmSD);

    auto* slabSD = new SLabSensitiveDetector("BlockTest/Scint");
    sdMgr->AddNewDetector(slabSD);
    if (fLogicScint) fLogicScint->SetSensitiveDetector(slabSD);

    fLogger->info("Sensitive detectors attached (SiPM active area + block Edep).");
}
