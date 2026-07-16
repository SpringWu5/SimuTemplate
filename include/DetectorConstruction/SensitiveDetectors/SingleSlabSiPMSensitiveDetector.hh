#ifndef SINGLESLABSIPM_SENSITIVE_DETECTOR_HH
#define SINGLESLABSIPM_SENSITIVE_DETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "globals.hh"

class G4HCofThisEvent;
class G4Step;
class G4TouchableHistory;

/**
 * @brief Sensitive detector for the single-slab SiPM-sizing experiment.
 *
 * Records every optical photon that enters a SiPM *active-area* volume as a
 * slim hit (channel ID, arrival time, wavelength) into OutputManager's SiPMHit
 * collection. No PDE is applied here -- detection is ideal (100%); photon
 * detection efficiency is folded in offline. The photon is killed on hit.
 *
 * The channel ID is the copy number of the active-area physical volume, set by
 * SingleSlabSiPMTest as  edge*1000 + pos*100 + cell  (cell=0 for single SiPMs,
 * 0..3 for the 2x2 array).
 */
class SingleSlabSiPMSensitiveDetector : public G4VSensitiveDetector
{
public:
    explicit SingleSlabSiPMSensitiveDetector(const G4String& name);
    virtual ~SingleSlabSiPMSensitiveDetector();

    virtual void Initialize(G4HCofThisEvent*);
    virtual G4bool ProcessHits(G4Step* step, G4TouchableHistory*);
    virtual void EndOfEvent(G4HCofThisEvent*);

private:
    G4int fTotalHits;
};

#endif // SINGLESLABSIPM_SENSITIVE_DETECTOR_HH
