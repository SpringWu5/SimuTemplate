#include "G4Event.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "g4root.hh"
#include "G4RunManager.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4PrimaryParticle.hh"
#include "G4PrimaryVertex.hh"

#include "Action/EventAction.hh"
#include "Action/SteppingAction.hh"
#include "Util/Logger.hh"

EventAction::EventAction() : fEventID(-1) {}

EventAction::~EventAction() {}

void EventAction::BeginOfEventAction(const G4Event *event) {
    // Update event ID
    fEventID = event->GetEventID();

    // Log event start
    LogUtils::log_info("Starting Event ID: " + std::to_string(fEventID));

    // Reset all statistics for the new event
    LogUtils::reset_slab_statistics();
    LogUtils::reset_detection_statistics();
    LogUtils::reset_unique_statistics();

    // ============================================================
    // Task 2: Capture Global Truth for ML
    // ============================================================
    if (event->GetNumberOfPrimaryVertex() > 0) {
        G4PrimaryVertex* vertex = event->GetPrimaryVertex();
        if (vertex && vertex->GetNumberOfParticle() > 0) {
            G4PrimaryParticle* primary = vertex->GetPrimary();
            if (primary && primary->GetG4code()) {
                // Get particle info
                G4String particleName = primary->GetG4code()->GetParticleName();
                G4double energy = primary->GetKineticEnergy() / CLHEP::MeV;

                // Log minimal primary particle info
                std::stringstream primaryInfo;
                primaryInfo << "Primary particle: " << particleName
                           << " with energy " << energy << " MeV";
                LogUtils::log_info(primaryInfo.str());

                // ============================================================
                // STORE GLOBAL TRUTH TO ROOT (Task 2)
                // ============================================================
                auto outputMgr = OutputManager::Instance();

                // PDG ID
                outputMgr->SetPrimaryPDG(primary->GetG4code()->GetPDGEncoding());

                // Initial kinetic energy (MeV)
                outputMgr->SetPrimaryEnergy(energy);

                // Initial vertex position (mm)
                outputMgr->SetPrimaryPosition(
                    vertex->GetX0() / CLHEP::mm,
                    vertex->GetY0() / CLHEP::mm,
                    vertex->GetZ0() / CLHEP::mm
                );

                // Initial momentum (MeV/c)
                outputMgr->SetPrimaryMomentum(
                    primary->GetPx() / CLHEP::MeV,
                    primary->GetPy() / CLHEP::MeV,
                    primary->GetPz() / CLHEP::MeV
                );

                // Initial time (ns)
                outputMgr->SetPrimaryTime(vertex->GetT0() / CLHEP::ns);
            }
        }
    }

    OutputManager::Instance()->SetEventID(fEventID);
}

void EventAction::EndOfEventAction(const G4Event* event)
{
    // Log completion
    LogUtils::log_info("End of event " + std::to_string(event->GetEventID()));
    
    // First log unique particle statistics
    LogUtils::log_unique_statistics(event->GetEventID());
    
    // Then log hit statistics 
    LogUtils::log_detection_statistics(event->GetEventID());
    
    // For the last event, add detailed particle summary
    if (event->GetEventID() == G4RunManager::GetRunManager()->GetNumberOfEventsToBeProcessed() - 1) {
        LogUtils::log_detailed_particle_summary();
    }
    
    OutputManager::Instance()->EndOfEvent();
}
