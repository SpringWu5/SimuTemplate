#include "DetectorConstruction/StackedDetector.hh"
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
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

#include "yaml-cpp/yaml.h"
#include <vector>

StackedDetector::StackedDetector(const char* config_path)
    : DetectorConstructionBase(config_path)
{
    fLogger = create_logger("StackedDetector");
    LoadParameters();
}

void StackedDetector::LoadParameters()
{
    try {
        auto cfg = MaterialManager::Instance()->getRootNode();
        if (cfg["Stacked"]) {
            auto n = cfg["Stacked"];
            if (n["layer_sep"])        fLsep        = n["layer_sep"].as<double>();
            if (n["same_layer_gap"])   fGap         = n["same_layer_gap"].as<double>();
            if (n["slab_hx"])          fSlabHx      = n["slab_hx"].as<double>();
            if (n["slab_hy"])          fSlabHy      = n["slab_hy"].as<double>();
            if (n["slab_hz"])          fSlabHz      = n["slab_hz"].as<double>();
            if (n["block_hx"])         fBlkHx       = n["block_hx"].as<double>();
            if (n["block_hy"])         fBlkHy       = n["block_hy"].as<double>();
            if (n["block_hz"])         fBlkHz       = n["block_hz"].as<double>();
            if (n["sipm_active"])      fSipmActive  = n["sipm_active"].as<double>();   // mm
            if (n["esr_thick"])        fESRThick    = n["esr_thick"].as<double>();     // cm
            if (n["esr_reflectivity"]) fRefl        = n["esr_reflectivity"].as<double>();
            if (n["esr_sigma_alpha_deg"]) fSigmaAlphaDeg = n["esr_sigma_alpha_deg"].as<double>();
            if (n["esr_finish"])          fFinish      = n["esr_finish"].as<std::string>();
        }
    } catch (const YAML::Exception& e) {
        fLogger->warn("Failed to read Stacked config ({}); using defaults", e.what());
    }
    fLogger->info("StackedDetector: Lsep={:.1f} gap={:.1f} cm; slab {:.0f}x{:.0f}x{:.0f} cm; "
                  "block {:.0f}x{:.0f}x{:.0f} cm; SiPM {:.1f}mm; ESR R={:.2f} sigma_alpha={:.1f}deg",
                  fLsep, fGap, 2*fSlabHx, 2*fSlabHy, 2*fSlabHz, 2*fBlkHx, 2*fBlkHy, 2*fBlkHz,
                  fSipmActive, fRefl, fSigmaAlphaDeg);
}

G4OpticalSurface* StackedDetector::MakeESRSurface(const G4String& name)
{
    G4OpticalSurfaceFinish fin = groundfrontpainted;
    if (fFinish == "polished")        fin = polished;
    else if (fFinish == "ground")     fin = ground;
    else if (fFinish == "groundfrontpainted") fin = groundfrontpainted;
    auto* s = new G4OpticalSurface(name, unified, fin, dielectric_dielectric);
    s->SetSigmaAlpha(fSigmaAlphaDeg * deg);
    auto* mpt = new G4MaterialPropertiesTable();
    const int ne = 2;
    G4double eE[ne] = {2.0 * eV, 4.0 * eV};
    G4double eR[ne] = {fRefl, fRefl};
    mpt->AddProperty("REFLECTIVITY", eE, eR, ne);
    s->SetMaterialPropertiesTable(mpt);
    return s;
}

