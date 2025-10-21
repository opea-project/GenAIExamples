#include "rest_api_server.h"
#include "cognidream_platform_api.h"
#include "enhanced_driver.h"
#include <spdlog/spdlog.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <signal.h>
#include <iostream>

namespace cogniware {

// Global variables for signal handling
static std::atomic<bool> g_shutdown_requested{false};
static RESTServer* g_server = nullptr;

// Signal handler
void signalHandler(int signal) {
    spdlog::info("Received signal {}, initiating shutdown...", signal);
    g_shutdown_requested = true;
    
    if (g_server) {
        g_server->shutdown();
    }
}

// Setup logging
void setupLogging(const std::string& logLevel, const std::string& logFile) {
    try {
        // Create console sink
        auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        console_sink->set_level(spdlog::level::from_str(logLevel));
        
        // Create file sink with rotation
        auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
            logFile, 1024 * 1024 * 10, 5); // 10MB max file size, 5 rotated files
        file_sink->set_level(spdlog::level::from_str(logLevel));
        
        // Create logger with both sinks
        auto logger = std::make_shared<spdlog::logger>("cogniware", 
            spdlog::sinks_init_list{console_sink, file_sink});
        
        spdlog::set_default_logger(logger);
        spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [%t] %v");
        
        spdlog::info("Logging initialized with level: {}", logLevel);
        
    } catch (const std::exception& e) {
        std::cerr << "Failed to setup logging: " << e.what() << std::endl;
        // Fallback to basic logging
        spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v");
    }
}

// Load configuration
nlohmann::json loadConfiguration(const std::string& configFile) {
    try {
        std::ifstream file(configFile);
        if (!file.is_open()) {
            spdlog::warn("Configuration file not found: {}, using defaults", configFile);
            return nlohmann::json::object();
        }
        
        nlohmann::json config;
        file >> config;
        spdlog::info("Configuration loaded from: {}", configFile);
        return config;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to load configuration: {}", e.what());
        return nlohmann::json::object();
    }
}

// Validate configuration
bool validateConfiguration(const nlohmann::json& config) {
    try {
        // Check required fields
        if (!config.contains("server")) {
            spdlog::error("Missing server configuration");
            return false;
        }
        
        auto& server = config["server"];
        if (!server.contains("host") || !server.contains("port")) {
            spdlog::error("Missing host or port in server configuration");
            return false;
        }
        
        if (!config.contains("logging")) {
            spdlog::warn("Missing logging configuration, using defaults");
        }
        
        if (!config.contains("compute")) {
            spdlog::warn("Missing compute configuration, using defaults");
        }
        
        spdlog::info("Configuration validation passed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Configuration validation failed: {}", e.what());
        return false;
    }
}

// Initialize platform components
bool initializePlatform(const nlohmann::json& config) {
    try {
        spdlog::info("Initializing MSmartCompute Platform...");
        
        // Initialize enhanced driver
        auto& driver = EnhancedDriver::getInstance();
        EnhancedDriverConfig driverConfig;
        
        if (config.contains("compute")) {
            auto& compute = config["compute"];
            driverConfig.deviceId = compute.value("device_id", 0);
            driverConfig.numStreams = compute.value("num_streams", 4);
            driverConfig.monitoringInterval = compute.value("monitoring_interval", 100);
            driverConfig.enableTensorCores = compute.value("enable_tensor_cores", true);
            driverConfig.enableMixedPrecision = compute.value("enable_mixed_precision", true);
            driverConfig.optimizationLevel = compute.value("optimization_level", 2);
        }
        
        if (!driver.initialize(driverConfig)) {
            spdlog::error("Failed to initialize enhanced driver");
            return false;
        }
        
        // Initialize CogniDream Platform API
        auto& api = CogniDreamPlatformAPI::getInstance();
        if (!api.initialize(config)) {
            spdlog::error("Failed to initialize CogniDream Platform API");
            return false;
        }
        
        // Initialize REST API server
        auto& server = RESTServer::getInstance();
        g_server = &server;
        
        ServerConfig serverConfig;
        if (config.contains("server")) {
            auto& serverConfigJson = config["server"];
            serverConfig.host = serverConfigJson.value("host", "localhost");
            serverConfig.port = serverConfigJson.value("port", 8080);
            serverConfig.deviceId = serverConfigJson.value("device_id", 0);
            serverConfig.numStreams = serverConfigJson.value("num_streams", 4);
            serverConfig.monitoringInterval = serverConfigJson.value("monitoring_interval", 100);
            serverConfig.enableTensorCores = serverConfigJson.value("enable_tensor_cores", true);
            serverConfig.enableMixedPrecision = serverConfigJson.value("enable_mixed_precision", true);
            serverConfig.optimizationLevel = serverConfigJson.value("optimization_level", 2);
            serverConfig.maxConnections = serverConfigJson.value("max_connections", 1000);
            serverConfig.requestTimeout = serverConfigJson.value("request_timeout", 30);
            serverConfig.enableCORS = serverConfigJson.value("enable_cors", true);
            serverConfig.logLevel = serverConfigJson.value("log_level", "info");
        }
        
        if (!server.initialize(serverConfig)) {
            spdlog::error("Failed to initialize REST API server");
            return false;
        }
        
        spdlog::info("MSmartCompute Platform initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize platform: {}", e.what());
        return false;
    }
}

