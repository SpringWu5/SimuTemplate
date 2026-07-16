#include "Action/SteppingAction.hh"
#include "Action/EventAction.hh"

#include "G4Step.hh"
#include "G4RunManager.hh"
#include "G4Event.hh"
#include "G4Track.hh"
#include "G4OpticalPhoton.hh"
#include "G4SystemOfUnits.hh"
#include "spdlog/spdlog.h"
#include "Util/Logger.hh"
#include <fstream>
#include <iomanip>
#include <ctime>
#include <vector>

SteppingAction::SteppingAction(EventAction* eventAction)
: G4UserSteppingAction(),
  fEventAction(eventAction),
  cerenkovCount(0),
  scintillationCount(0),
  wlsCount(0),
  currentEventID(-1)
{
    // Initialize photon counting using standardized logging
    LogUtils::log_info("Optical photon counting initialized");
}

SteppingAction::~SteppingAction()
{
    // Ensure statistics for the last event are output
    OutputFinalStatistics();
}

void SteppingAction::OutputFinalStatistics()
{
    // This function will output statistics for the last event
    if (currentEventID >= 0) {
        OutputPhotonStatistics(currentEventID, cerenkovCount, scintillationCount);
    }
    
    // Output the final particle statistics
    LogUtils::log_info("\n=== Final Particle Statistics ===");
    for (const auto& [particle, count] : particleCount) {
        LogUtils::log_particle_statistics(particle, count);
    }
    
    // Create a map for the finalize_logging function
    std::map<std::string, int> particleCountsStd;
    for (const auto& [particle, count] : particleCount) {
        particleCountsStd[particle] = count;
    }
    
    // Get total events - use a simpler approach to avoid compile errors
    G4int totalEvents = currentEventID + 1;
    if (totalEvents <= 0) totalEvents = 1; // Safety check
    
    // Finalize the logging with comprehensive summary
    LogUtils::finalize_logging(totalEvents, particleCountsStd, fCerenkovCounts, fScintillationCounts);
}