G4VPhysicalVolume* StackedDetector::ConstructDetector(G4LogicalVolume* worldLogical)
{
    fWorldLogical = worldLogical;
    auto M = MaterialManager::Instance();
    G4Material* scint = M->GetMaterial("Scint");
    G4Material* esr   = M->GetMaterial("ESR");
    G4Material* sipm  = M->GetMaterial("SiPM");

    // ---- all dimensions converted to Geant4 internal units (mm) here ----
    const G4double hx = fSlabHx * cm, hy = fSlabHy * cm, hz = fSlabHz * cm;
    const G4double bx = fBlkHx * cm, by = fBlkHy * cm, bz = fBlkHz * cm;
    const G4double e  = fESRThick * cm;
    const G4double halfActive = (fSipmActive / 2.0) * mm;
    const G4double halfThick  = 0.25 * mm;
    const G4double margin     = 0.02 * mm;
    const G4double halfFoot   = halfActive + margin;
    const G4double halfDepth  = e / 2.0 + margin;
    const G4double off = 5.0 * cm;

    // -------------------- central slab + 8 SiPMs --------------------------
    fLogicSlab = new G4LogicalVolume(new G4Box("Slab", hx, hy, hz), scint, "Slab");
    new G4PVPlacement(nullptr, G4ThreeVector(), fLogicSlab, "Slab", worldLogical, false, 10, true);
    new G4LogicalSkinSurface("SlabSkin", fLogicSlab,
        new G4OpticalSurface("SlabSurface", glisur, polished, dielectric_dielectric));

    fLogicActiveX = new G4LogicalVolume(new G4Box("SipmX", halfThick, halfActive, halfActive), sipm, "Sipm");
    fLogicActiveY = new G4LogicalVolume(new G4Box("SipmY", halfActive, halfThick, halfActive), sipm, "Sipm");

    G4VSolid* shell = new G4SubtractionSolid("SlabESR",
        new G4Box("o", hx + e, hy + e, hz + e), new G4Box("i", hx, hy, hz));
    struct Pl { G4LogicalVolume* lv; G4ThreeVector p; int c; };
    std::vector<Pl> pls;
    for (int edge = 0; edge < 4; ++edge) {
        bool xf = edge < 2; G4double sg = (edge % 2 == 0) ? +1 : -1;
        for (int pos = 0; pos < 2; ++pos) {
            G4double along = (pos == 0 ? +off : -off);
            int copy = edge * 1000 + pos * 100;
            G4LogicalVolume* lv = xf ? fLogicActiveX : fLogicActiveY;
            G4ThreeVector ctr; G4VSolid* win = nullptr;
            if (xf) {
                G4double py = along;
                ctr = G4ThreeVector(sg * (hx + halfThick), py, 0);
                win = new G4Box("w", halfDepth, halfFoot, halfFoot);
                shell = new G4SubtractionSolid("SlabESR", shell, win, nullptr,
                                               G4ThreeVector(sg * (hx + e / 2), py, 0));
            } else {
                G4double px = along;
                ctr = G4ThreeVector(px, sg * (hy + halfThick), 0);
                win = new G4Box("w", halfFoot, halfDepth, halfFoot);
                shell = new G4SubtractionSolid("SlabESR", shell, win, nullptr,
                                               G4ThreeVector(px, sg * (hy + e / 2), 0));
            }
            pls.push_back({lv, ctr, copy});
        }
    }
    auto* logicESR = new G4LogicalVolume(shell, esr, "SlabESR");
    new G4LogicalSkinSurface("SlabESRSkin", logicESR, MakeESRSurface("SlabESRSurf"));
    new G4PVPlacement(nullptr, G4ThreeVector(), logicESR, "SlabESR", worldLogical, false, 0, true);
    for (const auto& p : pls)
        new G4PVPlacement(nullptr, p.p, p.lv, "Sipm", worldLogical, false, p.c, true);

    // -------------------- 4 small scints (ESR-wrapped) -------------------
    const G4double xR = (fGap / 2.0 + fBlkHx) * cm;     // cm -> mm
    G4double cxmm[4] = {+xR, -xR, +xR, -xR};
    G4double czmm[4] = {+fLsep / 2.0 * cm, +fLsep / 2.0 * cm, -fLsep / 2.0 * cm, -fLsep / 2.0 * cm};
    int scopy[4] = {20, 21, 22, 23};
    for (int i = 0; i < 4; ++i) {
        G4String nm = "Small" + std::to_string(i);
        fLogicSmall[i] = new G4LogicalVolume(new G4Box(nm, bx, by, bz), scint, nm);
        new G4PVPlacement(nullptr, G4ThreeVector(cxmm[i], 0, czmm[i]), fLogicSmall[i], nm,
                          worldLogical, false, scopy[i], true);
        new G4LogicalSkinSurface(nm + "SS", fLogicSmall[i],
            new G4OpticalSurface(nm + "s", glisur, polished, dielectric_dielectric));
        auto* sshell = new G4SubtractionSolid(nm + "ESR",
            new G4Box(nm + "o", bx + e, by + e, bz + e), new G4Box(nm + "i", bx, by, bz));
        auto* lshell = new G4LogicalVolume(sshell, esr, nm + "ESR");
        new G4LogicalSkinSurface(nm + "ESRSkin", lshell, MakeESRSurface(nm + "ESRSurf"));
        new G4PVPlacement(nullptr, G4ThreeVector(cxmm[i], 0, czmm[i]), lshell, nm + "ESR",
                          worldLogical, false, 0, true);
    }

    fLogger->info("StackedDetector built: slab + 8 SiPMs + 4 small scints.");
    return fWorldPhysical;
}

void StackedDetector::BuildSensitiveDetectors()
{
    auto* sd = G4SDManager::GetSDMpointer();
    auto* sipmSD = new SingleSlabSiPMSensitiveDetector("Stacked/SiPM");
    sd->AddNewDetector(sipmSD);
    if (fLogicActiveX) fLogicActiveX->SetSensitiveDetector(sipmSD);
    if (fLogicActiveY) fLogicActiveY->SetSensitiveDetector(sipmSD);
    auto* eSD = new SLabSensitiveDetector("Stacked/Scint");
    sd->AddNewDetector(eSD);
    if (fLogicSlab) fLogicSlab->SetSensitiveDetector(eSD);
    for (int i = 0; i < 4; ++i)
        if (fLogicSmall[i]) fLogicSmall[i]->SetSensitiveDetector(eSD);
    fLogger->info("SDs attached: 8 slab SiPMs + slab/4-small Edep.");
}
