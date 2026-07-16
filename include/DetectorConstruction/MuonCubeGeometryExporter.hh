/*
 * MuonCubeGeometryExporter.hh
 *
 * Exports ground truth geometry map of MuonCube SiPM positions
 * Iterates through the Geant4 geometry tree and records actual sensor positions
 *
 * Created on: 2026-01-21
 * Author: Claude Code
 */

#ifndef MUONCUBEGEOMETRYEXPORTER_HH
#define MUONCUBEGEOMETRYEXPORTER_HH

#include "globals.hh"
#include "G4VPhysicalVolume.hh"
#include "G4LogicalVolume.hh"
#include "Record/GeometryMap.hh"
#include <string>

class MuonCubeGeometryExporter
{
public:
    MuonCubeGeometryExporter();
    virtual ~MuonCubeGeometryExporter();

    // Export geometry map to ROOT file
    static G4bool ExportMap(
        G4VPhysicalVolume* world,
        const G4String& rootFilename,
        const G4String& treeName = "GeometryMap"
    );

private:
    // Recursive function to traverse geometry tree
    static void TraverseGeometry(
        G4VPhysicalVolume* volume,
        const G4ThreeVector& motherTranslation,
        GeometryMap* geoMap
    );

    // Process a single SiPM volume
    static void ProcessSiPM(
        G4VPhysicalVolume* volume,
        const G4ThreeVector& globalPos,
        GeometryMap* geoMap
    );

    // Decode copy number to fiber ID and indices
    static G4bool DecodeCopyNumber(
        G4int copyNo,
        G4int& fiberID,
        G4String& plane,
        G4int& row,
        G4int& col,
        G4int& layer
    );
};

#endif
