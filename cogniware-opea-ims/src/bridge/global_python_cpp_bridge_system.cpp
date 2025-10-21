#include "bridge/python_cpp_bridge.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace bridge {

GlobalPythonCppBridgeSystem& GlobalPythonCppBridgeSystem::getInstance() {
    static GlobalPythonCppBridgeSystem instance;
    return instance;
}

GlobalPythonCppBridgeSystem::GlobalPythonCppBridgeSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalPythonCppBridgeSystem singleton created");
}

GlobalPythonCppBridgeSystem::~GlobalPythonCppBridgeSystem() {
    shutdown();
}

bool GlobalPythonCppBridgeSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global Python-C++ bridge system already initialized");
        return true;
    }
    
    try {
        // Initialize bridge manager
        bridgeManager_ = std::make_shared<PythonCppBridgeManager>();
        if (!bridgeManager_->initialize()) {
            spdlog::error("Failed to initialize Python-C++ bridge manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_bridges"] = "10";
        configuration_["python_path"] = "/usr/lib/python3.12";
        configuration_["memory_sharing_strategy"] = "shared";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalPythonCppBridgeSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global Python-C++ bridge system: {}", e.what());
        return false;
    }
}

void GlobalPythonCppBridgeSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown bridge manager
        if (bridgeManager_) {
            bridgeManager_->shutdown();
            bridgeManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalPythonCppBridgeSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global Python-C++ bridge system shutdown: {}", e.what());
    }
}

bool GlobalPythonCppBridgeSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<PythonCppBridgeManager> GlobalPythonCppBridgeSystem::getBridgeManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return bridgeManager_;
}

std::shared_ptr<PythonCppBridge> GlobalPythonCppBridgeSystem::createBridge(const BridgeConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create bridge
        auto bridge = bridgeManager_->createBridge(config);
        
        if (bridge) {
            spdlog::info("Created Python-C++ bridge: {}", config.bridgeId);
        } else {
            spdlog::error("Failed to create Python-C++ bridge: {}", config.bridgeId);
        }
        
        return bridge;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create Python-C++ bridge {}: {}", config.bridgeId, e.what());
        return nullptr;
    }
}

bool GlobalPythonCppBridgeSystem::destroyBridge(const std::string& bridgeId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy bridge
        bool destroyed = bridgeManager_->destroyBridge(bridgeId);
        
        if (destroyed) {
            spdlog::info("Destroyed Python-C++ bridge: {}", bridgeId);
        } else {
            spdlog::error("Failed to destroy Python-C++ bridge: {}", bridgeId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy Python-C++ bridge {}: {}", bridgeId, e.what());
        return false;
    }
}

std::shared_ptr<PythonCppBridge> GlobalPythonCppBridgeSystem::getBridge(const std::string& bridgeId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return bridgeManager_->getBridge(bridgeId);
}

std::string GlobalPythonCppBridgeSystem::registerMemoryPointer(void* address, size_t size, MemoryAccessType accessType) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return "";
    }
    
    try {
        // Register memory pointer
        std::string pointerId = bridgeManager_->registerMemoryPointer(address, size, accessType);
        
        if (!pointerId.empty()) {
            spdlog::info("Memory pointer registered: {}", pointerId);
        } else {
            spdlog::error("Failed to register memory pointer");
        }
        
        return pointerId;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register memory pointer: {}", e.what());
        return "";
    }
}

bool GlobalPythonCppBridgeSystem::unregisterMemoryPointer(const std::string& pointerId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Unregister memory pointer
        bool unregistered = bridgeManager_->unregisterMemoryPointer(pointerId);
        
        if (unregistered) {
            spdlog::info("Memory pointer unregistered: {}", pointerId);
        } else {
            spdlog::error("Failed to unregister memory pointer: {}", pointerId);
        }
        
        return unregistered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister memory pointer {}: {}", pointerId, e.what());
        return false;
    }
}

MemoryPointerInfo GlobalPythonCppBridgeSystem::getMemoryPointerInfo(const std::string& pointerId) const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        MemoryPointerInfo emptyInfo;
        emptyInfo.pointerId = pointerId;
        return emptyInfo;
    }
    
    return bridgeManager_->getMemoryPointerInfo(pointerId);
}

std::string GlobalPythonCppBridgeSystem::registerResource(const ResourceInfo& resourceInfo) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return "";
    }
    
    try {
        // Register resource
        std::string resourceId = bridgeManager_->registerResource(resourceInfo);
        
        if (!resourceId.empty()) {
            spdlog::info("Resource registered: {}", resourceId);
        } else {
            spdlog::error("Failed to register resource");
        }
        
        return resourceId;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register resource: {}", e.what());
        return "";
    }
}

bool GlobalPythonCppBridgeSystem::unregisterResource(const std::string& resourceId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Unregister resource
        bool unregistered = bridgeManager_->unregisterResource(resourceId);
        
        if (unregistered) {
            spdlog::info("Resource unregistered: {}", resourceId);
        } else {
            spdlog::error("Failed to unregister resource: {}", resourceId);
        }
        
        return unregistered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister resource {}: {}", resourceId, e.what());
        return false;
    }
}

ResourceInfo GlobalPythonCppBridgeSystem::getResourceInfo(const std::string& resourceId) const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        ResourceInfo emptyInfo;
        emptyInfo.resourceId = resourceId;
        return emptyInfo;
    }
    
    return bridgeManager_->getResourceInfo(resourceId);
}

std::vector<std::shared_ptr<PythonCppBridge>> GlobalPythonCppBridgeSystem::getAllBridges() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<PythonCppBridge>>();
    }
    
    return bridgeManager_->getAllBridges();
}

std::map<std::string, double> GlobalPythonCppBridgeSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !bridgeManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = bridgeManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalPythonCppBridgeSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to bridge manager
    if (bridgeManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_bridges") != config.end()) {
                int maxBridges = std::stoi(config.at("max_bridges"));
                bridgeManager_->setMaxBridges(maxBridges);
            }
            
            if (config.find("python_path") != config.end()) {
                std::string path = config.at("python_path");
                bridgeManager_->setPythonPath(path);
            }
            
            if (config.find("memory_sharing_strategy") != config.end()) {
                std::string strategy = config.at("memory_sharing_strategy");
                bridgeManager_->setMemorySharingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalPythonCppBridgeSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace bridge
} // namespace cogniware
