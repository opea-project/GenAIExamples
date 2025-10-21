#include "virtualization/virtual_compute_node.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <random>
#include <sstream>

namespace cogniware {
namespace virtualization {

VirtualComputeNodeManager::VirtualComputeNodeManager()
    : initialized_(false)
    , allocationStrategy_(AllocationStrategy::DYNAMIC)
    , maxNodes_(100)
    , maxMemory_(1024 * 1024 * 1024 * 16) // 16GB
    , maxCores_(1024)
    , maxTensorCores_(512)
    , totalAllocatedMemory_(0)
    , totalAllocatedCores_(0)
    , totalAllocatedTensorCores_(0)
    , systemProfilingEnabled_(false) {
    
    spdlog::info("VirtualComputeNodeManager initialized");
}

VirtualComputeNodeManager::~VirtualComputeNodeManager() {
    shutdown();
}

bool VirtualComputeNodeManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Virtual compute node manager already initialized");
        return true;
    }
    
    try {
        // Initialize system
        nodes_.clear();
        totalAllocatedMemory_ = 0;
        totalAllocatedCores_ = 0;
        totalAllocatedTensorCores_ = 0;
        
        initialized_ = true;
        spdlog::info("VirtualComputeNodeManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize virtual compute node manager: {}", e.what());
        return false;
    }
}

void VirtualComputeNodeManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Destroy all nodes
        for (auto& node : nodes_) {
            if (node.second) {
                node.second->shutdown();
            }
        }
        nodes_.clear();
        
        initialized_ = false;
        spdlog::info("VirtualComputeNodeManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during virtual compute node manager shutdown: {}", e.what());
    }
}

bool VirtualComputeNodeManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<VirtualComputeNode> VirtualComputeNodeManager::createNode(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        // Validate node creation
        if (!validateNodeCreation(config)) {
            spdlog::error("Invalid node configuration");
            return nullptr;
        }
        
        // Check if node already exists
        if (nodes_.find(config.nodeId) != nodes_.end()) {
            spdlog::error("Node {} already exists", config.nodeId);
            return nullptr;
        }
        
        // Check node limits
        if (static_cast<int>(nodes_.size()) >= maxNodes_) {
            spdlog::error("Maximum number of nodes ({}) reached", maxNodes_);
            return nullptr;
        }
        
        // Create node
        auto node = std::make_shared<AdvancedVirtualComputeNode>(config);
        if (!node->initialize()) {
            spdlog::error("Failed to initialize node {}", config.nodeId);
            return nullptr;
        }
        
        // Add to manager
        nodes_[config.nodeId] = node;
        
        spdlog::info("Created virtual compute node: {}", config.nodeId);
        return node;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create node {}: {}", config.nodeId, e.what());
        return nullptr;
    }
}

bool VirtualComputeNodeManager::destroyNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Find node
        auto it = nodes_.find(nodeId);
        if (it == nodes_.end()) {
            spdlog::error("Node {} not found", nodeId);
            return false;
        }
        
        // Shutdown node
        if (it->second) {
            it->second->shutdown();
        }
        
        // Remove from manager
        nodes_.erase(it);
        
        spdlog::info("Destroyed virtual compute node: {}", nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy node {}: {}", nodeId, e.what());
        return false;
    }
}

std::shared_ptr<VirtualComputeNode> VirtualComputeNodeManager::getNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = nodes_.find(nodeId);
    if (it != nodes_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<VirtualComputeNode>> VirtualComputeNodeManager::getAllNodes() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<VirtualComputeNode>> allNodes;
    for (const auto& node : nodes_) {
        allNodes.push_back(node.second);
    }
    return allNodes;
}

std::vector<std::shared_ptr<VirtualComputeNode>> VirtualComputeNodeManager::getNodesByType(VirtualNodeType type) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<VirtualComputeNode>> nodesByType;
    for (const auto& node : nodes_) {
        if (node.second && node.second->getNodeType() == type) {
            nodesByType.push_back(node.second);
        }
    }
    return nodesByType;
}

