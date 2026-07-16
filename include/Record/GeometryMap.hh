/*
 * GeometryMap.hh
 *
 * Ground truth geometry map for MuonCube SiPM positions
 * Stores the actual physical positions of all SiPM sensors as placed by Geant4
 *
 * Created on: 2026-01-21
 * Author: Claude Code
 */

#ifndef GEOMETRYMAP_HH
#define GEOMETRYMAP_HH

#include "TTree.h"
#include <vector>
#include <string>

class GeometryMap
{
public:
    GeometryMap() : fIsFilled(false) {};
    ~GeometryMap() {};

    void BookBranches(TTree* tree) {
        tree->Branch("FiberID", &fFiberID);
        tree->Branch("CopyNo", &fCopyNo);
        tree->Branch("Plane", &fPlane);
        tree->Branch("Row", &fRow);
        tree->Branch("Col", &fCol);
        tree->Branch("Layer", &fLayer);
        tree->Branch("X", &fX);
        tree->Branch("Y", &fY);
        tree->Branch("Z", &fZ);
    }

    void Reset() {
        fFiberID.clear();
        fCopyNo.clear();
        fPlane.clear();
        fRow.clear();
        fCol.clear();
        fLayer.clear();
        fX.clear();
        fY.clear();
        fZ.clear();
        fIsFilled = false;
    }

    void AddSensor(
            int fiberID, int copyNo, const std::string& plane,
            int row, int col, int layer,
            double x, double y, double z
        ) {
        fFiberID.push_back(fiberID);
        fCopyNo.push_back(copyNo);
        fPlane.push_back(plane);
        fRow.push_back(row);
        fCol.push_back(col);
        fLayer.push_back(layer);
        fX.push_back(x);
        fY.push_back(y);
        fZ.push_back(z);
        fIsFilled = true;
    }

    bool IsFilled() const { return fIsFilled; }

    size_t GetNSensors() const { return fFiberID.size(); }

private:
    bool fIsFilled;

    std::vector<int> fFiberID;      // Encoded fiber ID
    std::vector<int> fCopyNo;       // Geant4 copy number
    std::vector<std::string> fPlane; // Plane type: "Z", "X", "Y"
    std::vector<int> fRow;          // Row index (0-7)
    std::vector<int> fCol;          // Column index (0-7)
    std::vector<int> fLayer;        // Layer index (0-3, -1 for Z-plane)
    std::vector<double> fX;         // Physical X position (mm)
    std::vector<double> fY;         // Physical Y position (mm)
    std::vector<double> fZ;         // Physical Z position (mm)
};

#endif
