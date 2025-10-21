#include "virtualization/virtual_compute_node.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace virtualization {

GlobalVirtualComputeNodeSystem& GlobalVirtualComputeNodeSystem::getInstance() {
    static GlobalVirtualComputeNodeSystem instance;
    return instance;
}

GlobalVirtualComputeNodeSystem::GlobalVirtualComputeNodeSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalVirtualComputeNodeSystem singleton created");
}

GlobalVirtualComputeNodeSystem::~GlobalVirtualComputeNodeSystem() {
    shutdown();
}

bool GlobalVirtualComputeNodeSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global virtual compute node system already initialized");
        return true;
    }
    
    try {
        // Initialize node manager
        nodeManager_ = std::make_shared<VirtualComputeNodeManager>();
        if (!nodeManager_->initialize()) {
            spdlog::error("Failed to initialize virtual compute node manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_nodes"] = "100";
        configuration_["max_memory"] = "17179869184"; // 16GB
        configuration_["max_cores"] = "1024";
        configuration_["max_tensor_cores"] = "512";
        configuration_["allocation_strategy"] = "dynamic";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["load_balancing"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalVirtualComputeNodeSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global virtual compute node system: {}", e.what());
        return false;
    }
}

void GlobalVirtualComputeNodeSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown node manager
        if (nodeManager_) {
            nodeManager_->shutdown();
            nodeManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalVirtualComputeNodeSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global virtual compute node system shutdown: {}", e.what());
    }
}

bool GlobalVirtualComputeNodeSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<VirtualComputeNodeManager> GlobalVirtualComputeNodeSystem::getNodeManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return nodeManager_;
}

std::shared_ptr<VirtualComputeNode> GlobalVirtualComputeNodeSystem::createNode(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create node
        auto node = nodeManager_->createNode(config);
        
        if (node) {
            spdlog::info("Created virtual compute node: {}", config.nodeId);
        } else {
            spdlog::error("Failed to create virtual compute node: {}", config.nodeId);
        }
        
        return node;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create node {}: {}", config.nodeId, e.what());
        return nullptr;
    }
}

bool GlobalVirtualComputeNodeSystem::destroyNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy node
        bool success = nodeManager_->destroyNode(nodeId);
        
        if (success) {
            spdlog::info("Destroyed virtual compute node: {}", nodeId);
        } else {
            spdlog::error("Failed to destroy virtual compute node: {}", nodeId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy node {}: {}", nodeId, e.what());
        return false;
    }
}

std::shared_ptr<VirtualComputeNode> GlobalVirtualComputeNodeSystem::getNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return nodeManager_->getNode(nodeId);
}

ResourceAllocationResponse GlobalVirtualComputeNodeSystem::allocateResources(const ResourceAllocationRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        ResourceAllocationResponse response;
        response.requestId = request.requestId;
        response.success = false;
        response.error = "System not initialized";
        return response;
    }
    
    try {
        // Allocate resources
        auto response = nodeManager_->allocateResources(request);
        
        if (response.success) {
            spdlog::info("Allocated resources for request {} to node {}", request.requestId, response.nodeId);
        } else {
            spdlog::error("Failed to allocate resources for request {}: {}", request.requestId, response.error);
        }
        
        return response;
        
    } catch (const std::exception& e) {
        ResourceAllocationResponse response;
        response.requestId = request.requestId;
        response.success = false;
        response.error = "Allocation failed: " + std::string(e.what());
        spdlog::error("Failed to allocate resources for request {}: {}", request.requestId, e.what());
        return response;
    }
}

bool GlobalVirtualComputeNodeSystem::deallocateResources(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Deallocate resources
        bool success = nodeManager_->deallocateResources(nodeId);
        
        if (success) {
            spdlog::info("Deallocated resources for node: {}", nodeId);
        } else {
            spdlog::error("Failed to deallocate resources for node: {}", nodeId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate resources for node {}: {}", nodeId, e.what());
        return false;
    }
}

std::vector<std::shared_ptr<VirtualComputeNode>> GlobalVirtualComputeNodeSystem::getAllNodes() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<VirtualComputeNode>>();
    }
    
    return nodeManager_->getAllNodes();
}

std::map<std::string, double> GlobalVirtualComputeNodeSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !nodeManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = nodeManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalVirtualComputeNodeSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to node manager
    if (nodeManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_nodes") != config.end()) {
                int maxNodes = std::stoi(config.at("max_nodes"));
                nodeManager_->setMaxNodes(maxNodes);
            }
            
            if (config.find("max_memory") != config.end() && 
                config.find("max_cores") != config.end() && 
                config.find("max_tensor_cores") != config.end()) {
                size_t maxMemory = std::stoull(config.at("max_memory"));
                size_t maxCores = std::stoull(config.at("max_cores"));
                size_t maxTensorCores = std::stoull(config.at("max_tensor_cores"));
                nodeManager_->setResourceLimits(maxMemory, maxCores, maxTensorCores);
            }
            
            if (config.find("allocation_strategy") != config.end()) {
                std::string strategy = config.at("allocation_strategy");
                AllocationStrategy allocationStrategy;
                if (strategy == "static") {
                    allocationStrategy = AllocationStrategy::STATIC;
                } else if (strategy == "dynamic") {
                    allocationStrategy = AllocationStrategy::DYNAMIC;
                } else if (strategy == "adaptive") {
                    allocationStrategy = AllocationStrategy::ADAPTIVE;
                } else if (strategy == "predictive") {
                    allocationStrategy = AllocationStrategy::PREDICTIVE;
                } else if (strategy == "on_demand") {
                    allocationStrategy = AllocationStrategy::ON_DEMAND;
                } else {
                    allocationStrategy = AllocationStrategy::DYNAMIC;
                }
                nodeManager_->setAllocationStrategy(allocationStrategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalVirtualComputeNodeSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace virtualization
} // namespace cogniware
