#include "DetectorConstruction/SensitiveDetectors/SingleSlabSiPMSensitiveDetector.hh"
#include "Record/OutputManager.hh"
#include "Record/SiPMHit.hh"

#include "G4Step.hh"
#include "G4TouchableHistory.hh"
#include "G4Track.hh"
#include "G4VTouchable.hh"
#include "G4OpticalPhoton.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "spdlog/spdlog.h"

SingleSlabSiPMSensitiveDetector::SingleSlabSiPMSensitiveDetector(const G4String& name)
    : G4VSensitiveDetector(name), fTotalHits(0)
{
    collectionName.insert("SingleSlabSiPMHitsCollection");
}

SingleSlabSiPMSensitiveDetector::~SingleSlabSiPMSensitiveDetector() {}

void SingleSlabSiPMSensitiveDetector::Initialize(G4HCofThisEvent*) { fTotalHits = 0; }

G4bool SingleSlabSiPMSensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*)
{
    // Only optical photons are detected by the SiPM active area.
    G4Track* track = step->GetTrack();
    if (track->GetDefinition() != G4OpticalPhoton::OpticalPhotonDefinition()) {
        return false;
    }

    // Channel ID == copy number of the active-area placement.
    auto touchable = step->GetPreStepPoint()->GetTouchableHandle();
    G4int channel = -1;
    if (touchable && touchable->GetVolume()) {
        channel = touchable->GetVolume()->GetCopyNo();
    }

    G4StepPoint* post = step->GetPostStepPoint();
    G4double hitTime = post->GetGlobalTime() / ns;
    G4double energy = post->GetKineticEnergy();
    G4double wavelength = (energy > 0.0) ? (1240.0 / (energy / eV)) : 0.0;  // nm

    OutputManager::Instance()->GetSiPMHits()->AddHit(channel, hitTime, wavelength);
    ++fTotalHits;

    // Kill the photon once it has been recorded.
    track->SetTrackStatus(fStopAndKill);
    return true;
}

void SingleSlabSiPMSensitiveDetector::EndOfEvent(G4HCofThisEvent*)
{
    if (fTotalHits > 0) {
        spdlog::debug("SingleSlab SiPM: {} photons recorded this event", fTotalHits);
    }
}