std::vector<std::shared_ptr<VirtualComputeNode>> VirtualComputeNodeManager::getNodesByOwner(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<VirtualComputeNode>> nodesByOwner;
    for (const auto& node : nodes_) {
        if (node.second && node.second->isResourceAllocated()) {
            // Check if node is owned by this LLM
            auto config = node.second->getConfig();
            if (config.ownerLLM == llmId) {
                nodesByOwner.push_back(node.second);
            }
        }
    }
    return nodesByOwner;
}

ResourceAllocationResponse VirtualComputeNodeManager::allocateResources(const ResourceAllocationRequest& request) {
    ResourceAllocationResponse response;
    response.requestId = request.requestId;
    response.success = false;
    
    if (!initialized_) {
        response.error = "Manager not initialized";
        return response;
    }
    
    try {
        // Validate allocation request
        if (!validateResourceAllocation(request)) {
            response.error = "Invalid resource allocation request";
            return response;
        }
        
        // Find best node for allocation
        std::string bestNodeId;
        if (!findBestNode(request, bestNodeId)) {
            response.error = "No suitable node found for allocation";
            return response;
        }
        
        // Allocate resources to node
        if (!allocateResourcesToNode(bestNodeId, request)) {
            response.error = "Failed to allocate resources to node";
            return response;
        }
        
        // Get allocated node
        auto node = getNode(bestNodeId);
        if (!node) {
            response.error = "Allocated node not found";
            return response;
        }
        
        // Set response
        response.success = true;
        response.nodeId = bestNodeId;
        response.allocatedMemory = request.requestedMemory;
        response.allocatedCores = request.requestedCores;
        response.allocatedTensorCores = request.requestedTensorCores;
        response.allocatedAt = std::chrono::system_clock::now();
        
        spdlog::info("Allocated resources for request {} to node {}", request.requestId, bestNodeId);
        
    } catch (const std::exception& e) {
        response.error = "Allocation failed: " + std::string(e.what());
        spdlog::error("Failed to allocate resources for request {}: {}", request.requestId, e.what());
    }
    
    return response;
}

