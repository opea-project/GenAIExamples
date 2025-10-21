#include "virtualization/virtual_compute_node.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <random>
#include <sstream>

namespace cogniware {
namespace virtualization {

AdvancedVirtualComputeNode::AdvancedVirtualComputeNode(const VirtualNodeConfig& config)
    : config_(config)
    , status_(NodeStatus::CREATING)
    , initialized_(false)
    , resourceAllocated_(false)
    , priority_(config.priority)
    , allocatedMemory_(0)
    , allocatedCores_(0)
    , allocatedTensorCores_(0)
    , nodeStream_(nullptr)
    , deviceMemory_(nullptr)
    , deviceMemorySize_(0)
    , profilingEnabled_(false) {
    
    spdlog::info("Creating virtual compute node: {}", config_.nodeId);
}

AdvancedVirtualComputeNode::~AdvancedVirtualComputeNode() {
    shutdown();
}

bool AdvancedVirtualComputeNode::initialize() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (initialized_) {
        spdlog::warn("Virtual compute node {} already initialized", config_.nodeId);
        return true;
    }
    
    try {
        // Initialize CUDA
        if (!initializeCUDA()) {
            spdlog::error("Failed to initialize CUDA for node {}", config_.nodeId);
            return false;
        }
        
        // Allocate device memory
        if (!allocateDeviceMemory(config_.memorySize)) {
            spdlog::error("Failed to allocate device memory for node {}", config_.nodeId);
            return false;
        }
        
        // Initialize performance metrics
        performanceMetrics_["utilization"] = 0.0;
        performanceMetrics_["memory_usage"] = 0.0;
        performanceMetrics_["core_usage"] = 0.0;
        performanceMetrics_["tensor_core_usage"] = 0.0;
        performanceMetrics_["task_count"] = 0.0;
        lastUpdateTime_ = std::chrono::system_clock::now();
        
        status_ = NodeStatus::ACTIVE;
        initialized_ = true;
        
        spdlog::info("Virtual compute node {} initialized successfully", config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize virtual compute node {}: {}", config_.nodeId, e.what());
        status_ = NodeStatus::ERROR;
        return false;
    }
}

void AdvancedVirtualComputeNode::shutdown() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Cancel all active tasks
        for (const auto& task : activeTasks_) {
            cancelTask(task.first);
        }
        
        // Wait for tasks to complete
        for (auto& task : activeTasks_) {
            if (task.second.joinable()) {
                task.second.join();
            }
        }
        activeTasks_.clear();
        
        // Deallocate device memory
        deallocateDeviceMemory();
        
        // Shutdown CUDA
        shutdownCUDA();
        
        status_ = NodeStatus::DESTROYED;
        initialized_ = false;
        
        spdlog::info("Virtual compute node {} shutdown completed", config_.nodeId);
        
    } catch (const std::exception& e) {
        spdlog::error("Error during virtual compute node {} shutdown: {}", config_.nodeId, e.what());
    }
}

bool AdvancedVirtualComputeNode::isInitialized() const {
    return initialized_;
}

std::string AdvancedVirtualComputeNode::getNodeId() const {
    return config_.nodeId;
}

VirtualNodeType AdvancedVirtualComputeNode::getNodeType() const {
    return config_.type;
}

NodeStatus AdvancedVirtualComputeNode::getStatus() const {
    return status_;
}

VirtualNodeConfig AdvancedVirtualComputeNode::getConfig() const {
    return config_;
}

