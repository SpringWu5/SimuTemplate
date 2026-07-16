/*
 * GeometryExporter.cc
 *
 * Implementation of the generic geometry exporter.
 *
 * Author: SimuTemplate
 */

#include "DetectorConstruction/GeometryExporter.hh"

#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4ThreeVector.hh"
#include "G4VSolid.hh"
#include "G4SystemOfUnits.hh"

#include "TTree.h"
#include "TDirectory.h"
#include <spdlog/spdlog.h>

namespace {
// Scalar per-volume buffers (one TTree row == one placed physical volume).
// std::string is used so ROOT stores a TString-backed branch.
std::string gName;
std::string gPhysName;
int         gCopyNo;
std::string gMaterial;
double      gX, gY, gZ;
double      gDX, gDY, gDZ;
int         gDepth;
long        gCount = 0;
} // namespace

void GeometryExporter::Traverse(G4VPhysicalVolume* volume,
                                const G4ThreeVector& motherTranslation,
                                int depth,
                                TTree* tree)
{
    if (!volume || !tree) return;

    // Global centre = mother translation + this placement translation.
    G4ThreeVector globalPos = motherTranslation + volume->GetTranslation();

    G4LogicalVolume* logical = volume->GetLogicalVolume();
    G4Material* material = logical ? logical->GetMaterial() : nullptr;
    G4VSolid* solid = logical ? logical->GetSolid() : nullptr;

    // Bounding-box extents (full length along each axis) in mm.
    G4double dx = 0, dy = 0, dz = 0;
    if (solid) {
        G4ThreeVector pmin, pmax;
        solid->BoundingLimits(pmin, pmax);
        dx = (pmax.x() - pmin.x()) / CLHEP::mm;
        dy = (pmax.y() - pmin.y()) / CLHEP::mm;
        dz = (pmax.z() - pmin.z()) / CLHEP::mm;
    }

    gName     = logical ? std::string(logical->GetName())   : "";
    gPhysName = std::string(volume->GetName());
    gCopyNo   = volume->GetCopyNo();
    gMaterial = material ? std::string(material->GetName()) : "";
    gX = globalPos.x() / CLHEP::mm;
    gY = globalPos.y() / CLHEP::mm;
    gZ = globalPos.z() / CLHEP::mm;
    gDX = dx; gDY = dy; gDZ = dz;
    gDepth = depth;

    tree->Fill();
    ++gCount;

    if (logical) {
        for (size_t i = 0; i < logical->GetNoDaughters(); ++i) {
            Traverse(logical->GetDaughter(i), globalPos, depth + 1, tree);
        }
    }
}

G4bool GeometryExporter::Export(G4VPhysicalVolume* world,
                                const G4String& rootFilename,
                                const G4String& treeName)
{
    spdlog::info("GeometryExporter: exporting full geometry tree to {}", rootFilename);

    if (!gDirectory) {
        spdlog::error("GeometryExporter: no active ROOT gDirectory (file not open)");
        return false;
    }
    if (!world) {
        spdlog::error("GeometryExporter: null world volume");
        return false;
    }

    gCount = 0;

    TTree* tree = new TTree(treeName, "Generic Geant4 geometry model");
    tree->Branch("Name",     &gName);
    tree->Branch("PhysName", &gPhysName);
    tree->Branch("CopyNo",   &gCopyNo);
    tree->Branch("Material", &gMaterial);
    tree->Branch("X",        &gX);
    tree->Branch("Y",        &gY);
    tree->Branch("Z",        &gZ);
    tree->Branch("DX",       &gDX);
    tree->Branch("DY",       &gDY);
    tree->Branch("DZ",       &gDZ);
    tree->Branch("Depth",    &gDepth);

    G4ThreeVector origin(0, 0, 0);
    Traverse(world, origin, 0, tree);

    tree->Write();

    spdlog::info("GeometryExporter: exported {} volumes", gCount);
    return true;
}