bool VirtualComputeNodeManager::deallocateResources(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Get node
        auto node = getNode(nodeId);
        if (!node) {
            spdlog::error("Node {} not found", nodeId);
            return false;
        }
        
        // Deallocate resources
        bool success = node->deallocateResources();
        
        if (success) {
            spdlog::info("Deallocated resources for node {}", nodeId);
        } else {
            spdlog::error("Failed to deallocate resources for node {}", nodeId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate resources for node {}: {}", nodeId, e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::isResourceAvailable(const ResourceAllocationRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return false;
    }
    
    try {
        // Check if any node can satisfy the request
        for (const auto& node : nodes_) {
            if (node.second && !node.second->isResourceAllocated()) {
                if (node.second->getAvailableMemory() >= request.requestedMemory &&
                    node.second->getAvailableCores() >= request.requestedCores &&
                    node.second->getAvailableTensorCores() >= request.requestedTensorCores) {
                    return true;
                }
            }
        }
        
        return false;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check resource availability: {}", e.what());
        return false;
    }
}

std::vector<std::string> VirtualComputeNodeManager::findAvailableNodes(const ResourceAllocationRequest& request) {
    std::vector<std::string> availableNodes;
    
    try {
        for (const auto& node : nodes_) {
            if (node.second && !node.second->isResourceAllocated()) {
                if (node.second->getAvailableMemory() >= request.requestedMemory &&
                    node.second->getAvailableCores() >= request.requestedCores &&
                    node.second->getAvailableTensorCores() >= request.requestedTensorCores) {
                    availableNodes.push_back(node.first);
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find available nodes: {}", e.what());
    }
    
    return availableNodes;
}

bool VirtualComputeNodeManager::suspendNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto node = getNode(nodeId);
    if (!node) {
        spdlog::error("Node {} not found", nodeId);
        return false;
    }
    
    // Cast to advanced node to access suspend method
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    if (!advancedNode) {
        spdlog::error("Node {} is not an advanced node", nodeId);
        return false;
    }
    
    return advancedNode->suspend();
}

bool VirtualComputeNodeManager::resumeNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto node = getNode(nodeId);
    if (!node) {
        spdlog::error("Node {} not found", nodeId);
        return false;
    }
    
    // Cast to advanced node to access resume method
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    if (!advancedNode) {
        spdlog::error("Node {} is not an advanced node", nodeId);
        return false;
    }
    
    return advancedNode->resume();
}

bool VirtualComputeNodeManager::migrateNode(const std::string& nodeId, const std::string& targetNodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto node = getNode(nodeId);
    if (!node) {
        spdlog::error("Node {} not found", nodeId);
        return false;
    }
    
    // Cast to advanced node to access migrate method
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    if (!advancedNode) {
        spdlog::error("Node {} is not an advanced node", nodeId);
        return false;
    }
    
    return advancedNode->migrate(targetNodeId);
}

bool VirtualComputeNodeManager::cloneNode(const std::string& nodeId, const std::string& newNodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto node = getNode(nodeId);
    if (!node) {
        spdlog::error("Node {} not found", nodeId);
        return false;
    }
    
    // Cast to advanced node to access clone method
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    if (!advancedNode) {
        spdlog::error("Node {} is not an advanced node", nodeId);
        return false;
    }
    
    return advancedNode->clone(newNodeId);
}

bool VirtualComputeNodeManager::scaleNode(const std::string& nodeId, size_t newMemorySize, size_t newCores, size_t newTensorCores) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto node = getNode(nodeId);
    if (!node) {
        spdlog::error("Node {} not found", nodeId);
        return false;
    }
    
    // Cast to advanced node to access scale method
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    if (!advancedNode) {
        spdlog::error("Node {} is not an advanced node", nodeId);
        return false;
    }
    
    return advancedNode->scale(newMemorySize, newCores, newTensorCores);
}

bool VirtualComputeNodeManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing virtual compute node system");
        
        // Optimize each node
        for (const auto& node : nodes_) {
            if (node.second) {
                auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node.second);
                if (advancedNode) {
                    advancedNode->optimize();
                }
            }
        }
        
        // Update system metrics
        updateSystemMetrics();
        
        spdlog::info("System optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system: {}", e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::balanceLoad() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing load across virtual compute nodes");
        
        // Get all active nodes
        std::vector<std::shared_ptr<VirtualComputeNode>> activeNodes;
        for (const auto& node : nodes_) {
            if (node.second && node.second->getStatus() == NodeStatus::ACTIVE) {
                activeNodes.push_back(node.second);
            }
        }
        
        if (activeNodes.empty()) {
            spdlog::warn("No active nodes found for load balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& node : activeNodes) {
            totalUtilization += node->getUtilization();
        }
        float averageUtilization = totalUtilization / activeNodes.size();
        
        // Balance load (simplified implementation)
        for (const auto& node : activeNodes) {
            float utilization = node->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                // Node is overloaded, try to redistribute
                spdlog::debug("Node {} is overloaded (utilization: {:.2f})", 
                            node->getNodeId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                // Node is underloaded, can take more work
                spdlog::debug("Node {} is underloaded (utilization: {:.2f})", 
                            node->getNodeId(), utilization);
            }
        }
        
        spdlog::info("Load balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load: {}", e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::cleanupIdleNodes() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up idle virtual compute nodes");
        
        // Find idle nodes
        std::vector<std::string> idleNodes;
        for (const auto& node : nodes_) {
            if (node.second && node.second->getStatus() == NodeStatus::IDLE) {
                idleNodes.push_back(node.first);
            }
        }
        
        // Cleanup idle nodes
        for (const auto& nodeId : idleNodes) {
            spdlog::info("Cleaning up idle node: {}", nodeId);
            cleanupNode(nodeId);
        }
        
        spdlog::info("Cleaned up {} idle nodes", idleNodes.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup idle nodes: {}", e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating virtual compute node system");
        
        bool isValid = true;
        
        // Validate each node
        for (const auto& node : nodes_) {
            if (node.second) {
                auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node.second);
                if (advancedNode && !advancedNode->validateResources()) {
                    spdlog::error("Node {} failed validation", node.first);
                    isValid = false;
                }
            }
        }
        
        // Validate system resources
        if (totalAllocatedMemory_ > maxMemory_) {
            spdlog::error("Total allocated memory exceeds limit");
            isValid = false;
        }
        
        if (totalAllocatedCores_ > maxCores_) {
            spdlog::error("Total allocated cores exceeds limit");
            isValid = false;
        }
        
        if (totalAllocatedTensorCores_ > maxTensorCores_) {
            spdlog::error("Total allocated tensor cores exceeds limit");
            isValid = false;
        }
        
        if (isValid) {
            spdlog::info("System validation passed");
        } else {
            spdlog::error("System validation failed");
        }
        
        return isValid;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate system: {}", e.what());
        return false;
    }
}