bool AdvancedVirtualComputeNode::allocateResources(const ResourceAllocationRequest& request) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Node {} not initialized", config_.nodeId);
        return false;
    }
    
    if (resourceAllocated_) {
        spdlog::warn("Node {} already has resources allocated", config_.nodeId);
        return false;
    }
    
    try {
        // Validate allocation request
        if (!validateAllocation(request)) {
            spdlog::error("Invalid allocation request for node {}", config_.nodeId);
            return false;
        }
        
        // Allocate resources
        allocatedMemory_ = std::min(request.requestedMemory, config_.memorySize);
        allocatedCores_ = std::min(request.requestedCores, config_.computeCores);
        allocatedTensorCores_ = std::min(request.requestedTensorCores, config_.tensorCores);
        ownerLLM_ = request.llmId;
        
        resourceAllocated_ = true;
        config_.lastUsed = std::chrono::system_clock::now();
        
        spdlog::info("Allocated resources for node {}: {}MB memory, {} cores, {} tensor cores", 
                    config_.nodeId, allocatedMemory_ / (1024 * 1024), allocatedCores_, allocatedTensorCores_);
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate resources for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::deallocateResources() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Node {} not initialized", config_.nodeId);
        return false;
    }
    
    if (!resourceAllocated_) {
        spdlog::warn("Node {} has no resources allocated", config_.nodeId);
        return true;
    }
    
    try {
        // Cancel all active tasks
        for (const auto& task : activeTasks_) {
            cancelTask(task.first);
        }
        
        // Deallocate resources
        allocatedMemory_ = 0;
        allocatedCores_ = 0;
        allocatedTensorCores_ = 0;
        ownerLLM_.clear();
        
        resourceAllocated_ = false;
        
        spdlog::info("Deallocated resources for node {}", config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate resources for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::isResourceAllocated() const {
    return resourceAllocated_;
}

size_t AdvancedVirtualComputeNode::getAvailableMemory() const {
    return config_.memorySize - allocatedMemory_;
}

size_t AdvancedVirtualComputeNode::getAvailableCores() const {
    return config_.computeCores - allocatedCores_;
}

size_t AdvancedVirtualComputeNode::getAvailableTensorCores() const {
    return config_.tensorCores - allocatedTensorCores_;
}

bool AdvancedVirtualComputeNode::executeTask(const std::string& taskId, const std::function<void()>& task) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Node {} not initialized", config_.nodeId);
        return false;
    }
    
    if (activeTasks_.find(taskId) != activeTasks_.end()) {
        spdlog::warn("Task {} already running on node {}", taskId, config_.nodeId);
        return false;
    }
    
    try {
        // Execute task in separate thread
        bool success = executeTaskInternal(taskId, task);
        
        if (success) {
            spdlog::info("Task {} started on node {}", taskId, config_.nodeId);
        } else {
            spdlog::error("Failed to start task {} on node {}", taskId, config_.nodeId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute task {} on node {}: {}", taskId, config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::cancelTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (activeTasks_.find(taskId) == activeTasks_.end()) {
        spdlog::warn("Task {} not found on node {}", taskId, config_.nodeId);
        return false;
    }
    
    try {
        // Mark task as cancelled
        taskCancelled_[taskId] = true;
        
        // Wait for task to complete
        if (activeTasks_[taskId].joinable()) {
            activeTasks_[taskId].join();
        }
        
        // Cleanup task
        cleanupTask(taskId);
        
        spdlog::info("Task {} cancelled on node {}", taskId, config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel task {} on node {}: {}", taskId, config_.nodeId, e.what());
        return false;
    }
}

std::vector<std::string> AdvancedVirtualComputeNode::getActiveTasks() const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    std::vector<std::string> activeTaskIds;
    for (const auto& task : activeTasks_) {
        activeTaskIds.push_back(task.first);
    }
    return activeTaskIds;
}

bool AdvancedVirtualComputeNode::isTaskRunning(const std::string& taskId) const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    return activeTasks_.find(taskId) != activeTasks_.end();
}

std::map<std::string, double> AdvancedVirtualComputeNode::getPerformanceMetrics() const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    return performanceMetrics_;
}

float AdvancedVirtualComputeNode::getUtilization() const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (config_.memorySize == 0 || config_.computeCores == 0) {
        return 0.0f;
    }
    
    float memoryUtilization = static_cast<float>(allocatedMemory_) / config_.memorySize;
    float coreUtilization = static_cast<float>(allocatedCores_) / config_.computeCores;
    
    return (memoryUtilization + coreUtilization) / 2.0f;
}

bool AdvancedVirtualComputeNode::enableProfiling() {
    profilingEnabled_ = true;
    spdlog::info("Profiling enabled for node {}", config_.nodeId);
    return true;
}

bool AdvancedVirtualComputeNode::disableProfiling() {
    profilingEnabled_ = false;
    spdlog::info("Profiling disabled for node {}", config_.nodeId);
    return true;
}

std::map<std::string, double> AdvancedVirtualComputeNode::getProfilingData() const {
    std::map<std::string, double> profilingData;
    
    if (!profilingEnabled_) {
        return profilingData;
    }
    
    try {
        // Collect profiling data
        auto metrics = getPerformanceMetrics();
        profilingData["utilization"] = metrics.at("utilization");
        profilingData["memory_usage"] = metrics.at("memory_usage");
        profilingData["core_usage"] = metrics.at("core_usage");
        profilingData["tensor_core_usage"] = metrics.at("tensor_core_usage");
        profilingData["task_count"] = metrics.at("task_count");
        profilingData["available_memory"] = static_cast<double>(getAvailableMemory());
        profilingData["available_cores"] = static_cast<double>(getAvailableCores());
        profilingData["available_tensor_cores"] = static_cast<double>(getAvailableTensorCores());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get profiling data for node {}: {}", config_.nodeId, e.what());
    }
    
    return profilingData;
}

