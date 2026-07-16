#ifndef LOGGER_HH
#define LOGGER_HH

#include <spdlog/fmt/ostr.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/spdlog.h>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <map>
#include <set>  // Added this include for std::set
#include <vector>
#include <algorithm>

namespace LogUtils {

// Add a global flag to track initialization
inline bool logging_initialized = false;

// Global variables for log file paths
inline std::string current_log_file;
inline std::string current_photon_stats_file;
inline std::filesystem::path log_directory;

// Get formatted timestamp for log file names
inline std::string get_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t_now = std::chrono::system_clock::to_time_t(now);
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t_now), "%Y-%m-%d_%H-%M-%S");
    return ss.str();
}

// Get absolute path for log directory
inline std::filesystem::path get_log_directory() {
    // Get current working directory
    std::filesystem::path cwd = std::filesystem::current_path();
    // Navigate to build/log from current directory
    std::filesystem::path logDir = cwd.parent_path() / "build" / "log";
    return logDir;
}

// 确保日志目录存在
inline bool ensure_log_directory() {
    log_directory = get_log_directory();
    
    if (!std::filesystem::exists(log_directory)) {
        try {
            bool created = std::filesystem::create_directories(log_directory);
            if (!created) {
                std::cerr << "Failed to create log directory: " << log_directory.string() << std::endl;
                return false;
            }
        } catch (const std::exception& e) {
            std::cerr << "Error creating log directory: " << e.what() << std::endl;
            return false;
        }
    }
    
    return true;
}

// Initialize photon statistics file with header
inline bool initialize_photon_stats_file() {
    if (log_directory.empty()) {
        if (!ensure_log_directory()) {
            return false;
        }
    }
    
    current_photon_stats_file = (log_directory / "photon_statistics.log").string();
    
    // Create the file with header
    std::ofstream photonFile(current_photon_stats_file, std::ios::trunc);
    if (!photonFile.is_open()) {
        std::cerr << "Failed to create photon statistics file: " << current_photon_stats_file << std::endl;
        return false;
    }
    
    // Write CSV header line
    photonFile << "EventID,CerenkovCount,ScintillationCount,TotalCount,Timestamp" << std::endl;
    photonFile.close();
    
    if (photonFile.fail()) {
        std::cerr << "Error writing to photon statistics file" << std::endl;
        return false;
    }
    
    return true;
}

// Create timestamped log file
inline std::string create_timestamped_logfile() {
    // Ensure log directory exists
    if (!ensure_log_directory()) {
        return "";
    }
    
    // Create timestamp and log file path
    std::string timestamp = get_timestamp();
    std::filesystem::path log_file_path = log_directory / ("run_" + timestamp + ".log");
    current_log_file = log_file_path.string();
    
    // Create empty file to initialize it
    std::ofstream logFile(current_log_file, std::ios::trunc);
    if (!logFile.is_open()) {
        std::cerr << "Failed to create log file: " << current_log_file << std::endl;
        return "";
    }
    
    logFile << "=== Simulation Run Started at " << timestamp << " ===" << std::endl;
    logFile << "Logging system initialized" << std::endl;
    logFile.close();
    
    if (logFile.fail()) {
        std::cerr << "Error writing to log file" << std::endl;
        return "";
    }
    
    return current_log_file;
}

// Log levels enum for consistent API
enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR
};

// Convert LogLevel to string
inline std::string log_level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG: return "[DEBUG]";
        case LogLevel::INFO: return "[INFO]";
        case LogLevel::WARNING: return "[WARNING]";
        case LogLevel::ERROR: return "[ERROR]";
        default: return "[INFO]";
    }
}

// Log a message to the current log file with level
inline bool log_message(const std::string& message, LogLevel level = LogLevel::INFO, bool console_output = true) {
    if (current_log_file.empty()) {
        return false;
    }
    
    std::string timestamp = get_timestamp();
    std::string levelStr = log_level_to_string(level);
    std::string formattedMessage = "[" + timestamp + "] " + levelStr + " " + message;
    
    // Write to log file
    std::ofstream logFile(current_log_file, std::ios::app);
    if (!logFile.is_open()) {
        std::cerr << "Failed to open log file for writing: " << current_log_file << std::endl;
        return false;
    }
    
    logFile << formattedMessage << std::endl;
    logFile.close();
    
    if (logFile.fail()) {
        std::cerr << "Error writing to log file" << std::endl;
        return false;
    }
    
    // Also output to console if requested
    if (console_output) {
        // Use spdlog with appropriate level
        switch (level) {
            case LogLevel::DEBUG:
                spdlog::debug(message);
                break;
            case LogLevel::INFO:
                spdlog::info(message);
                break;
            case LogLevel::WARNING:
                spdlog::warn(message);
                break;
            case LogLevel::ERROR:
                spdlog::error(message);
                break;
        }
    }
    
    return true;
}

