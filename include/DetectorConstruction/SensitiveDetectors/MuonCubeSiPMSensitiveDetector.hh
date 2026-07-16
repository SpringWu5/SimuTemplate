/*
 * MuonCubeSiPMSensitiveDetector.hh
 *
 * Specialized sensitive detector for MuonCube SiPM planes
 * Detects optical photons and maps them to fiber IDs
 *
 * Phase 3.0: Ideal optical physics - records 100% of arriving photons
 *
 * Created on: 2024
 * Author: Claude Code
 */

#ifndef MUONCUBE_SIPM_SENSITIVE_DETECTOR_HH
#define MUONCUBE_SIPM_SENSITIVE_DETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "G4HCofThisEvent.hh"
#include "globals.hh"
#include <map>
#include <string>
#include <vector>

class G4Step;
class G4TouchableHistory;

/**
 * @brief Sensitive detector for MuonCube SiPM planes
 *
 * Detects optical photons exiting the WLS fibers and records:
 * - Hit position (x, y, z)
 * - Photon energy/wavelength
 * - Global time
 * - Fiber ID mapping (based on position)
 */
class MuonCubeSiPMSensitiveDetector : public G4VSensitiveDetector
{
public:
    MuonCubeSiPMSensitiveDetector(const G4String& name);
    virtual ~MuonCubeSiPMSensitiveDetector();

    virtual void Initialize(G4HCofThisEvent*) override;
    virtual G4bool ProcessHits(G4Step* step, G4TouchableHistory*) override;
    virtual void EndOfEvent(G4HCofThisEvent*) override;

private:
    G4int fTotalOpticalHits;      // Total optical photons detected
    G4int fTotalWLPHits;          // WLS photons detected
};

#endif // MUONCUBE_SIPM_SENSITIVE_DETECTOR_HH
