#include "Action/RunAction.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4TransportationManager.hh"
#include "Action/SteppingAction.hh"
#include "DetectorConstruction/GeometryExporter.hh"
#include "Record/OutputManager.hh"
#include "Util/Logger.hh"

RunAction::RunAction()
    : fWorldVolume(nullptr)
{}

RunAction::~RunAction()
{}

void RunAction::BeginOfRunAction(const G4Run* aRun)
{
    // Log run start with standardized logging
    LogUtils::log_run_start(aRun->GetRunID(), aRun->GetNumberOfEventToBeProcessed());

    // Inform the run manager to save random number seed
    G4RunManager::GetRunManager()->SetRandomNumberStore(true);

    // Get world volume for geometry export
    // Note: We cannot access currentWorld directly as it's protected
    // We'll get it from the detector construction via navigator
    G4TransportationManager* transportMgr = G4TransportationManager::GetTransportationManager();
    if (transportMgr) {
        fWorldVolume = transportMgr->GetParallelWorld("World");
        if (!fWorldVolume) {
            // Fallback: get navigator's world volume
            G4Navigator* navigator = transportMgr->GetNavigatorForTracking();
            if (navigator) {
                fWorldVolume = navigator->GetWorldVolume();
            }
        }
    }

    // Create a particle filter to track hadrons and nuclei of interest
    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
    G4ParticleDefinition* particle;
    
    // Important particles to track for hadronic physics
    std::vector<std::string> importantParticles = {
        "proton", "neutron", "pi+", "pi-", "pi0", "kaon+", "kaon-", "kaon0", 
        "deuteron", "triton", "alpha", "He3", "gamma", "e-", "e+"
    };
    
    LogUtils::log_info("=== Tracking Important Particles ===");
    int trackedCount = 0;
    
    for (const auto& name : importantParticles) {
        particle = particleTable->FindParticle(name);
        if (particle) {
            trackedCount++;
            LogUtils::log_info("  Tracking particle: " + name);
            
            // Optionally set tracking verbosity for these particles
            // G4ParticleTable::GetParticleTable()->FindParticle(name)->SetVerboseLevel(1);
        }
    }
    
    LogUtils::log_info("Tracking " + std::to_string(trackedCount) + " particle types");
}

void RunAction::EndOfRunAction(const G4Run* aRun)
{
    G4int nofEvents = aRun->GetNumberOfEvent();
    if (nofEvents == 0) return;
    
    // Report run completion
    LogUtils::log_run_end(aRun->GetRunID(), nofEvents);
    
    // Access SteppingAction to get particle statistics - fix const conversion issue
    const G4UserSteppingAction* userSteppingAction = 
        G4RunManager::GetRunManager()->GetUserSteppingAction();
    
    if (userSteppingAction) {
        // Use const_cast as a workaround since we know it's safe in this context
        const SteppingAction* slabSteppingAction = 
            dynamic_cast<const SteppingAction*>(userSteppingAction);
        
        if (slabSteppingAction) {
            // Get the particle statistics
            const std::map<G4String, G4int>& particleCounts = 
                slabSteppingAction->GetParticleCount();
            
            // Log particle statistics for this run
            LogUtils::log_info("\n=== Particle Statistics for Run ===");
            for (const auto& [particle, count] : particleCounts) {
                LogUtils::log_particle_statistics(particle.data(), count);
            }
        }
    }

    // ====================================================================
    // Export generic geometry model (detector -> 3D position/dimension map)
    // Done at end of run; writes into the ROOT file owned by OutputManager.
    // The OutputManager::Save() (called after BeamOn) closes the file.
    // ====================================================================
    if (fWorldVolume) {
        auto outputMgr = OutputManager::Instance();
        G4String outputFile = outputMgr->GetOutputFileName();

        if (GeometryExporter::Export(fWorldVolume, outputFile, "GeometryModel")) {
            LogUtils::log_info("Generic geometry model exported successfully");
        } else {
            LogUtils::log_warning("Failed to export geometry model");
        }
    } else {
        LogUtils::log_warning("World volume not set - skipping geometry export");
    }
}