// Simplified alias functions for different log levels
inline bool log_debug(const std::string& message, bool console_output = true) {
    return log_message(message, LogLevel::DEBUG, console_output);
}

inline bool log_info(const std::string& message, bool console_output = true) {
    return log_message(message, LogLevel::INFO, console_output);
}

inline bool log_warning(const std::string& message, bool console_output = true) {
    return log_message(message, LogLevel::WARNING, console_output);
}

inline bool log_error(const std::string& message, bool console_output = true) {
    return log_message(message, LogLevel::ERROR, console_output);
}

// Initialize logging system
inline bool initialize_logging() {
    if (logging_initialized) {
        // Already initialized, just return success
        return true;
    }
    
    try {
        // Ensure log directory exists and create log file
        if (!ensure_log_directory()) {
            return false;
        }
        
        // Create timestamped log file
        std::string log_file_path = create_timestamped_logfile();
        if (log_file_path.empty()) {
            return false;
        }
        
        // Initialize photon statistics file
        if (!initialize_photon_stats_file()) {
            log_error("Failed to initialize photon statistics file", true);
            // Continue anyway - non-fatal error
        }
        
        // Configure spdlog
        auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        console_sink->set_pattern("[%H:%M:%S] [%^%l%$] %v");
        
        auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(log_file_path, true);
        file_sink->set_pattern("[%H:%M:%S] [%l] %v");
        
        spdlog::sinks_init_list sinks = {console_sink, file_sink};
        auto logger = std::make_shared<spdlog::logger>("main", sinks);
        
        // Set default level to info
        logger->set_level(spdlog::level::info);
        logger->flush_on(spdlog::level::info);
        
        spdlog::register_logger(logger);
        spdlog::set_default_logger(logger);
        
        spdlog::info("Logging system initialized");
        log_info("Logging system initialized");
        
        // Mark as initialized
        logging_initialized = true;
        
        return true;
    } catch (const spdlog::spdlog_ex& ex) {
        std::cerr << "Log initialization failed: " << ex.what() << std::endl;
        return false;
    }
}

// Log to photon statistics file
inline bool log_photon_statistics_to_file(int event_id, int cerenkov_count, int scintillation_count) {
    if (current_photon_stats_file.empty()) {
        if (!initialize_photon_stats_file()) {
            return false;
        }
    }
    
    std::string timestamp = get_timestamp();
    int total_count = cerenkov_count + scintillation_count;
    
    std::ofstream logFile(current_photon_stats_file, std::ios::app);
    if (!logFile.is_open()) {
        std::cerr << "Failed to open photon statistics file: " << current_photon_stats_file << std::endl;
        return false;
    }
    
    // Add photon statistics record with timestamp
    logFile << event_id << "," 
            << cerenkov_count << "," 
            << scintillation_count << "," 
            << total_count << ","
            << timestamp << std::endl;
    
    logFile.close();
    
    if (logFile.fail()) {
        std::cerr << "Error writing to photon statistics file" << std::endl;
        return false;
    }
    
    return true;
}

// Log particle statistics
inline bool log_particle_statistics(const std::string& particle_name, int count) {
    std::string message = "Particle statistics: " + particle_name + " count: " + std::to_string(count);
    return log_info(message);
}

// Log photon statistics (to both main log and photon-specific file)
inline bool log_photon_statistics(int event_id, int cerenkov_count, int scintillation_count) {
    std::string message = "Event " + std::to_string(event_id) + 
                         " photon statistics: Cerenkov=" + std::to_string(cerenkov_count) + 
                         ", Scintillation=" + std::to_string(scintillation_count) + 
                         ", Total=" + std::to_string(cerenkov_count + scintillation_count);
    
    // Log to main log file
    bool main_log_success = log_info(message);
    
    // Log to photon statistics CSV file
    bool photon_log_success = log_photon_statistics_to_file(event_id, cerenkov_count, scintillation_count);
    
    return main_log_success && photon_log_success;
}