// Shutdown platform components
void shutdownPlatform() {
    spdlog::info("Shutting down MSmartCompute Platform...");
    
    try {
        // Shutdown components in reverse order
        if (g_server) {
            g_server->shutdown();
            g_server = nullptr;
        }
        
        CogniDreamPlatformAPI::getInstance().shutdown();
        EnhancedDriver::getInstance().shutdown();
        
        spdlog::info("MSmartCompute Platform shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during shutdown: {}", e.what());
    }
}

// Main application loop
void runMainLoop() {
    spdlog::info("Starting main application loop...");
    
    while (!g_shutdown_requested) {
        try {
            // Check if server is still running
            if (g_server && !g_server->isRunning()) {
                spdlog::error("REST API server stopped unexpectedly");
                break;
            }
            
            // Sleep for a short interval
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
            
        } catch (const std::exception& e) {
            spdlog::error("Error in main loop: {}", e.what());
            break;
        }
    }
    
    spdlog::info("Main application loop ended");
}

// Print startup banner
void printBanner() {
    std::cout << R"(
╔══════════════════════════════════════════════════════════════╗
║                    MSmartCompute Platform                    ║
║                        Version 1.0.0                        ║
║                                                              ║
║  High-Performance CUDA-Based Machine Learning Platform      ║
║  Enhanced Kernels, Virtualization, and CogniDream APIs      ║
║                                                              ║
║  Copyright (c) 2024 MSmartCompute                           ║
╚══════════════════════════════════════════════════════════════╝
)" << std::endl;
}

// Print usage information
void printUsage(const char* programName) {
    std::cout << "Usage: " << programName << " [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -c, --config <file>     Configuration file (default: config.json)" << std::endl;
    std::cout << "  -l, --log-level <level> Log level (debug, info, warn, error)" << std::endl;
    std::cout << "  -h, --help              Show this help message" << std::endl;
    std::cout << "  -v, --version           Show version information" << std::endl;
}

// Print version information
void printVersion() {
    std::cout << "MSmartCompute Platform v1.0.0" << std::endl;
    std::cout << "Build: " << __DATE__ << " " << __TIME__ << std::endl;
    std::cout << "CUDA Support: Enabled" << std::endl;
    std::cout << "Enhanced Kernels: Enabled" << std::endl;
    std::cout << "Virtualization: Enabled" << std::endl;
    std::cout << "CogniDream APIs: Enabled" << std::endl;
}

} // namespace cogniware

int main(int argc, char* argv[]) {
    using namespace cogniware;
    
    // Parse command line arguments
    std::string configFile = "config.json";
    std::string logLevel = "info";
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "-h" || arg == "--help") {
            printUsage(argv[0]);
            return 0;
        } else if (arg == "-v" || arg == "--version") {
            printVersion();
            return 0;
        } else if (arg == "-c" || arg == "--config") {
            if (i + 1 < argc) {
                configFile = argv[++i];
            } else {
                std::cerr << "Error: Missing configuration file path" << std::endl;
                return 1;
            }
        } else if (arg == "-l" || arg == "--log-level") {
            if (i + 1 < argc) {
                logLevel = argv[++i];
            } else {
                std::cerr << "Error: Missing log level" << std::endl;
                return 1;
            }
        } else {
            std::cerr << "Error: Unknown argument: " << arg << std::endl;
            printUsage(argv[0]);
            return 1;
        }
    }
    
    // Print startup banner
    printBanner();
    
    try {
        // Setup signal handlers
        signal(SIGINT, signalHandler);
        signal(SIGTERM, signalHandler);
        
        // Setup logging
        setupLogging(logLevel, "logs/cogniware.log");
        
        // Load and validate configuration
        auto config = loadConfiguration(configFile);
        if (!validateConfiguration(config)) {
            spdlog::error("Configuration validation failed");
            return 1;
        }
        
        // Initialize platform
        if (!initializePlatform(config)) {
            spdlog::error("Platform initialization failed");
            return 1;
        }
        
        // Run main application loop
        runMainLoop();
        
        // Shutdown platform
        shutdownPlatform();
        
        spdlog::info("Application terminated successfully");
        return 0;
        
    } catch (const std::exception& e) {
        spdlog::critical("Unhandled exception: {}", e.what());
        shutdownPlatform();
        return 1;
    } catch (...) {
        spdlog::critical("Unknown error occurred");
        shutdownPlatform();
        return 1;
    }
} 