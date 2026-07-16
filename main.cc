/*
 * SLabSimu.cc
 *
 * Main entry point for the MuonSLab/MuonCube simulation.
 * Supports runtime detector selection via config.yaml.
 *
 * Usage:
 *   ./SLabSimu                       # GUI mode with default config
 *   ./SLabSimu config.yaml           # Batch mode
 *   ./SLabSimu config.yaml out.root  # Batch mode with custom output
 */

#include "spdlog/spdlog.h"
#include "G4Types.hh"
#include "G4RunManager.hh"
#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"
#include "G4UImanager.hh"
#include "yaml-cpp/yaml.h"
#include "nlohmann/json.hpp"
#include "Util/Logger.hh"

#include "DetectorConstruction/DetectorFactory.hh"
#include "PhysicsList/PhysicsList.hh"
#include "Action/ActionInitialization.hh"
#include "Record/OutputManager.hh"

#include <sys/stat.h>

using json = nlohmann::json;
using std::string;

// Helper function to check if file exists
bool file_exists(const char* path) {
    struct stat buffer;
    return (stat(path, &buffer) == 0);
}

// Helper function to resolve config path (handles both root and build/ execution)
std::string resolve_config_path(const char* default_config) {
    // Try direct path first (for root directory execution)
    if (file_exists(default_config)) {
        spdlog::info("Using config path: {}", default_config);
        return std::string(default_config);
    }
    // Try with ../ prefix (for build/ directory execution)
    std::string build_path = std::string("../") + default_config;
    if (file_exists(build_path.c_str())) {
        spdlog::info("Detected execution from build/ directory");
        spdlog::info("Using config path: {}", build_path);
        return build_path;
    }
    // Return original path and let YAML throw error with proper message
    spdlog::error("Config file not found!");
    spdlog::error("  Tried: {}", default_config);
    spdlog::error("  Tried: {}", build_path);
    return std::string(default_config);
}

int main([[maybe_unused]] int argc, [[maybe_unused]] char** argv)
{
    // Initialize logging system
    LogUtils::initialize_logging();

    bool gui = false;
    std::string config = "config/config.yaml";  // Default config path
    const char* output = "output.root";
    json particle_list;
    int n_events = 1;

    // Parse command line arguments
    if (argc == 2 && (std::string(argv[1]) == "-h" || std::string(argv[1]) == "--help")) {
        spdlog::info("Usage: SimuTemplate [config.yaml] [output.root]");
        spdlog::info("");
        spdlog::info("Detector type is specified in config.yaml:");
        spdlog::info("  Detector:");
        spdlog::info("    type: \"MuonSLab\"  # or \"MuonCube\", or your own");
        return 0;
    } else if (argc == 1) {
        spdlog::info("No argument is given, running in GUI mode");
        gui = true;
        // Resolve default config path (handles both root and build/ execution)
        config = resolve_config_path(config.c_str());
    } else {
        spdlog::info("Running in batch mode");
        config = argv[1];
        output = argc > 2 ? argv[2] : output;
    }

    // Load config file
    spdlog::info("Loading config file: {}", config);
    auto config_root_node = YAML::LoadFile(config);

    // Load particle data from JSON file
    string particle_json_path = config_root_node["Particles"]["particle_file_path"].as<string>();
    std::ifstream particles_file;
    particles_file.open(particle_json_path.c_str());
    if (!particles_file.is_open()) {
        spdlog::error("Failed to open particle json file: {:s}", particle_json_path);
        throw std::runtime_error("Cannot open particle file");
    } else {
        spdlog::info("Particle json file opened: {:s}", particle_json_path);
        particles_file >> particle_list;
    }

    if (!gui) {
        n_events = config_root_node["Run"]["number_of_events"].as<int>();
        if (n_events < 0 || n_events > int(particle_list.size())) {
            n_events = int(particle_list.size());
        }
    }

    // Initialize output manager
    OutputManager::Instance()->Book(output, config);

    // Create run manager
    G4RunManager* runManager = new G4RunManager;

    // ============================================================
    // DETECTOR SELECTION VIA FACTORY PATTERN
    // ============================================================
    // Read detector type from config, default to "MuonSLab" for backward compatibility
    G4String detectorType = "MuonSLab";
    if (config_root_node["Detector"] && config_root_node["Detector"]["type"]) {
        detectorType = config_root_node["Detector"]["type"].as<string>();
    }
    spdlog::info("Selected detector type: {}", detectorType.c_str());

    // Create detector using factory
    DetectorConstructionBase* detector = DetectorFactory::Create(detectorType, config.c_str());
    runManager->SetUserInitialization(detector);
    // ============================================================

    // User physics list
    G4VModularPhysicsList* physicsList = new PhysicsList();
    runManager->SetUserInitialization(physicsList);

    // User action class
    ActionInitialization* action = new ActionInitialization(particle_list);
    runManager->SetUserInitialization(action);

    runManager->Initialize();

    if (gui) {
        // Initialize visualization
        G4VisManager* visManager = new G4VisExecutive();
        visManager->Initialize();

        // Get the pointer to the User Interface manager
        G4UImanager* UImanager = G4UImanager::GetUIpointer();

        // Optionally initialize a user interface
        G4UIExecutive* ui = new G4UIExecutive(argc, argv);

        // Select visualization macro based on detector type
        std::string vis_macro_name;
        if (detectorType == "MuonCube") {
            vis_macro_name = "config/vis_cube.mac";
            spdlog::info("Using MuonCube visualization macro: vis_cube.mac");
        } else {
            vis_macro_name = "config/vis.mac";
            spdlog::info("Using MuonSLab visualization macro: vis.mac");
        }

        // Execute the visualization macro
        std::string vis_mac = resolve_config_path(vis_macro_name.c_str());
        std::string vis_command = "/control/execute " + vis_mac;
        UImanager->ApplyCommand(vis_command.c_str());
        ui->SessionStart();
        OutputManager::Instance()->Save();
        delete ui;
        delete visManager;
    } else {
        // Run simulation in batch mode
        runManager->BeamOn(n_events);
        OutputManager::Instance()->Save();
    }

    delete runManager;

    return 0;
}