// Log event information
inline bool log_event_info(int event_id, const std::string& particle_name, double energy) {
    std::string message = "Event " + std::to_string(event_id) + 
                         ": Particle=" + particle_name + 
                         ", Energy=" + std::to_string(energy) + " MeV";
    return log_info(message);
}

// Log detector hit information
inline bool log_detector_hit(const std::string& detector_name, const std::string& particle_name, 
                            int copy_number, double energy, double time) {
    std::string message = detector_name + " hit: Particle=" + particle_name + 
                          ", ID=" + std::to_string(copy_number) + 
                          ", Energy=" + std::to_string(energy) + " MeV" +
                          ", Time=" + std::to_string(time) + " ns";
    return log_debug(message, false); // Don't duplicate to console by default
}

// Log run information
inline bool log_run_start(int run_id, int num_events) {
    std::string message = "=== Run " + std::to_string(run_id) + 
                         " started with " + std::to_string(num_events) + " events ===";
    return log_info(message);
}

inline bool log_run_end(int run_id, int num_events) {
    std::string message = "=== Run " + std::to_string(run_id) + 
                         " completed, processed " + std::to_string(num_events) + " events ===";
    return log_info(message);
}

// Calculate statistics for a sequence of numbers
template<typename Container>
inline std::map<std::string, double> calculate_statistics(const Container& values) {
    std::map<std::string, double> stats;
    
    if (values.empty()) {
        stats["count"] = 0;
        stats["sum"] = 0;
        stats["min"] = 0;
        stats["max"] = 0;
        stats["mean"] = 0;
        stats["stddev"] = 0;
        return stats;
    }
    
    double sum = 0;
    double min_val = *std::min_element(values.begin(), values.end());
    double max_val = *std::max_element(values.begin(), values.end());
    
    for (const auto& val : values) {
        sum += val;
    }
    
    double mean = sum / values.size();
    
    double variance_sum = 0;
    for (const auto& val : values) {
        variance_sum += (val - mean) * (val - mean);
    }
    
    double stddev = values.size() > 1 ? std::sqrt(variance_sum / (values.size() - 1)) : 0;
    
    stats["count"] = values.size();
    stats["sum"] = sum;
    stats["min"] = min_val;
    stats["max"] = max_val;
    stats["mean"] = mean;
    stats["stddev"] = stddev;
    
    return stats;
}

// Create machine-readable summary
inline bool export_summary_stats(const std::string& filename, 
                                const std::map<std::string, std::map<std::string, double>>& statistics) {
    try {
        std::filesystem::path stats_file_path = log_directory / filename;
        
        std::ofstream statsFile(stats_file_path.string(), std::ios::trunc);
        if (!statsFile.is_open()) {
            log_error("Failed to create statistics summary file: " + stats_file_path.string());
            return false;
        }
        
        // Write header first
        statsFile << "Category,Metric,Value" << std::endl;
        
        // Write all statistics
        for (const auto& [category, metrics] : statistics) {
            for (const auto& [metric, value] : metrics) {
                statsFile << category << "," << metric << "," << value << std::endl;
            }
        }
        
        statsFile.close();
        
        if (statsFile.fail()) {
            log_error("Error writing to statistics summary file");
            return false;
        }
        
        log_info("Statistics summary exported to: " + stats_file_path.string());
        return true;
    }
    catch (const std::exception& e) {
        log_error("Exception while exporting statistics summary: " + std::string(e.what()));
        return false;
    }
}

