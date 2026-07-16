#include "DetectorConstruction/SensitiveDetectors/SLabSensitiveDetector.hh"
#include "Record/Hits.hh"
#include "Record/VoxelTruthHit.hh"
#include "Record/OutputManager.hh"

#include "G4Material.hh"
#include "G4ParticleDefinition.hh"
#include "G4SDManager.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4OpticalPhoton.hh"
#include "G4TouchableHistory.hh"
#include "G4VTouchable.hh"
#include "g4root.hh"
#include "G4VProcess.hh"  // Added this header for G4VProcess
#include "G4MuonPlus.hh"
#include "G4MuonMinus.hh"

#include "spdlog/spdlog.h"
#include "Util/Logger.hh"

SLabSensitiveDetector::SLabSensitiveDetector(G4String name)
    : G4VSensitiveDetector(name) {}

SLabSensitiveDetector::~SLabSensitiveDetector() {}

G4bool SLabSensitiveDetector::ProcessHits(G4Step *step, G4TouchableHistory *)
{
    auto *track = step->GetTrack();
    auto preStepPoint = step->GetPreStepPoint();
    auto postStepPoint = step->GetPostStepPoint();
    auto touchable =
        static_cast<const G4TouchableHistory *>(preStepPoint->GetTouchable());

    // ============================================================
    // PHYSICS FIX 1: Optical Photon Filter (Immediate return)
    // ============================================================
    // Optical photons don't deposit energy in scintillator
    // They are absorbed/converted in WLS fibers or detected at SiPMs
    if (track->GetDefinition() == G4OpticalPhoton::OpticalPhotonDefinition()) {
        return false;
    }

    // ============================================================
    // PHYSICS FIX 2: Robust Voxel ID Resolution
    // ============================================================
    // The unique VoxelID (0-255) is stored in the parent VoxelWrapper volume,
    // NOT in the scintillator volume itself. We must traverse the touchable
    // history to find the VoxelWrapper and extract its CopyNumber.
    G4int voxelID = -1;

    for (G4int depth = 0; depth < touchable->GetHistoryDepth(); depth++) {
        G4String volName = touchable->GetVolume(depth)->GetName();
        if (volName.contains("VoxelWrapper")) {
            voxelID = touchable->GetCopyNumber(depth);
            break;
        }
    }

    // Safety check: if we couldn't find VoxelWrapper, try alternative methods
    if (voxelID < 0) {
        // Fallback: try the immediate parent (depth 1)
        if (touchable->GetHistoryDepth() > 1) {
            voxelID = touchable->GetCopyNumber(1);
        } else {
            // Last resort: use depth 0
            voxelID = touchable->GetCopyNumber(0);
        }
    }

    // Get voxel truth collection
    VoxelTruthHit* voxelTruth = OutputManager::Instance()->GetVoxelTruth();

    // ============================================================
    // PHYSICS FIX 3: Decouple Energy Deposition from Kinematics
    // ============================================================
    // Energy Deposition (ALL particles including secondaries/delta-rays)
    // This is critical for calorimetry - we want TOTAL energy deposited
    G4double edep = step->GetTotalEnergyDeposit();  // MeV

    // Add energy deposition for ALL particles (no trackID filter)
    // This captures delta-ray energy, Bremsstrahlung, etc.
    if (edep > 0.0) {
        voxelTruth->AddEnergy(voxelID, edep);
    }

    // Track ID and Primary Particle Check
    G4int trackID = track->GetTrackID();
    const G4bool isPrimary = (trackID == 1);

    // ============================================================
    // PRIMARY KINEMATICS ONLY (TrackID == 1)
    // ============================================================
    // Entry/Exit positions, times, and track length are ONLY meaningful
    // for the primary particle. Secondaries don't have "trajectory" in the
    // same sense - they originate and stop within voxels.
    if (isPrimary) {
        // Get current track length BEFORE adding this step (to detect first step)
        G4double currentTrackLen = voxelTruth->GetTrackLen(voxelID);
        G4double stepLen = step->GetStepLength();  // mm

        // Get entry state (PreStepPoint)
        G4ThreeVector entryPos = preStepPoint->GetPosition();
        G4double entryTime = preStepPoint->GetGlobalTime() / ns;
        G4double entryE = preStepPoint->GetKineticEnergy() / MeV;

        // Get exit state (PostStepPoint)
        G4ThreeVector exitPos = postStepPoint->GetPosition();
        G4double exitTime = postStepPoint->GetGlobalTime() / ns;
        G4double exitE = postStepPoint->GetKineticEnergy() / MeV;

        // Initialize voxel entry state on FIRST step (tracklen == 0)
        // This must happen BEFORE UpdateVoxel adds the step length
        if (currentTrackLen == 0.0) {
            voxelTruth->InitializeVoxel(
                voxelID,
                entryPos.x() / mm, entryPos.y() / mm, entryPos.z() / mm,
                entryTime,
                entryE
            );
        }

        // Always update exit state (last step's PostStepPoint will remain)
        voxelTruth->UpdateVoxel(
            voxelID,
            stepLen,
            exitPos.x() / mm, exitPos.y() / mm, exitPos.z() / mm,
            exitTime,
            exitE
        );
    }

    // ============================================================
    // LEGACY: Keep original hit recording for backward compatibility
    // ============================================================
    Hits* hits = OutputManager::Instance()->GetSLabHits();

    // Keep primary muon steps even if Edep=0, but ignore secondaries with no Edep
    if (edep == 0. && !isPrimary) return false;

    auto hitType = HitType::Muon;
    G4ThreeVector momentum = postStepPoint->GetMomentum();
    G4ThreeVector pos = postStepPoint->GetPosition();
    Float_t hitTime = postStepPoint->GetGlobalTime() / ns;

    // Get step length - ONLY for primary muon (TrackID == 1)
    G4double stepLen = 0.0;
    if (isPrimary) {
        stepLen = step->GetStepLength();
    }

    // Add hit to legacy collection
    hits->AddHit(
        hitType,
        trackID,
        voxelID,
        edep,
        momentum.x(), momentum.y(), momentum.z(),
        pos.x(), pos.y(), pos.z(),
        hitTime,
        stepLen
    );

    return true;
}

