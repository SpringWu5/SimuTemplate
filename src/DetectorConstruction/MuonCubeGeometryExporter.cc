/*
 * MuonCubeGeometryExporter.cc
 *
 * Implementation of MuonCube geometry exporter
 *
 * Created on: 2026-01-21
 * Author: Claude Code
 */

#include "DetectorConstruction/MuonCubeGeometryExporter.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VPVParameterisation.hh"
#include "G4Transform3D.hh"
#include "G4SystemOfUnits.hh"
#include "TFile.h"
#include "TTree.h"
#include "TDirectory.h"
#include "spdlog/spdlog.h"
#include <sstream>

MuonCubeGeometryExporter::MuonCubeGeometryExporter()
{
}

MuonCubeGeometryExporter::~MuonCubeGeometryExporter()
{
}

G4bool MuonCubeGeometryExporter::ExportMap(
    G4VPhysicalVolume* world,
    const G4String& rootFilename,
    const G4String& treeName)
{
    spdlog::info("MuonCubeGeometryExporter: Exporting geometry map to {}", rootFilename);

    // ========================================================================
    // ARCHITECTURAL FIX: Use gDirectory instead of opening file
    // ========================================================================
    // The ROOT file is already opened by OutputManager and is the current gDirectory.
    // We are a GUEST in this file - we do NOT own it, we do NOT close it.
    // OutputManager owns the file and will handle closing it.
    // ========================================================================

    if (!gDirectory) {
        spdlog::error("No active ROOT directory (gDirectory is null)");
        return false;
    }

    // Create geometry map
    GeometryMap* geoMap = new GeometryMap();

    // Create TTree for geometry (goes to current gDirectory, which is OutputManager's file)
    TTree* tree = new TTree(treeName, "MuonCube SiPM Geometry Map");
    geoMap->BookBranches(tree);

    // Traverse geometry starting from world volume
    G4ThreeVector origin(0, 0, 0);
    TraverseGeometry(world, origin, geoMap);

    // Fill the tree
    tree->Fill();

    // Write the tree to the currently open file (managed by OutputManager)
    tree->Write();

    // DO NOT call file->Close() - OutputManager owns the file!
    // DO NOT delete file - OutputManager will clean it up!
    // DO NOT delete tree - ROOT manages tree memory tied to gDirectory

    spdlog::info("MuonCubeGeometryExporter: Exported {} sensor positions to {}",
                 geoMap->GetNSensors(), rootFilename);

    delete geoMap;
    return true;
}

void MuonCubeGeometryExporter::TraverseGeometry(
    G4VPhysicalVolume* volume,
    const G4ThreeVector& motherTranslation,
    GeometryMap* geoMap)
{
    if (!volume || !geoMap) {
        return;
    }

    // Get global translation of this volume
    G4ThreeVector globalTranslation = motherTranslation + volume->GetTranslation();

    // Check if this is an SiPM volume
    G4String volumeName = volume->GetName();
    if (volumeName.contains("SiPM_")) {
        ProcessSiPM(volume, globalTranslation, geoMap);
    }

    // Recursively traverse children
    G4LogicalVolume* logical = volume->GetLogicalVolume();
    if (logical) {
        for (size_t i = 0; i < logical->GetNoDaughters(); ++i) {
            G4VPhysicalVolume* daughter = logical->GetDaughter(i);
            TraverseGeometry(daughter, globalTranslation, geoMap);
        }
    }
}

void MuonCubeGeometryExporter::ProcessSiPM(
    G4VPhysicalVolume* volume,
    const G4ThreeVector& globalPos,
    GeometryMap* geoMap)
{
    G4int copyNo = volume->GetCopyNo();

    // Decode copy number to fiber ID and indices
    G4int fiberID;
    G4String plane;
    G4int row, col, layer;

    if (!DecodeCopyNumber(copyNo, fiberID, plane, row, col, layer)) {
        spdlog::warn("Invalid copy number {} for SiPM {}", copyNo, volume->GetName());
        return;
    }

    // Convert position to mm
    G4double x = globalPos.x() / CLHEP::mm;
    G4double y = globalPos.y() / CLHEP::mm;
    G4double z = globalPos.z() / CLHEP::mm;

    // Add to geometry map
    geoMap->AddSensor(fiberID, copyNo, plane, row, col, layer, x, y, z);

    spdlog::debug("SiPM: Copy={}, ID={}, Plane={}, Pos=({:.2f}, {:.2f}, {:.2f}) mm",
                  copyNo, fiberID, plane, x, y, z);
}

G4bool MuonCubeGeometryExporter::DecodeCopyNumber(
    G4int copyNo,
    G4int& fiberID,
    G4String& plane,
    G4int& row,
    G4int& col,
    G4int& layer)
{
    // ================================================================
    // Phase 3.0: Dual-Ended Readout Encoding (End-Bit Schema)
    // ================================================================
    // Copy number scheme (must match MuonCubeSiPMSensitiveDetector):
    // - Z-SiPMs: 0-127 (8x8 grid at Z+ and Z-)
    //   - 0-63:   Z+ face (positive Z, top) → add 1000 offset
    //   - 64-127: Z- face (negative Z, bottom) → no offset
    // - X-SiPMs: 128-191 (8x4 grid at X+ and X-)
    //   - 128-159: X+ face (positive X, right) → add 1000 offset
    //   - 160-191: X- face (negative X, left) → no offset
    // - Y-SiPMs: 192-255 (8x4 grid at Y+ and Y-)
    //   - 192-223: Y+ face (positive Y, front) → add 1000 offset
    //   - 224-255: Y- face (negative Y, back) → no offset

    if (copyNo < 0 || copyNo > 255) {
        return false;
    }

    if (copyNo < 128) {
        // Z-SiPMs
        plane = "Z";
        G4int localIdx = copyNo % 64;
        row = localIdx / 8;
        col = localIdx % 8;
        layer = -1;  // Z-plane has no layer

        // Phase 3.0: Add +1000 for Z+ (top) end
        G4int endOffset = (copyNo < 64) ? 1000 : 0;
        fiberID = 10000 + endOffset + row * 100 + col;
        // Result: ZM: 10000-10799, ZP: 11000-11799

    } else if (copyNo < 192) {
        // X-SiPMs
        plane = "X";
        G4int localIdx = (copyNo - 128) % 32;
        row = localIdx / 4;
        layer = localIdx % 4;
        col = -1;  // X-plane doesn't use col

        // Phase 3.0: Add +1000 for X+ (right) end
        G4int endOffset = (copyNo < 160) ? 1000 : 0;
        fiberID = 20000 + endOffset + layer * 100 + row;
        // Result: XM: 20000-20399, XP: 21000-21399

    } else {
        // Y-SiPMs
        plane = "Y";
        G4int localIdx = (copyNo - 192) % 32;
        col = localIdx / 4;
        layer = localIdx % 4;
        row = -1;  // Y-plane doesn't use row

        // Phase 3.0: Add +1000 for Y+ (front) end
        G4int endOffset = (copyNo < 224) ? 1000 : 0;
        fiberID = 30000 + endOffset + layer * 100 + col;
        // Result: YM: 30000-30399, YP: 31000-31399
    }

    return true;
}
