#include "DetectorConstruction/SipmBuilder.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "DetectorConstruction/SensitiveDetectors/SipmSensitiveDetector.hh"
#include "G4SDManager.hh"

#include "G4SystemOfUnits.hh"
#include "G4Box.hh"
#include "G4Element.hh"
#include "G4Material.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"

SipmBuilder::SipmBuilder()
{
}

void SipmBuilder::Build()
{
    BuildSolid();
    auto matSipm = MaterialManager::Instance()->GetMaterial("SiPM");
    fLogicSipm = new G4LogicalVolume(fSolidSipm, matSipm, "SiPM");
    BuildSurface();
    BuildSD();
}

void SipmBuilder::BuildSolid()
{
    const auto &geoSlab = MaterialManager::Instance()->GetSLabGeometry();

    fSolidSipm = new G4Box("SiPM",
                            geoSlab.SiPMxlength / 2,
                            geoSlab.SiPMylength / 2,
                            geoSlab.SiPMzlength / 2);
}

void SipmBuilder::BuildSD()
{
    SipmSensitiveDetector *sdSipm = new SipmSensitiveDetector("SiPM");
    G4SDManager::GetSDMpointer()->AddNewDetector(sdSipm);
    fLogicSipm->SetSensitiveDetector(sdSipm);
}

void SipmBuilder::BuildSurface()
{
    G4OpticalSurface *opSurface = new G4OpticalSurface("SiPM");
    opSurface->SetType(dielectric_metal);
    auto detSipm = MaterialManager::Instance()->GetSipmProperty();
    G4MaterialPropertiesTable *mptSurface = new G4MaterialPropertiesTable();
    // mptSurface->AddProperty("REFLECTIVITY", detSipm.Ephoton, detSipm.Reflection, detSipm.Num);
    mptSurface->AddProperty("EFFICIENCY", detSipm.Ephoton, detSipm.RelativeEfficiency, detSipm.Num);
    opSurface->SetMaterialPropertiesTable(mptSurface);
    new G4LogicalSkinSurface("SiPM",
                            fLogicSipm,
                            opSurface);
}