// Finalize logging with comprehensive summary
inline bool finalize_logging(int total_events, 
                           const std::map<std::string, int>& particle_counts,
                           const std::vector<int>& cerenkov_counts = {},
                           const std::vector<int>& scintillation_counts = {}) {
    
    // Build comprehensive summary text
    std::stringstream summary;
    summary << "\n===== SIMULATION SUMMARY =====" << std::endl;
    summary << "Total events processed: " << total_events << std::endl;
    
    // Particle statistics
    summary << "\n--- Particle Statistics ---" << std::endl;
    for (const auto& [particle, count] : particle_counts) {
        summary << "  - " << particle << ": " << count;
        if (total_events > 0) {
            summary << " (avg " << std::fixed << std::setprecision(2) 
                    << static_cast<double>(count) / total_events << " per event)";
        }
        summary << std::endl;
    }
    
    // Photon statistics if available
    if (!cerenkov_counts.empty() || !scintillation_counts.empty()) {
        summary << "\n--- Optical Photon Statistics ---" << std::endl;
        
        auto cerenkov_stats = calculate_statistics(cerenkov_counts);
        auto scintillation_stats = calculate_statistics(scintillation_counts);
        
        // Cerenkov photons
        summary << "  Cerenkov photons:" << std::endl;
        summary << "    - Total: " << static_cast<int>(cerenkov_stats["sum"]) << std::endl;
        if (total_events > 0) {
            summary << "    - Average per event: " << std::fixed << std::setprecision(2) 
                    << cerenkov_stats["mean"] << std::endl;
        }
        summary << "    - Min/Max: " << static_cast<int>(cerenkov_stats["min"]) << " / " 
                << static_cast<int>(cerenkov_stats["max"]) << std::endl;
        summary << "    - Std Dev: " << std::fixed << std::setprecision(2) 
                << cerenkov_stats["stddev"] << std::endl;
        
        // Scintillation photons
        summary << "  Scintillation photons:" << std::endl;
        summary << "    - Total: " << static_cast<int>(scintillation_stats["sum"]) << std::endl;
        if (total_events > 0) {
            summary << "    - Average per event: " << std::fixed << std::setprecision(2) 
                    << scintillation_stats["mean"] << std::endl;
        }
        summary << "    - Min/Max: " << static_cast<int>(scintillation_stats["min"]) << " / " 
                << static_cast<int>(scintillation_stats["max"]) << std::endl;
        summary << "    - Std Dev: " << std::fixed << std::setprecision(2) 
                << scintillation_stats["stddev"] << std::endl;
        
        // Total photons
        double total_photons = cerenkov_stats["sum"] + scintillation_stats["sum"];
        double avg_photons = total_events > 0 ? total_photons / total_events : 0;
        
        summary << "  Total photons:" << std::endl;
        summary << "    - Total: " << static_cast<int>(total_photons) << std::endl;
        if (total_events > 0) {
            summary << "    - Average per event: " << std::fixed << std::setprecision(2) 
                    << avg_photons << std::endl;
        }
        
        // Export statistics to CSV file
        std::map<std::string, std::map<std::string, double>> stats_summary;
        stats_summary["Cerenkov"] = cerenkov_stats;
        stats_summary["Scintillation"] = scintillation_stats;
        
        // Add run statistics
        std::map<std::string, double> run_stats;
        run_stats["total_events"] = total_events;
        run_stats["total_photons"] = total_photons;
        run_stats["avg_photons_per_event"] = avg_photons;
        stats_summary["Run"] = run_stats;
        
        // Add particle statistics
        for (const auto& [particle, count] : particle_counts) {
            std::map<std::string, double> particle_stats;
            particle_stats["count"] = count;
            particle_stats["avg_per_event"] = total_events > 0 ? 
                static_cast<double>(count) / total_events : 0;
            stats_summary["Particle_" + particle] = particle_stats;
        }
        
        // Export to CSV
        std::string timestamp = get_timestamp();
        export_summary_stats("run_summary_" + timestamp + ".csv", stats_summary);
    }
    
    summary << "\n=============================" << std::endl;
    
    // Log the summary
    return log_info(summary.str());
}

// Structure to store slab statistics
struct SlabStatistics {
    std::map<std::string, int> incidentParticles;  // Particles entering the slab
    std::map<std::string, int> generatedParticles; // Particles created in the slab
    int cerenkovPhotons = 0;
    int scintillationPhotons = 0;
};

// Global map to track statistics for each slab
inline std::map<int, SlabStatistics> slab_statistics;

// Reset slab statistics at the beginning of an event
inline void reset_slab_statistics() {
    slab_statistics.clear();
}