bool AdvancedVirtualComputeNode::updateConfig(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Node {} not initialized", config_.nodeId);
        return false;
    }
    
    try {
        // Update configuration
        config_ = config;
        priority_ = config.priority;
        
        spdlog::info("Configuration updated for node {}", config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update configuration for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::setPriority(float priority) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (priority < 0.0f || priority > 1.0f) {
        spdlog::error("Invalid priority {} for node {}", priority, config_.nodeId);
        return false;
    }
    
    priority_ = priority;
    config_.priority = priority;
    
    spdlog::info("Priority set to {} for node {}", priority, config_.nodeId);
    return true;
}

float AdvancedVirtualComputeNode::getPriority() const {
    return priority_;
}

bool AdvancedVirtualComputeNode::suspend() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::ACTIVE) {
        spdlog::warn("Node {} is not active, cannot suspend", config_.nodeId);
        return false;
    }
    
    status_ = NodeStatus::SUSPENDED;
    spdlog::info("Node {} suspended", config_.nodeId);
    return true;
}

bool AdvancedVirtualComputeNode::resume() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::SUSPENDED) {
        spdlog::warn("Node {} is not suspended, cannot resume", config_.nodeId);
        return false;
    }
    
    status_ = NodeStatus::ACTIVE;
    spdlog::info("Node {} resumed", config_.nodeId);
    return true;
}

bool AdvancedVirtualComputeNode::migrate(const std::string& targetNodeId) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::ACTIVE) {
        spdlog::warn("Node {} is not active, cannot migrate", config_.nodeId);
        return false;
    }
    
    // Simulate migration
    spdlog::info("Node {} migrated to {}", config_.nodeId, targetNodeId);
    return true;
}

bool AdvancedVirtualComputeNode::clone(const std::string& newNodeId) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::ACTIVE) {
        spdlog::warn("Node {} is not active, cannot clone", config_.nodeId);
        return false;
    }
    
    // Simulate cloning
    spdlog::info("Node {} cloned to {}", config_.nodeId, newNodeId);
    return true;
}

