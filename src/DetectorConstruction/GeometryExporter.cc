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
// Per-export row buffers (one TTree row == one placed physical volume).
// std::string is used so ROOT stores a TString-backed branch.
// All buffers are local to each Export() call -> no shared/global state, so
// the exporter is safe to use from a single thread per run (and trivially
// re-entrant across runs).
struct ExportBuffers {
    std::string name;
    std::string physName;
    std::string material;
    int copyNo = 0;
    double x = 0, y = 0, z = 0;
    double dx = 0, dy = 0, dz = 0;
    int depth = 0;
    long count = 0;
};

// Recursive traversal accumulating global translation; fills one TTree row
// per placed physical volume.
void Traverse(G4VPhysicalVolume* volume,
              const G4ThreeVector& motherTranslation,
              int depth,
              TTree* tree,
              ExportBuffers& b)
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

    b.name     = logical ? std::string(logical->GetName())   : "";
    b.physName = std::string(volume->GetName());
    b.copyNo   = volume->GetCopyNo();
    b.material = material ? std::string(material->GetName()) : "";
    b.x = globalPos.x() / CLHEP::mm;
    b.y = globalPos.y() / CLHEP::mm;
    b.z = globalPos.z() / CLHEP::mm;
    b.dx = dx; b.dy = dy; b.dz = dz;
    b.depth = depth;

    tree->Fill();
    ++b.count;

    if (logical) {
        for (size_t i = 0; i < logical->GetNoDaughters(); ++i) {
            Traverse(logical->GetDaughter(i), globalPos, depth + 1, tree, b);
        }
    }
}
} // namespace

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

    ExportBuffers b;

    TTree* tree = new TTree(treeName, "Generic Geant4 geometry model");
    tree->Branch("Name",     &b.name);
    tree->Branch("PhysName", &b.physName);
    tree->Branch("CopyNo",   &b.copyNo);
    tree->Branch("Material", &b.material);
    tree->Branch("X",        &b.x);
    tree->Branch("Y",        &b.y);
    tree->Branch("Z",        &b.z);
    tree->Branch("DX",       &b.dx);
    tree->Branch("DY",       &b.dy);
    tree->Branch("DZ",       &b.dz);
    tree->Branch("Depth",    &b.depth);

    G4ThreeVector origin(0, 0, 0);
    Traverse(world, origin, 0, tree, b);

    tree->Write();

    spdlog::info("GeometryExporter: exported {} volumes", b.count);
    return true;
}