// Get particle category (for better organization)
inline std::string get_particle_category(const std::string& particle_name) {
    // Leptons
    static const std::set<std::string> leptons = {
        "e-", "e+", "mu-", "mu+", "tau-", "tau+", "nu_e", "anti_nu_e", 
        "nu_mu", "anti_nu_mu", "nu_tau", "anti_nu_tau"
    };
    
    // Mesons
    static const std::set<std::string> mesons = {
        "pi+", "pi-", "pi0", "kaon+", "kaon-", "kaon0", "anti_kaon0", 
        "eta", "eta_prime", "rho+", "rho-", "rho0", "omega"
    };
    
    // Baryons
    static const std::set<std::string> baryons = {
        "proton", "neutron", "lambda", "sigma+", "sigma0", "sigma-", 
        "xi0", "xi-", "omega-", "anti_proton", "anti_neutron", "anti_lambda"
    };
    
    // Light nuclei
    static const std::set<std::string> light_nuclei = {
        "deuteron", "triton", "alpha", "He3", "Li6", "Li7", "Be7", "Be9", "B10", "B11"
    };
    
    // Photons
    static const std::set<std::string> photons = {
        "gamma", "opticalphoton"
    };
    
    // Check category
    if (leptons.find(particle_name) != leptons.end()) {
        return "Lepton";
    } else if (mesons.find(particle_name) != mesons.end()) {
        return "Meson";
    } else if (baryons.find(particle_name) != baryons.end()) {
        return "Baryon";
    } else if (light_nuclei.find(particle_name) != light_nuclei.end()) {
        return "LightNucleus";
    } else if (photons.find(particle_name) != photons.end()) {
        return "Photon";
    } else {
        return "Other";
    }
}

// Log slab statistics for an event
inline bool log_slab_statistics(int event_id) {
    if (slab_statistics.empty()) {
        return log_info("Event " + std::to_string(event_id) + ": No slab hits recorded");
    }
    
    std::stringstream ss;
    ss << "Event " << event_id << " Slab Statistics:";
    
    // Sort slabs by ID for consistent output
    std::vector<int> slabIds;
    for (const auto& [id, _] : slab_statistics) {
        slabIds.push_back(id);
    }
    std::sort(slabIds.begin(), slabIds.end());
    
    for (int slabId : slabIds) {
        const auto& stats = slab_statistics[slabId];
        
        ss << "\n  Slab ID: " << slabId;
        
        // Incident particles
        ss << "\n    Incident particles:";
        if (stats.incidentParticles.empty()) {
            ss << " None";
        } else {
            for (const auto& [particle, count] : stats.incidentParticles) {
                ss << " " << particle << "(" << count << ")";
            }
        }
        
        // Generated particles
        ss << "\n    Generated particles:";
        if (stats.generatedParticles.empty()) {
            ss << " None";
        } else {
            for (const auto& [particle, count] : stats.generatedParticles) {
                ss << " " << particle << "(" << count << ")";
            }
        }
        
        // Optical photons
        ss << "\n    Optical photons: Cherenkov(" << stats.cerenkovPhotons 
           << "), Scintillation(" << stats.scintillationPhotons
           << "), Total(" << (stats.cerenkovPhotons + stats.scintillationPhotons) << ")";
    }
    
    return log_info(ss.str());
}

// Add incident particle to slab statistics
inline void add_incident_particle(int slab_id, const std::string& particle_name) {
    auto& stats = slab_statistics[slab_id];
    if (stats.incidentParticles.find(particle_name) == stats.incidentParticles.end()) {
        stats.incidentParticles[particle_name] = 1;
    } else {
        stats.incidentParticles[particle_name]++;
    }
}

// Add generated particle to slab statistics
inline void add_generated_particle(int slab_id, const std::string& particle_name) {
    auto& stats = slab_statistics[slab_id];
    if (stats.generatedParticles.find(particle_name) == stats.generatedParticles.end()) {
        stats.generatedParticles[particle_name] = 1;
    } else {
        stats.generatedParticles[particle_name]++;
    }
}

// Add optical photon to slab statistics
inline void add_optical_photon(int slab_id, bool is_cerenkov) {
    auto& stats = slab_statistics[slab_id];
    if (is_cerenkov) {
        stats.cerenkovPhotons++;
    } else {
        stats.scintillationPhotons++;
    }
}

// Log event summary with incident and generated particles
inline bool log_event_summary(int event_id, 
                              const std::map<std::string, int>& incident_particles,
                              int cerenkov_count, 
                              int scintillation_count) {
    std::stringstream ss;
    ss << "Event " << event_id << " Summary:";
    
    // Incident particles
    ss << "\n  Incident particles:";
    if (incident_particles.empty()) {
        ss << " None";
    } else {
        for (const auto& [particle, count] : incident_particles) {
            ss << " " << particle << "(" << count << ")";
        }
    }
    
    // Optical photons
    ss << "\n  Optical photons: Cherenkov(" << cerenkov_count 
       << "), Scintillation(" << scintillation_count
       << "), Total(" << (cerenkov_count + scintillation_count) << ")";
    
    return log_info(ss.str());
}

