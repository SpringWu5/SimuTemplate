#include "DetectorConstruction/SingleSlabSiPMTest.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "DetectorConstruction/SensitiveDetectors/SingleSlabSiPMSensitiveDetector.hh"
#include "DetectorConstruction/SensitiveDetectors/SLabSensitiveDetector.hh"

#include "G4Box.hh"
#include "G4SubtractionSolid.hh"
#include "G4VSolid.hh"
#include "G4PVPlacement.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4SDManager.hh"

#include "yaml-cpp/yaml.h"
#include <vector>
#include <tuple>

SingleSlabSiPMTest::SingleSlabSiPMTest(const char* config_path)
    : DetectorConstructionBase(config_path)
{
    fLogger = create_logger("SingleSlabSiPMTest");
    LoadParameters();
}

void SingleSlabSiPMTest::LoadParameters()
{
    try {
        auto cfg = MaterialManager::Instance()->getRootNode();
        if (cfg["SiPMTest"]) {
            auto n = cfg["SiPMTest"];
            if (n["config"])          fConfig          = n["config"].as<int>();
            if (n["slab_x"])          fSlabX           = n["slab_x"].as<double>();      // mm
            if (n["slab_y"])          fSlabY           = n["slab_y"].as<double>();      // mm
            if (n["slab_z"])          fSlabZ           = n["slab_z"].as<double>();      // mm
            if (n["esr_thickness"])   fESRThick        = n["esr_thickness"].as<double>();
            if (n["active_thickness"])fActiveThick     = n["active_thickness"].as<double>();
            if (n["esr_reflectivity"])fESRReflectivity = n["esr_reflectivity"].as<double>();
            if (n["position_offset"]) fPosOffset       = n["position_offset"].as<double>();
        }
    } catch (const YAML::Exception& e) {
        fLogger->warn("Failed to read SiPMTest config ({}); using defaults", e.what());
    }

    // Derive the "unit SiPM" geometry from the selected config.
    if (fConfig == 1) {            // single 6x6 mm active (physical 7x7)
        fActiveSize = 6.0; fArrayN = 1; fCellPitch = 0.0;
    } else if (fConfig == 2) {     // single 3x3 mm active (physical 4x4)
        fActiveSize = 3.0; fArrayN = 1; fCellPitch = 0.0;
    } else {                       // 2x2 array of 3x3 mm active (1 mm gap, 9x9 footprint)
        fActiveSize = 3.0; fArrayN = 2; fCellPitch = 5.0;  // 4 mm cell + 1 mm gap
    }

    fLogger->info("SingleSlab SiPM-sizing test: config={}, active={:.1f} mm, array={}x{}, pitch={:.1f} mm",
                  fConfig, fActiveSize, fArrayN, fArrayN, fCellPitch);
    fLogger->info("  slab={:.1f} x {:.1f} x {:.1f} mm, ESR={:.2f} mm (R={:.2f}), 8 unit SiPMs at |{}| mm",
                  fSlabX, fSlabY, fSlabZ, fESRThick, fESRReflectivity, fPosOffset);
}