std::map<std::string, double> VirtualComputeNodeManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Update system metrics
        updateSystemMetrics();
        
        // Calculate system metrics
        metrics["total_nodes"] = static_cast<double>(nodes_.size());
        metrics["active_nodes"] = 0.0;
        metrics["idle_nodes"] = 0.0;
        metrics["suspended_nodes"] = 0.0;
        metrics["total_memory"] = static_cast<double>(maxMemory_);
        metrics["allocated_memory"] = static_cast<double>(totalAllocatedMemory_);
        metrics["available_memory"] = static_cast<double>(maxMemory_ - totalAllocatedMemory_);
        metrics["total_cores"] = static_cast<double>(maxCores_);
        metrics["allocated_cores"] = static_cast<double>(totalAllocatedCores_);
        metrics["available_cores"] = static_cast<double>(maxCores_ - totalAllocatedCores_);
        metrics["total_tensor_cores"] = static_cast<double>(maxTensorCores_);
        metrics["allocated_tensor_cores"] = static_cast<double>(totalAllocatedTensorCores_);
        metrics["available_tensor_cores"] = static_cast<double>(maxTensorCores_ - totalAllocatedTensorCores_);
        
        // Count nodes by status
        for (const auto& node : nodes_) {
            if (node.second) {
                switch (node.second->getStatus()) {
                    case NodeStatus::ACTIVE:
                        metrics["active_nodes"] += 1.0;
                        break;
                    case NodeStatus::IDLE:
                        metrics["idle_nodes"] += 1.0;
                        break;
                    case NodeStatus::SUSPENDED:
                        metrics["suspended_nodes"] += 1.0;
                        break;
                    default:
                        break;
                }
            }
        }
        
        // Calculate utilization percentages
        if (maxMemory_ > 0) {
            metrics["memory_utilization"] = static_cast<double>(totalAllocatedMemory_) / maxMemory_;
        }
        if (maxCores_ > 0) {
            metrics["core_utilization"] = static_cast<double>(totalAllocatedCores_) / maxCores_;
        }
        if (maxTensorCores_ > 0) {
            metrics["tensor_core_utilization"] = static_cast<double>(totalAllocatedTensorCores_) / maxTensorCores_;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> VirtualComputeNodeManager::getNodeCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(nodes_.size());
        counts["active"] = 0;
        counts["idle"] = 0;
        counts["suspended"] = 0;
        counts["destroyed"] = 0;
        counts["error"] = 0;
        
        for (const auto& node : nodes_) {
            if (node.second) {
                switch (node.second->getStatus()) {
                    case NodeStatus::ACTIVE:
                        counts["active"]++;
                        break;
                    case NodeStatus::IDLE:
                        counts["idle"]++;
                        break;
                    case NodeStatus::SUSPENDED:
                        counts["suspended"]++;
                        break;
                    case NodeStatus::DESTROYED:
                        counts["destroyed"]++;
                        break;
                    case NodeStatus::ERROR:
                        counts["error"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get node counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> VirtualComputeNodeManager::getResourceUtilization() {
    std::map<std::string, double> utilization;
    
    try {
        // Calculate resource utilization
        if (maxMemory_ > 0) {
            utilization["memory"] = static_cast<double>(totalAllocatedMemory_) / maxMemory_;
        }
        if (maxCores_ > 0) {
            utilization["cores"] = static_cast<double>(totalAllocatedCores_) / maxCores_;
        }
        if (maxTensorCores_ > 0) {
            utilization["tensor_cores"] = static_cast<double>(totalAllocatedTensorCores_) / maxTensorCores_;
        }
        
        // Calculate average node utilization
        double totalUtilization = 0.0;
        int nodeCount = 0;
        for (const auto& node : nodes_) {
            if (node.second) {
                totalUtilization += node.second->getUtilization();
                nodeCount++;
            }
        }
        if (nodeCount > 0) {
            utilization["average_node"] = totalUtilization / nodeCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get resource utilization: {}", e.what());
    }
    
    return utilization;
}

bool VirtualComputeNodeManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool VirtualComputeNodeManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> VirtualComputeNodeManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        // Get system metrics
        auto metrics = getSystemMetrics();
        auto utilization = getResourceUtilization();
        
        // Combine metrics and utilization
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(utilization.begin(), utilization.end());
        
        // Add profiling-specific data
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        profilingData["allocation_strategy"] = static_cast<double>(allocationStrategy_);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void VirtualComputeNodeManager::setAllocationStrategy(AllocationStrategy strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    allocationStrategy_ = strategy;
    spdlog::info("Set allocation strategy to: {}", static_cast<int>(strategy));
}

AllocationStrategy VirtualComputeNodeManager::getAllocationStrategy() const {
    return allocationStrategy_;
}

void VirtualComputeNodeManager::setMaxNodes(int maxNodes) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxNodes_ = maxNodes;
    spdlog::info("Set maximum nodes to: {}", maxNodes);
}

int VirtualComputeNodeManager::getMaxNodes() const {
    return maxNodes_;
}

void VirtualComputeNodeManager::setResourceLimits(size_t maxMemory, size_t maxCores, size_t maxTensorCores) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxMemory_ = maxMemory;
    maxCores_ = maxCores;
    maxTensorCores_ = maxTensorCores;
    spdlog::info("Set resource limits: {}MB memory, {} cores, {} tensor cores", 
                maxMemory / (1024 * 1024), maxCores, maxTensorCores);
}

std::map<std::string, size_t> VirtualComputeNodeManager::getResourceLimits() const {
    std::map<std::string, size_t> limits;
    limits["max_memory"] = maxMemory_;
    limits["max_cores"] = maxCores_;
    limits["max_tensor_cores"] = maxTensorCores_;
    return limits;
}

bool VirtualComputeNodeManager::validateNodeCreation(const VirtualNodeConfig& config) {
    try {
        // Validate node ID
        if (config.nodeId.empty()) {
            spdlog::error("Node ID cannot be empty");
            return false;
        }
        
        // Validate memory size
        if (config.memorySize == 0) {
            spdlog::error("Memory size must be greater than 0");
            return false;
        }
        
        // Validate cores
        if (config.computeCores == 0) {
            spdlog::error("Compute cores must be greater than 0");
            return false;
        }
        
        // Validate priority
        if (config.priority < 0.0f || config.priority > 1.0f) {
            spdlog::error("Priority must be between 0.0 and 1.0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate node creation: {}", e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::validateResourceAllocation(const ResourceAllocationRequest& request) {
    try {
        // Validate request ID
        if (request.requestId.empty()) {
            spdlog::error("Request ID cannot be empty");
            return false;
        }
        
        // Validate LLM ID
        if (request.llmId.empty()) {
            spdlog::error("LLM ID cannot be empty");
            return false;
        }
        
        // Validate memory request
        if (request.requestedMemory == 0) {
            spdlog::error("Requested memory must be greater than 0");
            return false;
        }
        
        // Validate cores request
        if (request.requestedCores == 0) {
            spdlog::error("Requested cores must be greater than 0");
            return false;
        }
        
        // Validate priority
        if (request.priority < 0.0f || request.priority > 1.0f) {
            spdlog::error("Request priority must be between 0.0 and 1.0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate resource allocation: {}", e.what());
        return false;
    }
}

std::string VirtualComputeNodeManager::generateNodeId() {
    try {
        // Generate unique node ID
        std::stringstream ss;
        ss << "node_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate node ID: {}", e.what());
        return "node_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool VirtualComputeNodeManager::cleanupNode(const std::string& nodeId) {
    try {
        // Get node
        auto node = getNode(nodeId);
        if (!node) {
            spdlog::error("Node {} not found for cleanup", nodeId);
            return false;
        }
        
        // Shutdown node
        node->shutdown();
        
        // Remove from manager
        nodes_.erase(nodeId);
        
        spdlog::info("Cleaned up node: {}", nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup node {}: {}", nodeId, e.what());
        return false;
    }
}

void VirtualComputeNodeManager::updateSystemMetrics() {
    try {
        // Reset counters
        totalAllocatedMemory_ = 0;
        totalAllocatedCores_ = 0;
        totalAllocatedTensorCores_ = 0;
        
        // Update counters
        for (const auto& node : nodes_) {
            if (node.second && node.second->isResourceAllocated()) {
                totalAllocatedMemory_ += node.second->getConfig().memorySize;
                totalAllocatedCores_ += node.second->getConfig().computeCores;
                totalAllocatedTensorCores_ += node.second->getConfig().tensorCores;
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool VirtualComputeNodeManager::findBestNode(const ResourceAllocationRequest& request, std::string& bestNodeId) {
    try {
        // Find nodes that can satisfy the request
        std::vector<std::string> availableNodes = findAvailableNodes(request);
        
        if (availableNodes.empty()) {
            spdlog::warn("No available nodes found for request {}", request.requestId);
            return false;
        }
        
        // Select best node based on allocation strategy
        switch (allocationStrategy_) {
            case AllocationStrategy::STATIC:
                // Select first available node
                bestNodeId = availableNodes[0];
                break;
                
            case AllocationStrategy::DYNAMIC:
                // Select node with best resource fit
                bestNodeId = availableNodes[0];
                for (const auto& nodeId : availableNodes) {
                    auto node = getNode(nodeId);
                    if (node) {
                        // Prefer node with closest resource match
                        size_t currentFit = node->getAvailableMemory() + node->getAvailableCores() + node->getAvailableTensorCores();
                        size_t bestFit = getNode(bestNodeId)->getAvailableMemory() + 
                                       getNode(bestNodeId)->getAvailableCores() + 
                                       getNode(bestNodeId)->getAvailableTensorCores();
                        if (currentFit < bestFit) {
                            bestNodeId = nodeId;
                        }
                    }
                }
                break;
                
            case AllocationStrategy::ADAPTIVE:
                // Select node with lowest utilization
                bestNodeId = availableNodes[0];
                float bestUtilization = getNode(bestNodeId)->getUtilization();
                for (const auto& nodeId : availableNodes) {
                    auto node = getNode(nodeId);
                    if (node) {
                        float utilization = node->getUtilization();
                        if (utilization < bestUtilization) {
                            bestNodeId = nodeId;
                            bestUtilization = utilization;
                        }
                    }
                }
                break;
                
            case AllocationStrategy::PREDICTIVE:
                // Select node based on predicted performance
                bestNodeId = availableNodes[0];
                // Simplified prediction based on available resources
                break;
                
            case AllocationStrategy::ON_DEMAND:
                // Select node that can be created on demand
                // For now, select first available node
                bestNodeId = availableNodes[0];
                break;
                
            default:
                bestNodeId = availableNodes[0];
                break;
        }
        
        spdlog::debug("Selected best node {} for request {}", bestNodeId, request.requestId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best node: {}", e.what());
        return false;
    }
}

bool VirtualComputeNodeManager::allocateResourcesToNode(const std::string& nodeId, const ResourceAllocationRequest& request) {
    try {
        // Get node
        auto node = getNode(nodeId);
        if (!node) {
            spdlog::error("Node {} not found for allocation", nodeId);
            return false;
        }
        
        // Allocate resources
        bool success = node->allocateResources(request);
        
        if (success) {
            spdlog::info("Allocated resources to node {} for request {}", nodeId, request.requestId);
        } else {
            spdlog::error("Failed to allocate resources to node {} for request {}", nodeId, request.requestId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate resources to node {}: {}", nodeId, e.what());
        return false;
    }
}

} // namespace virtualization
} // namespace cogniware