// Determine if a process is likely Cherenkov based on process type
inline bool is_likely_cerenkov(int processType) {
    // Process type 21 is often associated with Cherenkov
    return processType == 21;
}

// Determine if a process is likely Scintillation based on process type
inline bool is_likely_scintillation(int processType) {
    // Process type 22 is often associated with Scintillation
    return processType == 22;
}

// Structure to store detected particle statistics
struct DetectedSlabStatistics {
    std::map<std::string, int> detectedParticles;
    int detectedCerenkovPhotons = 0;
    int detectedScintillationPhotons = 0;
};

// Global map to track detection statistics for each slab
inline std::map<int, DetectedSlabStatistics> detected_slab_statistics;

// Reset detection statistics at the beginning of an event
inline void reset_detection_statistics() {
    detected_slab_statistics.clear();
}

// Log detection statistics for an event
inline bool log_detection_statistics(int event_id) {
    if (detected_slab_statistics.empty()) {
        return log_info("Event " + std::to_string(event_id) + ": No detected particles recorded");
    }
    
    std::stringstream ss;
    ss << "Event " << event_id << " Detection Statistics:";
    
    // Sort slabs by ID for consistent output
    std::vector<int> slabIds;
    for (const auto& [id, _] : detected_slab_statistics) {
        slabIds.push_back(id);
    }
    std::sort(slabIds.begin(), slabIds.end());
    
    for (int slabId : slabIds) {
        const auto& stats = detected_slab_statistics[slabId];
        
        ss << "\n  Slab ID: " << slabId;
        
        // Group particles by category
        std::map<std::string, std::map<std::string, int>> categorized_particles;
        for (const auto& [particle, count] : stats.detectedParticles) {
            std::string category = get_particle_category(particle);
            categorized_particles[category][particle] = count;
        }
        
        // Output by category
        for (const auto& [category, particles] : categorized_particles) {
            ss << "\n    " << category << "s:";
            for (const auto& [particle, count] : particles) {
                ss << " " << particle << "(" << count << ")";
            }
        }
        
        // Detected optical photons
        ss << "\n    Optical photons: Cherenkov(" << stats.detectedCerenkovPhotons 
           << "), Scintillation(" << stats.detectedScintillationPhotons
           << "), Total(" << (stats.detectedCerenkovPhotons + stats.detectedScintillationPhotons) << ")";
    }
    
    return log_info(ss.str());
}

// Add detected particle to statistics
inline void add_detected_particle(int slab_id, const std::string& particle_name) {
    auto& stats = detected_slab_statistics[slab_id];
    if (stats.detectedParticles.find(particle_name) == stats.detectedParticles.end()) {
        stats.detectedParticles[particle_name] = 1;
    } else {
        stats.detectedParticles[particle_name]++;
    }
}

// Add detected optical photon to statistics
inline void add_detected_optical_photon(int slab_id, bool is_cerenkov) {
    auto& stats = detected_slab_statistics[slab_id];
    if (is_cerenkov) {
        stats.detectedCerenkovPhotons++;
    } else {
        stats.detectedScintillationPhotons++;
    }
}

// Structure to track unique particles by their track IDs
struct UniqueParticleStatistics {
    std::map<std::string, std::set<int>> uniqueParticleIDs; // Map of particle name to set of track IDs
    std::set<int> uniqueCerenkovPhotonIDs;
    std::set<int> uniqueScintillationPhotonIDs;
};

// Global map to track unique particles for each slab
inline std::map<int, UniqueParticleStatistics> unique_particle_statistics;

// Reset unique particle statistics at the beginning of an event
inline void reset_unique_statistics() {
    unique_particle_statistics.clear();
}

// Add a unique particle to statistics (returns true if it's new)
inline bool add_unique_particle(int slab_id, const std::string& particle_name, int track_id) {
    auto& stats = unique_particle_statistics[slab_id];
    return stats.uniqueParticleIDs[particle_name].insert(track_id).second;
}

// Add a unique optical photon to statistics (returns true if it's new)
inline bool add_unique_optical_photon(int slab_id, bool is_cerenkov, int track_id) {
    auto& stats = unique_particle_statistics[slab_id];
    if (is_cerenkov) {
        return stats.uniqueCerenkovPhotonIDs.insert(track_id).second;
    } else {
        return stats.uniqueScintillationPhotonIDs.insert(track_id).second;
    }
}