// Modified parameter names to avoid variable shadowing
void SteppingAction::OutputPhotonStatistics(G4int eventID, G4int cerCount, G4int scintCount)
{
    // Store counts for summary statistics
    fCerenkovCounts.push_back(cerCount);
    fScintillationCounts.push_back(scintCount);

    // Use the enhanced logging system
    LogUtils::log_photon_statistics(eventID, cerCount, scintCount);
}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
    // === DIAGNOSTIC: Track muon steps in first 2 events ===
    // PRODUCTION: Disabled for performance
    /*
    static int step_in_detector = 0;
    G4int eventID = -1;
    const G4Event* currentEvent = G4RunManager::GetRunManager()->GetCurrentEvent();
    if (currentEvent) {
        eventID = currentEvent->GetEventID();
        if (eventID < 2) {  // Only for first 2 events
            G4Track* track = step->GetTrack();
            if (track->GetDefinition()->GetParticleName() == "mu-") {
                G4StepPoint* prePoint = step->GetPreStepPoint();
                G4StepPoint* postPoint = step->GetPostStepPoint();
                G4VPhysicalVolume* preVol = prePoint->GetPhysicalVolume();
                G4VPhysicalVolume* postVol = postPoint->GetPhysicalVolume();

                G4ThreeVector prePos = prePoint->GetPosition();
                G4ThreeVector postPos = postPoint->GetPosition();

                G4String preVolName = preVol ? preVol->GetName() : "NULL";
                G4String postVolName = postVol ? postVol->GetName() : "NULL";

                // Check if entering/inside voxel
                bool inVoxel = (preVolName.contains("Voxel") || postVolName.contains("Voxel"));

                if (inVoxel || step_in_detector < 50) {
                    G4cout << ">>> [STEP-DEBUG] Event" << eventID
                           << " Step#" << track->GetCurrentStepNumber()
                           << " PreVol: " << preVolName
                           << " PostVol: " << postVolName
                           << " PrePos(mm): (" << prePos.x()/mm << ", " << prePos.y()/mm << ", " << prePos.z()/mm << ")"
                           << " PostPos(mm): (" << postPos.x()/mm << ", " << postPos.y()/mm << ", " << postPos.z()/mm << ")"
                           << " StepLen(mm): " << step->GetStepLength()/mm
                           << " Edep(MeV): " << step->GetTotalEnergyDeposit()/MeV
                           << G4endl;

                    if (inVoxel) step_in_detector++;
                }
            }
        }
    }
    */
    // === END DIAGNOSTIC ===

    // Get current event ID safely
    G4int eventID = -1;
    const G4Event* currentEvent = G4RunManager::GetRunManager()->GetCurrentEvent();
    if (currentEvent) {
        eventID = currentEvent->GetEventID();
    }
    if (eventID == -1) return;  // Already set above

    // If event ID changes, output results of previous event and reset counters
    if (eventID != currentEventID) {
        if (currentEventID >= 0) {
            // Output photon statistics for the previous event
            OutputPhotonStatistics(currentEventID, cerenkovCount, scintillationCount);
            
            // Remove slab statistics logging
            // LogUtils::log_slab_statistics(currentEventID);  // REMOVE THIS LINE
            
            // Only keep detection statistics (will be logged by EventAction)
            
            // Log simplified event summary without detailed generation stats
            std::map<std::string, int> incidentParticles;
            for (const auto& [particle, count] : particleCount) {
                if (particle != "opticalphoton") {
                    incidentParticles[particle] = count;
                }
            }
            
            std::map<std::string, int> emptyMap; // No need for generated particles
            LogUtils::log_event_summary(currentEventID, incidentParticles, 
                                      cerenkovCount, scintillationCount);
        }
        
        // Reset counters
        cerenkovCount = 0;
        scintillationCount = 0;
        wlsCount = 0;
        currentEventID = eventID;
        particleCount.clear();
        
        // Reset statistics for the new event
        LogUtils::reset_detection_statistics();
        LogUtils::reset_unique_statistics();  // Add this line
    }
    
    // Get the volume information
    G4StepPoint* preStepPoint = step->GetPreStepPoint();
    G4StepPoint* postStepPoint = step->GetPostStepPoint();
    
    if (!preStepPoint || !postStepPoint) return;
    
    G4VPhysicalVolume* preVolume = preStepPoint->GetPhysicalVolume();
    
    if (!preVolume) return;
    
    // Check if this is a step inside a slab
    // Extract the touch history to get the volume hierarchy
    const G4TouchableHistory* touchable = 
        static_cast<const G4TouchableHistory*>(preStepPoint->GetTouchable());
    
    if (!touchable) return;
    
    // Get the copy number which should correspond to the slab ID
    G4int slabID = -1;
    
    // Check if the volume name contains "slab" (case insensitive)
    G4String volumeName = preVolume->GetName();
    std::string volumeNameLower = volumeName;
    std::transform(volumeNameLower.begin(), volumeNameLower.end(), volumeNameLower.begin(), ::tolower);
    
    if (volumeNameLower.find("slab") != std::string::npos) {
        slabID = touchable->GetCopyNumber(0);
    }
    
    // Track primary particle
    G4Track* primaryTrack = step->GetTrack();
    if (primaryTrack) {
        G4ParticleDefinition* particleDef = primaryTrack->GetDefinition();
        if (particleDef) {
            G4String particleName = particleDef->GetParticleName();
            
            // Only count particles we haven't seen in this event
            if (primaryTrack->GetParentID() == 0) { // Primary particle
                if (particleCount.find(particleName) == particleCount.end()) {
                    particleCount[particleName] = 1;
                } else {
                    particleCount[particleName]++;
                }
                
                // If this is a slab, record it as an incident particle
                if (slabID >= 0 && step->IsFirstStepInVolume()) {
                    LogUtils::add_incident_particle(slabID, particleName.data());
                }
            }
        }
    }
    
    // Get secondary particles in this step
    const std::vector<const G4Track*>* secondaries = step->GetSecondaryInCurrentStep();
    
    if (secondaries && !secondaries->empty()) {
        // Check each secondary particle
        for (const auto* secondaryTrack : *secondaries) {
            if (!secondaryTrack) continue; // Skip null pointers
            
            G4ParticleDefinition* particleDef = secondaryTrack->GetDefinition();
            if (!particleDef) continue; // Skip tracks with no definition
            
            G4String particleName = particleDef->GetParticleName();
            
            // Track ALL secondary particle types, not just a few specific ones
            if (particleDef != G4OpticalPhoton::OpticalPhotonDefinition()) {
                // For non-optical particles, count them for statistics
                if (secondaryTrack->GetParentID() > 0) { // Secondary particle
                    std::string trackName = particleName.data();
                    if (particleCount.find(trackName) == particleCount.end()) {
                        particleCount[trackName] = 1;
                    } else {
                        particleCount[trackName]++;
                    }
                    
                    // If this is a slab, record it as a generated particle
                    if (slabID >= 0) {
                        LogUtils::add_generated_particle(slabID, particleName.data());
                    }
                }
            } else {
                // Handle optical photons
                const G4VProcess* process = secondaryTrack->GetCreatorProcess();
                if (process) {
                    G4String processName = process->GetProcessName();
                    
                    // Update counter based on creation process
                    if (processName == "Cerenkov") {
                        cerenkovCount++;
                        
                        // Get creation position and find which slab (if any) it's in
                        G4ThreeVector position = secondaryTrack->GetPosition();
                        
                        // Find the slab this photon was created in (if any)
                        // This approach uses the current step's slabID as a fallback
                        G4int photonSlabID = slabID;
                        
                        // Always record the photon in global statistics
                        if (photonSlabID >= 0) {
                            LogUtils::add_optical_photon(photonSlabID, true);
                        }
                    }
                    else if (processName == "Scintillation") {
                        scintillationCount++;

                        // Use the same slabID logic as above
                        G4int photonSlabID = slabID;

                        // Always record the photon in global statistics
                        if (photonSlabID >= 0) {
                            LogUtils::add_optical_photon(photonSlabID, false);
                        }
                    }
                }
            }
        }
    }

    // === WLS PROBE: Detect OpWLS (Wavelength Shifting) photons ===
    G4Track* opticalTrack = step->GetTrack();
    if (opticalTrack->GetDefinition() == G4OpticalPhoton::OpticalPhotonDefinition()) {
        const G4VProcess* creatorProcess = opticalTrack->GetCreatorProcess();
        if (creatorProcess && creatorProcess->GetProcessName() == "OpWLS") {
            wlsCount++;

            // Get position for debugging
            G4ThreeVector position = opticalTrack->GetPosition();

            // Print first 5 WLS photons per event for debugging
            // PRODUCTION: Disabled WLS photon debug output
            /*
            static int wlsPrintCount = 0;
            if (wlsPrintCount < 5) {
                G4cout << ">>> [DEBUG] WLS Photon Created! "
                       << "Event: " << eventID
                       << ", Position(mm): (" << position.x()/mm << ", " << position.y()/mm << ", " << position.z()/mm << ")"
                       << G4endl;
                wlsPrintCount++;
            }
            */

            // Reset print counter for new event
            if (eventID != currentEventID) {
                // wlsPrintCount = 0;  // PRODUCTION: Disabled
            }
        }
    }

    // === WLS TRANSPORT TRACKING: Trace WLS photon propagation ===
    if (opticalTrack->GetDefinition() == G4OpticalPhoton::OpticalPhotonDefinition()) {
        const G4VProcess* creatorProcess = opticalTrack->GetCreatorProcess();
        if (creatorProcess && creatorProcess->GetProcessName() == "OpWLS") {

            // Track boundary crossings
            // PRODUCTION: Disabled for performance (uncomment for debugging)
            /*
            if (wlsPostStep->GetStepStatus() == fGeomBoundary) {
                G4ThreeVector pos = wlsPostStep->GetPosition();
                G4String preMaterial = wlsPreStep->GetMaterial()->GetName();
                G4String postMaterial = wlsPostStep->GetMaterial() ? wlsPostStep->GetMaterial()->GetName() : "NULL";

                G4cout << ">>> [WLS-TRANSPORT] TrackID " << opticalTrack->GetTrackID()
                       << " crossed boundary"
                       << " | PreVol: " << wlsPreStep->GetPhysicalVolume()->GetName()
                       << " -> PostVol: " << (wlsPostStep->GetPhysicalVolume() ? wlsPostStep->GetPhysicalVolume()->GetName() : "World")
                       << " | PreMat: " << preMaterial
                       << " -> PostMat: " << postMaterial
                       << " | Pos(mm): (" << pos.x()/mm << ", " << pos.y()/mm << ", " << pos.z()/mm << ")"
                       << " | Z_boundary: " << pos.z()/mm
                       << G4endl;
            }
            */

            // Track photon death
            // PRODUCTION: Disabled for performance (uncomment for debugging)
            /*
            if (opticalTrack->GetTrackStatus() == fStopAndKill ||
                opticalTrack->GetTrackStatus() == fKillTrackAndSecondaries) {

                G4ThreeVector pos = step->GetPostStepPoint()->GetPosition();
                G4String material = wlsPreStep->GetMaterial()->GetName();
                G4String volume = wlsPreStep->GetPhysicalVolume()->GetName();

                // Determine why it died
                const G4VProcess* postProcess = wlsPostStep->GetProcessDefinedStep();
                G4String killReason = postProcess ? postProcess->GetProcessName() : "Unknown";

                G4cout << ">>> [WLS-DEATH] TrackID " << opticalTrack->GetTrackID()
                       << " DIED"
                       << " | Reason: " << killReason
                       << " | Volume: " << volume
                       << " | Material: " << material
                       << " | Pos(mm): (" << pos.x()/mm << ", " << pos.y()/mm << ", " << pos.z()/mm << ")"
                       << " | Energy(eV): " << opticalTrack->GetKineticEnergy()/eV
                       << G4endl;
            }
            */
        }
    }

    // Track interesting primary particles too
    G4ParticleDefinition* particleDef = opticalTrack->GetDefinition();
    if (particleDef) {
        G4String particleName = particleDef->GetParticleName();
        G4int trackID = opticalTrack->GetTrackID();
        
        // Special logging for interesting particles like neutrons, protons, and other hadrons
        static const std::set<std::string> interestingParticles = {
            "neutron", "proton", "pi+", "pi-", "pi0", "kaon+", "kaon-", "kaon0", 
            "alpha", "deuteron", "triton", "He3", "sigma+", "sigma-", "xi-", "lambda"
        };
        
        std::string particleNameStr = particleName.data();
        if (interestingParticles.find(particleNameStr) != interestingParticles.end()) {
            // Log interesting hadronic physics at debug level
            G4double energy = opticalTrack->GetKineticEnergy() / CLHEP::MeV;

            // Only log when they're first created
            if (opticalTrack->GetCurrentStepNumber() == 1) {
                std::stringstream ss;
                ss << "Interesting particle created: " << particleNameStr
                   << " (TrackID: " << trackID
                   << ", ParentID: " << opticalTrack->GetParentID()
                   << ", Energy: " << energy << " MeV)";
                LogUtils::log_debug(ss.str());
            }
        }
    }
}