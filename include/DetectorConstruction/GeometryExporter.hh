/*
 * GeometryExporter.hh
 *
 * Generic, detector-agnostic geometry exporter.
 *
 * Traverses an arbitrary Geant4 physical-volume tree and records every
 * volume's name, copy number, material, global translation, and solid
 * bounding-box dimensions into a ROOT TTree ("GeometryModel").
 *
 * This is the reusable "Geant4 detector -> 3D model" conversion layer.
 * Unlike the specialized MuonCubeGeometryExporter (which decodes a specific
 * SiPM copy-number scheme), this class makes NO assumptions about the
 * detector layout: it simply walks the whole geometry and dumps everything,
 * so any newly-added detector is exported automatically.
 *
 * Typical use (called once at EndOfRunAction):
 *   GeometryExporter::Export(worldVolume, outputFile, "GeometryModel");
 *
 * The exporter writes into the currently open ROOT gDirectory (owned by
 * OutputManager) and does NOT open/close the file itself.
 *
 * Author: SimuTemplate
 */

#ifndef GEOMETRYEXPORTER_HH
#define GEOMETRYEXPORTER_HH

#include "globals.hh"
#include "G4ThreeVector.hh"
#include "G4VPhysicalVolume.hh"

class GeometryExporter
{
public:
    GeometryExporter() = default;
    ~GeometryExporter() = default;

    /**
     * @brief Export the full geometry tree to a ROOT TTree.
     *
     * @param world          Top physical volume of the geometry.
     * @param rootFilename   Output ROOT file (used only for logging).
     * @param treeName       Name of the TTree to create.
     * @return true on success.
     *
     * One TTree entry corresponds to ONE placed physical volume. Branches:
     *   Name      (std::string)   logical volume name
     *   PhysName  (std::string)   physical volume name
     *   CopyNo    (int)           copy number
     *   Material  (std::string)   material name
     *   X,Y,Z     (double, mm)    global centre position
     *   DX,DY,DZ  (double, mm)    bounding-box full extents along each axis
     *   Depth     (int)           depth in the volume tree (world = 0)
     */
    static G4bool Export(G4VPhysicalVolume* world,
                         const G4String& rootFilename,
                         const G4String& treeName = "GeometryModel");
};

#endif // GEOMETRYEXPORTER_HH