void SLabSensitiveDetector::DumpInfo(G4Step *step,
                                    G4TouchableHistory *touchable)
{
    // code for understanding the return value of Geant4 function
    G4cout << "*******************************" << G4endl;
    G4cout << "             Slab HIT           " << G4endl;
    G4cout << "  touchable->GetVolume(0)->GetCopyNo(): "
            << touchable->GetVolume(0)->GetCopyNo() << G4endl;
    G4cout << "  touchable->GetVolume(0)->GetTranslation(): "
            << touchable->GetVolume(0)->GetTranslation().x() / CLHEP::mm << " "
            << touchable->GetVolume(0)->GetTranslation().y() / CLHEP::mm << " "
            << touchable->GetVolume(0)->GetTranslation().z() / CLHEP::mm << G4endl;
    G4cout << "  step->GetTrack()->GetKineticEnergy() (eV) : "
            << step->GetTrack()->GetKineticEnergy() / CLHEP::eV << G4endl;
    G4ThreeVector VecSlabToMuon = step->GetPreStepPoint()->GetPosition() -
                                    touchable->GetVolume(0)->GetTranslation();
    G4cout << "  VecSlabToMuon (mm) : " << VecSlabToMuon.x() / CLHEP::mm << " "
            << VecSlabToMuon.y() / CLHEP::mm << " "
            << VecSlabToMuon.z() / CLHEP::mm << G4endl;
    G4cout << "  step->GetPreStepPoint()->GetMomentumDirection(): "
            << step->GetPreStepPoint()->GetMomentumDirection().x() << " "
            << step->GetPreStepPoint()->GetMomentumDirection().y() << " "
            << step->GetPreStepPoint()->GetMomentumDirection().z() << G4endl;
    G4cout << "  step->GetPreStepPoint()->GetGlobalTime() (ns): "
            << step->GetPreStepPoint()->GetGlobalTime() / CLHEP::ns << G4endl;
    G4cout << "  step->GetTrack()->GetStepLength() (mm): "
            << step->GetTrack()->GetStepLength() / CLHEP::mm << G4endl;
    G4cout << "*******************************" << G4endl << G4endl;
}
