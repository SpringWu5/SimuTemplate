#include "Action/ActionInitialization.hh"
#include "Action/PrimaryGeneratorAction.hh"
#include "Action/RunAction.hh"
#include "Action/EventAction.hh"
#include "Action/SteppingAction.hh"
#include "spdlog/spdlog.h"
#include "Util/Logger.hh"

ActionInitialization::ActionInitialization(json& particle_list)
    : fParticleList(particle_list),
      fPga(nullptr),
      fEventAction(nullptr),
      fRunAction(nullptr) {}

void ActionInitialization::Build() const
{
    // Create a new timestamped log file for this run
    LogUtils::initialize_logging();

    // ========================================================================
    // JSON-based Mode
    // ========================================================================
    LogUtils::log_info("=== Particle Information ===");
    if (!fParticleList.empty()) {
        LogUtils::log_info("Number of particles in list: " + std::to_string(fParticleList.size()));

        // Log first few particles as examples
        int max_examples = std::min(static_cast<int>(fParticleList.size()), 5);
        for (int i = 0; i < max_examples; i++) {
            json particle = fParticleList[i];
            std::string particle_info = "Particle " + std::to_string(i) + ": ";

            // Add available particle info
            if (particle.contains("pdgid")) {
                particle_info += "PDG ID=" + std::to_string(particle["pdgid"].get<int>()) + ", ";
            }
            if (particle.contains("energy")) {
                particle_info += "Energy=" + std::to_string(particle["energy"].get<double>()) + " MeV, ";
            }
            if (particle.contains("name")) {
                particle_info += "Name=" + particle["name"].get<std::string>();
            }

            LogUtils::log_info(particle_info);
        }

        if (fParticleList.size() > 5) {
            LogUtils::log_info("... and " + std::to_string(fParticleList.size() - 5) + " more particles");
        }
    } else {
        LogUtils::log_info("Particle list is empty");
    }

    // Set up JSON-based primary generator
    SetUserAction(new PrimaryGeneratorAction(fParticleList));

    // Set up common actions
    RunAction* runAction = new RunAction();
    SetUserAction(runAction);

    EventAction* eventAction = new EventAction();
    SetUserAction(eventAction);

    // CRITICAL FIX: Enable SteppingAction for debugging zero hits
    // This is needed to track where particles go and if they enter detector volumes
    SetUserAction(new SteppingAction(eventAction));

    spdlog::info("Action initialization completed");
    LogUtils::log_info("Action initialization completed");
}
