/*
 * SiPMHit.hh
 *
 * ML-Optimized SiPM Hit Collection (Phase 3.0)
 * Extreme Slimming: Only essential data for optical photons
 *
 * Created on: 2025
 * Author: Claude Code
 */

#ifndef SIPMHIT_HH
#define SIPMHIT_HH

#include "TTree.h"
#include "vector"
#include "TString.h"

using std::vector;

/**
 * @brief Slim SiPM hit collection for ML pipeline
 *
 * Stores ONLY the essential optical photon data:
 * - Detector ID (for geometry mapping)
 * - Hit time (for TOF reconstruction)
 * - Wavelength (for spectral analysis & PDE application)
 *
 * All spatial/kinematic data removed - will be deduced from GeometryMap in Python
 */
class SiPMHit
{
public:
    SiPMHit() {};
    ~SiPMHit() {};

    void BookBranches(TTree* tree, TString prefix="") {
        tree->Branch(prefix + "Hit_Det_ID", &fDetID);
        tree->Branch(prefix + "Hit_Time", &fTime);
        tree->Branch(prefix + "Hit_Wavelength", &fWavelength);
    }

    void Reset() {
        fDetID.clear();
        fTime.clear();
        fWavelength.clear();
    }

    void AddHit(int detID, double time, double wavelength) {
        fDetID.push_back(detID);
        fTime.push_back(time);
        fWavelength.push_back(wavelength);
    }

    // Getters
    vector<int> GetDetID() const { return fDetID; }
    vector<double> GetTime() const { return fTime; }
    vector<double> GetWavelength() const { return fWavelength; }

private:
    vector<int> fDetID;          // Fiber/Channel ID (with end-bit encoding)
    vector<double> fTime;        // Hit time (ns)
    vector<double> fWavelength;  // Wavelength (nm)
};

#endif // SIPMHIT_HH