// Log unique particle statistics for an event
inline bool log_unique_statistics(int event_id) {
    if (unique_particle_statistics.empty()) {
        return log_info("Event " + std::to_string(event_id) + ": No unique particles recorded");
    }
    
    std::stringstream ss;
    ss << "Event " << event_id << " Unique Particle Statistics:";
    
    // Sort slabs by ID for consistent output
    std::vector<int> slabIds;
    for (const auto& [id, _] : unique_particle_statistics) {
        slabIds.push_back(id);
    }
    std::sort(slabIds.begin(), slabIds.end());
    
    for (int slabId : slabIds) {
        const auto& stats = unique_particle_statistics[slabId];
        
        ss << "\n  Slab ID: " << slabId;
        
        // Group particles by category
        std::map<std::string, std::map<std::string, int>> categorized_particles;
        for (const auto& [particle, trackIDs] : stats.uniqueParticleIDs) {
            std::string category = get_particle_category(particle);
            categorized_particles[category][particle] = trackIDs.size();
        }
        
        // Output by category
        for (const auto& [category, particles] : categorized_particles) {
            ss << "\n    " << category << "s:";
            for (const auto& [particle, count] : particles) {
                ss << " " << particle << "(" << count << ")";
            }
        }
        
        // Unique optical photons
        int cerenkovCount = stats.uniqueCerenkovPhotonIDs.size();
        int scintillationCount = stats.uniqueScintillationPhotonIDs.size();
        ss << "\n    Optical photons: Cherenkov(" << cerenkovCount
           << "), Scintillation(" << scintillationCount
           << "), Total(" << (cerenkovCount + scintillationCount) << ")";
    }
    
    return log_info(ss.str());
}

// Add enhanced run summary with particle categories
inline bool log_detailed_particle_summary() {
    std::stringstream ss;
    ss << "\n===== DETAILED PARTICLE SUMMARY =====";
    
    // Group all seen particles by category for final statistics
    std::map<std::string, std::map<std::string, int>> categorized_total_counts;
    
    // Count total unique particles seen
    int total_unique_leptons = 0;
    int total_unique_mesons = 0;
    int total_unique_baryons = 0;
    int total_unique_nuclei = 0;
    int total_unique_other = 0;
    
    // Process all slabs
    for (const auto& [slabId, stats] : unique_particle_statistics) {
        for (const auto& [particle, trackIDs] : stats.uniqueParticleIDs) {
            std::string category = get_particle_category(particle);
            categorized_total_counts[category][particle] += trackIDs.size();
            
            // Update category totals
            if (category == "Lepton") total_unique_leptons += trackIDs.size();
            else if (category == "Meson") total_unique_mesons += trackIDs.size();
            else if (category == "Baryon") total_unique_baryons += trackIDs.size();
            else if (category == "LightNucleus") total_unique_nuclei += trackIDs.size();
            else total_unique_other += trackIDs.size();
        }
    }
    
    // Output category summaries
    ss << "\n\n--- Particle Category Summary ---";
    ss << "\n  Total unique leptons: " << total_unique_leptons;
    ss << "\n  Total unique mesons: " << total_unique_mesons;
    ss << "\n  Total unique baryons: " << total_unique_baryons;
    ss << "\n  Total unique light nuclei: " << total_unique_nuclei;
    ss << "\n  Total unique other particles: " << total_unique_other;
    
    // Output by category
    for (const auto& [category, particles] : categorized_total_counts) {
        ss << "\n\n--- " << category << " Details ---";
        for (const auto& [particle, count] : particles) {
            ss << "\n  " << particle << ": " << count << " unique particles";
        }
    }
    
    return log_info(ss.str());
}

// Close the LogUtils namespace before the compatibility functions
} // namespace LogUtils

// 为了兼容现有代码，提供原来的接口函数 (Keep these outside namespace)
inline std::shared_ptr<spdlog::logger> create_logger(
    [[maybe_unused]] std::string const &name, 
    [[maybe_unused]] bool const defaultlog = false) 
{
    // 简单返回默认记录器
    return spdlog::default_logger();
}

// 兼容函数：创建文件日志记录器
inline std::shared_ptr<spdlog::logger> create_file_logger(
    [[maybe_unused]] std::string const &name,
    [[maybe_unused]] std::string const &filename,
    [[maybe_unused]] bool const defaultlog = false) 
{
    return spdlog::default_logger();
}

#endif