G4VPhysicalVolume* SingleSlabSiPMTest::ConstructDetector(G4LogicalVolume* worldLogical)
{
    fWorldLogical = worldLogical;
    auto matMgr = MaterialManager::Instance();
    G4Material* scintMat = matMgr->GetMaterial("Scint");
    G4Material* esrMat   = matMgr->GetMaterial("ESR");
    G4Material* sipmMat  = matMgr->GetMaterial("SiPM");

    const G4double hx = fSlabX / 2.0, hy = fSlabY / 2.0, hz = fSlabZ / 2.0;
    const G4double halfActive = fActiveSize / 2.0;
    const G4double halfThick  = fActiveThick / 2.0;
    const G4double margin     = 0.02 * mm;          // window clearance
    const G4double halfFoot   = halfActive + margin;
    const G4double halfDepth  = fESRThick / 2.0 + margin;

    // --- Scintillator slab -------------------------------------------------
    auto* scintSolid = new G4Box("Scint", hx, hy, hz);
    fLogicScint = new G4LogicalVolume(scintSolid, scintMat, "Scint");
    new G4PVPlacement(nullptr, G4ThreeVector(), fLogicScint, "Scint", worldLogical, false, 0, true);

    // Polished dielectric skin surface (mirrors SLabBuilder).
    auto* scintSurf = new G4OpticalSurface("ScintSurface", glisur, polished, dielectric_dielectric);
    new G4LogicalSkinSurface("ScintSkin", fLogicScint, scintSurf);

    // --- Active-area solids/logicals (X- and Y-oriented share one SD) -----
    auto* activeSolidX = new G4Box("SiPMActiveX", halfThick, halfActive, halfActive);  // thick along X
    auto* activeSolidY = new G4Box("SiPMActiveY", halfActive, halfThick, halfActive);  // thick along Y
    fLogicActiveX = new G4LogicalVolume(activeSolidX, sipmMat, "SiPMActiveX");
    fLogicActiveY = new G4LogicalVolume(activeSolidY, sipmMat, "SiPMActiveY");

    // --- ESR shell (outer - inner) then punch SiPM windows -----------------
    auto* shellOuter = new G4Box("ESROuter", hx + fESRThick, hy + fESRThick, hz + fESRThick);
    auto* shellInner = new G4Box("ESRInner", hx, hy, hz);
    G4VSolid* shell  = new G4SubtractionSolid("ESRShell", shellOuter, shellInner);

    // Collect active-cell placements to apply after the shell is finalised.
    struct Placement { G4LogicalVolume* lv; G4ThreeVector pos; int copyNo; };
    std::vector<Placement> placements;

    // edge: 0=+X, 1=-X, 2=+Y, 3=-Y
    for (int edge = 0; edge < 4; ++edge) {
        const bool xFace = (edge < 2);
        const G4double sgn = (edge % 2 == 0) ? +1.0 : -1.0;

        for (int pos = 0; pos < 2; ++pos) {
            const G4double along = (pos == 0 ? +fPosOffset : -fPosOffset);  // mm along the edge

            for (int a = 0; a < fArrayN; ++a) {
                for (int b = 0; b < fArrayN; ++b) {
                    const G4double off1 = (a - (fArrayN - 1) / 2.0) * fCellPitch;  // first footprint axis
                    const G4double off2 = (b - (fArrayN - 1) / 2.0) * fCellPitch;  // second footprint axis (Z)
                    const int cellIdx = a * fArrayN + b;
                    const int copyNo = edge * 1000 + pos * 100 + cellIdx;

                    G4LogicalVolume* lv = xFace ? fLogicActiveX : fLogicActiveY;
                    G4ThreeVector ctr;
                    G4VSolid* win = nullptr;
                    if (xFace) {
                        // footprint axes = Y(along), Z(off2); thickness along X
                        const G4double py = along + off1;
                        const G4double pz = off2;
                        ctr = G4ThreeVector(sgn * (hx + halfThick), py, pz);
                        win = new G4Box("win", halfDepth, halfFoot, halfFoot);
                        shell = new G4SubtractionSolid("ESRShell", shell, win, nullptr,
                                                       G4ThreeVector(sgn * (hx + fESRThick / 2.0), py, pz));
                    } else {
                        // footprint axes = X(along), Z(off2); thickness along Y
                        const G4double px = along + off1;
                        const G4double pz = off2;
                        ctr = G4ThreeVector(px, sgn * (hy + halfThick), pz);
                        win = new G4Box("win", halfFoot, halfDepth, halfFoot);
                        shell = new G4SubtractionSolid("ESRShell", shell, win, nullptr,
                                                       G4ThreeVector(px, sgn * (hy + fESRThick / 2.0), pz));
                    }
                    placements.push_back({lv, ctr, copyNo});
                }
            }
        }
    }

    auto* logicESR = new G4LogicalVolume(shell, esrMat, "ESRShell");
    // Reflective ESR surface (real ESR film ~ high reflectivity).
    auto* esrSurf = new G4OpticalSurface("ESRSurface", unified, groundfrontpainted, dielectric_dielectric);
    esrSurf->SetSigmaAlpha(0.1);
    auto* esrProps = new G4MaterialPropertiesTable();
    const int ne = 2;
    G4double eE[ne]  = {2.0 * eV, 4.0 * eV};
    G4double eR[ne]  = {fESRReflectivity, fESRReflectivity};
    esrProps->AddProperty("REFLECTIVITY", eE, eR, ne);
    esrSurf->SetMaterialPropertiesTable(esrProps);
    new G4LogicalSkinSurface("ESRSkin", logicESR, esrSurf);
    new G4PVPlacement(nullptr, G4ThreeVector(), logicESR, "ESRShell", worldLogical, false, 0, true);

    // --- Place active cells ------------------------------------------------
    for (const auto& p : placements) {
        new G4PVPlacement(nullptr, p.pos, p.lv, "SiPMActive", worldLogical, false, p.copyNo, true);
    }

    fLogger->info("Placed {} active-area SiPM volumes around the slab", placements.size());
    return fWorldPhysical;
}

void SingleSlabSiPMTest::BuildSensitiveDetectors()
{
    auto* sdMgr = G4SDManager::GetSDMpointer();

    // SiPM active areas -> slim photon hits (channel/time/wavelength).
    // Both X- and Y-oriented active volumes share the same SD.
    auto* sipmSD = new SingleSlabSiPMSensitiveDetector("SiPMTest/SiPM");
    sdMgr->AddNewDetector(sipmSD);
    if (fLogicActiveX) fLogicActiveX->SetSensitiveDetector(sipmSD);
    if (fLogicActiveY) fLogicActiveY->SetSensitiveDetector(sipmSD);

    // Scintillator -> energy deposition (VoxelTruth) for normalisation
    auto* slabSD = new SLabSensitiveDetector("SiPMTest/Scint");
    sdMgr->AddNewDetector(slabSD);
    if (fLogicScint) fLogicScint->SetSensitiveDetector(slabSD);

    fLogger->info("Sensitive detectors attached (SiPM active areas + scintillator Edep)");
}