bool AdvancedVirtualComputeNode::scale(size_t newMemorySize, size_t newCores, size_t newTensorCores) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::ACTIVE) {
        spdlog::warn("Node {} is not active, cannot scale", config_.nodeId);
        return false;
    }
    
    try {
        // Update configuration
        config_.memorySize = newMemorySize;
        config_.computeCores = newCores;
        config_.tensorCores = newTensorCores;
        
        // Reallocate device memory if needed
        if (newMemorySize > deviceMemorySize_) {
            deallocateDeviceMemory();
            if (!allocateDeviceMemory(newMemorySize)) {
                spdlog::error("Failed to allocate new device memory for node {}", config_.nodeId);
                return false;
            }
        }
        
        spdlog::info("Node {} scaled to {}MB memory, {} cores, {} tensor cores", 
                    config_.nodeId, newMemorySize / (1024 * 1024), newCores, newTensorCores);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::optimize() {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (status_ != NodeStatus::ACTIVE) {
        spdlog::warn("Node {} is not active, cannot optimize", config_.nodeId);
        return false;
    }
    
    try {
        // Update performance metrics
        updatePerformanceMetrics();
        
        spdlog::info("Node {} optimized", config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedVirtualComputeNode::getResourceInfo() const {
    std::map<std::string, std::string> info;
    
    info["node_id"] = config_.nodeId;
    info["node_type"] = std::to_string(static_cast<int>(config_.type));
    info["status"] = std::to_string(static_cast<int>(status_));
    info["total_memory"] = std::to_string(config_.memorySize);
    info["allocated_memory"] = std::to_string(allocatedMemory_);
    info["available_memory"] = std::to_string(getAvailableMemory());
    info["total_cores"] = std::to_string(config_.computeCores);
    info["allocated_cores"] = std::to_string(allocatedCores_);
    info["available_cores"] = std::to_string(getAvailableCores());
    info["total_tensor_cores"] = std::to_string(config_.tensorCores);
    info["allocated_tensor_cores"] = std::to_string(allocatedTensorCores_);
    info["available_tensor_cores"] = std::to_string(getAvailableTensorCores());
    info["priority"] = std::to_string(priority_);
    info["owner_llm"] = ownerLLM_;
    info["utilization"] = std::to_string(getUtilization());
    
    return info;
}

bool AdvancedVirtualComputeNode::validateResources() const {
    try {
        // Validate memory allocation
        if (allocatedMemory_ > config_.memorySize) {
            spdlog::error("Node {} has more allocated memory than total", config_.nodeId);
            return false;
        }
        
        // Validate core allocation
        if (allocatedCores_ > config_.computeCores) {
            spdlog::error("Node {} has more allocated cores than total", config_.nodeId);
            return false;
        }
        
        // Validate tensor core allocation
        if (allocatedTensorCores_ > config_.tensorCores) {
            spdlog::error("Node {} has more allocated tensor cores than total", config_.nodeId);
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate resources for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

bool AdvancedVirtualComputeNode::initializeCUDA() {
    try {
        // Create CUDA stream
        cudaError_t cudaError = cudaStreamCreate(&nodeStream_);
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to create CUDA stream for node {}: {}", config_.nodeId, cudaGetErrorString(cudaError));
            return false;
        }
        
        spdlog::debug("CUDA stream created for node {}", config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize CUDA for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

void AdvancedVirtualComputeNode::shutdownCUDA() {
    try {
        if (nodeStream_) {
            cudaStreamDestroy(nodeStream_);
            nodeStream_ = nullptr;
        }
        
        spdlog::debug("CUDA stream destroyed for node {}", config_.nodeId);
        
    } catch (const std::exception& e) {
        spdlog::error("Error during CUDA shutdown for node {}: {}", config_.nodeId, e.what());
    }
}

bool AdvancedVirtualComputeNode::allocateDeviceMemory(size_t size) {
    try {
        cudaError_t cudaError = cudaMalloc(&deviceMemory_, size);
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to allocate device memory for node {}: {}", config_.nodeId, cudaGetErrorString(cudaError));
            return false;
        }
        
        deviceMemorySize_ = size;
        spdlog::debug("Allocated {}MB device memory for node {}", size / (1024 * 1024), config_.nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate device memory for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

void AdvancedVirtualComputeNode::deallocateDeviceMemory() {
    try {
        if (deviceMemory_) {
            cudaFree(deviceMemory_);
            deviceMemory_ = nullptr;
            deviceMemorySize_ = 0;
        }
        
        spdlog::debug("Deallocated device memory for node {}", config_.nodeId);
        
    } catch (const std::exception& e) {
        spdlog::error("Error during device memory deallocation for node {}: {}", config_.nodeId, e.what());
    }
}

bool AdvancedVirtualComputeNode::validateAllocation(const ResourceAllocationRequest& request) {
    try {
        // Check if node has enough resources
        if (request.requestedMemory > getAvailableMemory()) {
            spdlog::warn("Node {} has insufficient memory for request", config_.nodeId);
            return false;
        }
        
        if (request.requestedCores > getAvailableCores()) {
            spdlog::warn("Node {} has insufficient cores for request", config_.nodeId);
            return false;
        }
        
        if (request.requestedTensorCores > getAvailableTensorCores()) {
            spdlog::warn("Node {} has insufficient tensor cores for request", config_.nodeId);
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate allocation for node {}: {}", config_.nodeId, e.what());
        return false;
    }
}

void AdvancedVirtualComputeNode::updatePerformanceMetrics() {
    try {
        auto now = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(now - lastUpdateTime_);
        
        // Update metrics
        performanceMetrics_["utilization"] = getUtilization();
        performanceMetrics_["memory_usage"] = static_cast<double>(allocatedMemory_) / config_.memorySize;
        performanceMetrics_["core_usage"] = static_cast<double>(allocatedCores_) / config_.computeCores;
        performanceMetrics_["tensor_core_usage"] = static_cast<double>(allocatedTensorCores_) / config_.tensorCores;
        performanceMetrics_["task_count"] = static_cast<double>(activeTasks_.size());
        performanceMetrics_["update_duration_ms"] = static_cast<double>(duration.count());
        
        lastUpdateTime_ = now;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update performance metrics for node {}: {}", config_.nodeId, e.what());
    }
}

bool AdvancedVirtualComputeNode::executeTaskInternal(const std::string& taskId, const std::function<void()>& task) {
    try {
        // Create task cancellation flag
        taskCancelled_[taskId] = false;
        
        // Execute task in separate thread
        activeTasks_[taskId] = std::thread([this, taskId, task]() {
            try {
                // Check if task was cancelled before starting
                if (taskCancelled_[taskId]) {
                    return;
                }
                
                // Execute task
                task();
                
                // Cleanup task
                cleanupTask(taskId);
                
            } catch (const std::exception& e) {
                spdlog::error("Task {} failed on node {}: {}", taskId, config_.nodeId, e.what());
                cleanupTask(taskId);
            }
        });
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute task {} on node {}: {}", taskId, config_.nodeId, e.what());
        return false;
    }
}

void AdvancedVirtualComputeNode::cleanupTask(const std::string& taskId) {
    try {
        // Remove task from active tasks
        if (activeTasks_.find(taskId) != activeTasks_.end()) {
            if (activeTasks_[taskId].joinable()) {
                activeTasks_[taskId].join();
            }
            activeTasks_.erase(taskId);
        }
        
        // Remove cancellation flag
        taskCancelled_.erase(taskId);
        
        spdlog::debug("Task {} cleaned up on node {}", taskId, config_.nodeId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup task {} on node {}: {}", taskId, config_.nodeId, e.what());
    }
}

} // namespace virtualization
} // namespace cogniware
