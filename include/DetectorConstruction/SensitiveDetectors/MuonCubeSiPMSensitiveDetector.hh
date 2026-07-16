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
    /**
     * @brief Map hit position to fiber ID
     *
     * @param planeName Which SiPM plane ("X+", "X-", "Y+", "Y-", "Z+", "Z-")
     * @param x Hit x position (mm)
     * @param y Hit y position (mm)
     * @param z Hit z position (mm)
     * @return Fiber ID (encoded as appropriate for the plane)
     */
    G4int MapPositionToFiberID(const G4String& planeName,
                               G4double x, G4double y, G4double z);

    /**
     * @brief Map copy number to fiber ID
     *
     * Decodes the physical volume copy number to determine which SiPM
     * was hit and returns the corresponding fiber ID.
     *
     * Copy number scheme (from MuonCubeConstruction):
     * - Z-SiPMs: 0-127 (8x8 grid at Z+ and Z-)
     * - X-SiPMs: 128-191 (8x4 grid at X+ and X-)
     * - Y-SiPMs: 192-255 (8x4 grid at Y+ and Y-)
     *
     * @param copyNo The copy number from GetCopyNumber()
     * @return Fiber ID (10000+ for Z, 20000+ for X, 30000+ for Y)
     */
    G4int MapCopyNumberToFiberID(G4int copyNo);

    G4int fTotalOpticalHits;      // Total optical photons detected
    G4int fTotalWLPHits;          // WLS photons detected
};

#endif // MUONCUBE_SIPM_SENSITIVE_DETECTOR_HH
