#include "nvlink/nvlink_optimization.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace nvlink {

GlobalNVLinkOptimizationSystem& GlobalNVLinkOptimizationSystem::getInstance() {
    static GlobalNVLinkOptimizationSystem instance;
    return instance;
}

GlobalNVLinkOptimizationSystem::GlobalNVLinkOptimizationSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalNVLinkOptimizationSystem singleton created");
}

GlobalNVLinkOptimizationSystem::~GlobalNVLinkOptimizationSystem() {
    shutdown();
}

bool GlobalNVLinkOptimizationSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global NVLink optimization system already initialized");
        return true;
    }
    
    try {
        // Initialize topology manager
        topologyManager_ = std::make_shared<NVLinkTopologyManager>();
        if (!topologyManager_->initialize()) {
            spdlog::error("Failed to initialize NVLink topology manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_optimizers"] = "10";
        configuration_["topology_strategy"] = "balanced";
        configuration_["load_balancing_strategy"] = "round_robin";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalNVLinkOptimizationSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global NVLink optimization system: {}", e.what());
        return false;
    }
}

void GlobalNVLinkOptimizationSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown topology manager
        if (topologyManager_) {
            topologyManager_->shutdown();
            topologyManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalNVLinkOptimizationSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global NVLink optimization system shutdown: {}", e.what());
    }
}

bool GlobalNVLinkOptimizationSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<NVLinkTopologyManager> GlobalNVLinkOptimizationSystem::getTopologyManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return topologyManager_;
}

std::shared_ptr<NVLinkOptimizer> GlobalNVLinkOptimizationSystem::createOptimizer(const NVLinkConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create optimizer
        auto optimizer = topologyManager_->createOptimizer(config);
        
        if (optimizer) {
            spdlog::info("Created NVLink optimizer: {}", config.linkId);
        } else {
            spdlog::error("Failed to create NVLink optimizer: {}", config.linkId);
        }
        
        return optimizer;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create NVLink optimizer {}: {}", config.linkId, e.what());
        return nullptr;
    }
}

bool GlobalNVLinkOptimizationSystem::destroyOptimizer(const std::string& optimizerId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy optimizer
        bool destroyed = topologyManager_->destroyOptimizer(optimizerId);
        
        if (destroyed) {
            spdlog::info("Destroyed NVLink optimizer: {}", optimizerId);
        } else {
            spdlog::error("Failed to destroy NVLink optimizer: {}", optimizerId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy NVLink optimizer {}: {}", optimizerId, e.what());
        return false;
    }
}

std::shared_ptr<NVLinkOptimizer> GlobalNVLinkOptimizationSystem::getOptimizer(const std::string& optimizerId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return topologyManager_->getOptimizer(optimizerId);
}

std::future<NVLinkResponse> GlobalNVLinkOptimizationSystem::communicateAsync(const NVLinkRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return std::async(std::launch::deferred, []() {
            NVLinkResponse response;
            response.success = false;
            response.error = "System not initialized";
            return response;
        });
    }
    
    try {
        // Execute async communication
        auto future = topologyManager_->communicateAsync(request);
        
        spdlog::info("Async communication started for request {}", request.requestId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to start async communication for request {}: {}", request.requestId, e.what());
        return std::async(std::launch::deferred, []() {
            NVLinkResponse response;
            response.success = false;
            response.error = "Failed to start async communication";
            return response;
        });
    }
}

NVLinkResponse GlobalNVLinkOptimizationSystem::communicate(const NVLinkRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        NVLinkResponse response;
        response.success = false;
        response.error = "System not initialized";
        return response;
    }
    
    try {
        // Execute communication
        auto response = topologyManager_->communicate(request);
        
        if (response.success) {
            spdlog::info("Communication completed for request {}", request.requestId);
        } else {
            spdlog::error("Communication failed for request {}: {}", request.requestId, response.error);
        }
        
        return response;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to communicate for request {}: {}", request.requestId, e.what());
        NVLinkResponse response;
        response.success = false;
        response.error = "Communication failed: " + std::string(e.what());
        return response;
    }
}

std::vector<std::shared_ptr<NVLinkOptimizer>> GlobalNVLinkOptimizationSystem::getAllOptimizers() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<NVLinkOptimizer>>();
    }
    
    return topologyManager_->getAllOptimizers();
}

std::map<std::string, double> GlobalNVLinkOptimizationSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !topologyManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = topologyManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalNVLinkOptimizationSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to topology manager
    if (topologyManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_optimizers") != config.end()) {
                int maxOptimizers = std::stoi(config.at("max_optimizers"));
                topologyManager_->setMaxOptimizers(maxOptimizers);
            }
            
            if (config.find("topology_strategy") != config.end()) {
                std::string strategy = config.at("topology_strategy");
                topologyManager_->setTopologyStrategy(strategy);
            }
            
            if (config.find("load_balancing_strategy") != config.end()) {
                std::string strategy = config.at("load_balancing_strategy");
                topologyManager_->setLoadBalancingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalNVLinkOptimizationSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace nvlink
} // namespace cogniware
