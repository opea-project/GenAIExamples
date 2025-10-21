#include "core/python_cpp_bridge.h"
#include <spdlog/spdlog.h>
#include <cstring>
#include <algorithm>

namespace cogniware {
namespace core {

AdvancedPythonCppBridge::AdvancedPythonCppBridge()
    : initialized_(false) {
    
    spdlog::info("AdvancedPythonCppBridge initialized");
}

AdvancedPythonCppBridge::~AdvancedPythonCppBridge() {
    shutdown();
}

bool AdvancedPythonCppBridge::initialize() {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (initialized_) {
        spdlog::warn("Bridge already initialized");
        return true;
    }
    
    try {
        // Initialize kernel
        kernel_ = std::make_shared<AdvancedCustomizedKernel>();
        if (!kernel_->initialize()) {
            spdlog::error("Failed to initialize kernel");
            return false;
        }
        
        initialized_ = true;
        spdlog::info("AdvancedPythonCppBridge initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize bridge: {}", e.what());
        return false;
    }
}

void AdvancedPythonCppBridge::shutdown() {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Cleanup all LLM resources
        for (const auto& pair : llmConfigs_) {
            cleanupLLMResources(pair.first);
        }
        
        // Shutdown kernel
        if (kernel_) {
            kernel_->shutdown();
            kernel_.reset();
        }
        
        // Clear all data structures
        llmMemoryArrays_.clear();
        llmConfigs_.clear();
        llmTasks_.clear();
        llmProfiling_.clear();
        
        initialized_ = false;
        spdlog::info("AdvancedPythonCppBridge shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during bridge shutdown: {}", e.what());
    }
}

bool AdvancedPythonCppBridge::isInitialized() const {
    return initialized_;
}

pybind11::array_t<float> AdvancedPythonCppBridge::allocateMemoryArray(size_t size, const std::string& llmId) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        spdlog::error("Bridge not initialized");
        return pybind11::array_t<float>();
    }
    
    try {
        // Create numpy array
        pybind11::array_t<float> array(size);
        
        // Store array for this LLM
        llmMemoryArrays_[llmId] = array;
        
        spdlog::info("Allocated memory array of size {} for LLM {}", size, llmId);
        return array;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate memory array for LLM {}: {}", llmId, e.what());
        return pybind11::array_t<float>();
    }
}

bool AdvancedPythonCppBridge::deallocateMemoryArray(pybind11::array_t<float> array, const std::string& llmId) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        spdlog::error("Bridge not initialized");
        return false;
    }
    
    try {
        // Find and remove array from LLM's memory arrays
        auto it = llmMemoryArrays_.find(llmId);
        if (it != llmMemoryArrays_.end()) {
            llmMemoryArrays_.erase(it);
            spdlog::info("Deallocated memory array for LLM {}", llmId);
            return true;
        }
        
        spdlog::error("Memory array not found for LLM {}", llmId);
        return false;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate memory array for LLM {}: {}", llmId, e.what());
        return false;
    }
}

void* AdvancedPythonCppBridge::getMemoryPointer(pybind11::array_t<float> array) {
    if (!validateArray(array)) {
        return nullptr;
    }
    
    return array.mutable_data();
}

bool AdvancedPythonCppBridge::copyToGPU(pybind11::array_t<float> array, void* gpuPtr) {
    if (!validateArray(array) || !gpuPtr) {
        spdlog::error("Invalid array or GPU pointer");
        return false;
    }
    
    try {
        size_t size = array.size() * sizeof(float);
        cudaError_t cudaError = cudaMemcpy(gpuPtr, array.data(), size, cudaMemcpyHostToDevice);
        
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to copy array to GPU: {}", cudaGetErrorString(cudaError));
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to copy array to GPU: {}", e.what());
        return false;
    }
}

bool AdvancedPythonCppBridge::copyFromGPU(void* gpuPtr, pybind11::array_t<float> array) {
    if (!validateArray(array) || !gpuPtr) {
        spdlog::error("Invalid array or GPU pointer");
        return false;
    }
    
    try {
        size_t size = array.size() * sizeof(float);
        cudaError_t cudaError = cudaMemcpy(array.mutable_data(), gpuPtr, size, cudaMemcpyDeviceToHost);
        
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to copy array from GPU: {}", cudaGetErrorString(cudaError));
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to copy array from GPU: {}", e.what());
        return false;
    }
}

std::map<std::string, double> AdvancedPythonCppBridge::getResourceUsage(const std::string& llmId) {
    std::map<std::string, double> usage;
    
    if (!validateLLM(llmId)) {
        return usage;
    }
    
    try {
        // Get kernel performance metrics
        if (kernel_) {
            auto kernelMetrics = kernel_->getPerformanceMetrics();
            usage.insert(kernelMetrics.begin(), kernelMetrics.end());
        }
        
        // Add LLM-specific metrics
        auto it = llmMemoryArrays_.find(llmId);
        if (it != llmMemoryArrays_.end()) {
            usage["memory_array_size"] = static_cast<double>(it->second.size());
        }
        
        auto taskIt = llmTasks_.find(llmId);
        if (taskIt != llmTasks_.end()) {
            usage["active_tasks"] = static_cast<double>(taskIt->second.size());
        }
        
        usage["is_profiling_enabled"] = llmProfiling_[llmId] ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get resource usage for LLM {}: {}", llmId, e.what());
    }
    
    return usage;
}

std::map<std::string, size_t> AdvancedPythonCppBridge::getMemoryUsage(const std::string& llmId) {
    std::map<std::string, size_t> usage;
    
    if (!validateLLM(llmId)) {
        return usage;
    }
    
    try {
        // Get memory usage from kernel
        if (kernel_) {
            auto kernelUsage = kernel_->getResourceUsage();
            usage.insert(kernelUsage.begin(), kernelUsage.end());
        }
        
        // Add LLM-specific memory usage
        auto it = llmMemoryArrays_.find(llmId);
        if (it != llmMemoryArrays_.end()) {
            usage["array_memory_bytes"] = it->second.size() * sizeof(float);
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get memory usage for LLM {}: {}", llmId, e.what());
    }
    
    return usage;
}

std::vector<std::string> AdvancedPythonCppBridge::getActiveLLMs() {
    std::vector<std::string> activeLLMs;
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    for (const auto& pair : llmConfigs_) {
        if (isLLMActive(pair.first)) {
            activeLLMs.push_back(pair.first);
        }
    }
    
    return activeLLMs;
}

bool AdvancedPythonCppBridge::isLLMActive(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    // Check if LLM has configuration and active resources
    auto configIt = llmConfigs_.find(llmId);
    if (configIt == llmConfigs_.end()) {
        return false;
    }
    
    // Check if LLM has active memory arrays or tasks
    auto memoryIt = llmMemoryArrays_.find(llmId);
    auto taskIt = llmTasks_.find(llmId);
    
    return (memoryIt != llmMemoryArrays_.end() && !memoryIt->second.empty()) ||
           (taskIt != llmTasks_.end() && !taskIt->second.empty());
}

std::vector<int> AdvancedPythonCppBridge::getAvailableComputeNodes() {
    std::vector<int> availableNodes;
    
    if (!kernel_) {
        return availableNodes;
    }
    
    try {
        auto computeNodes = kernel_->getAvailableComputeNodes();
        for (const auto& node : computeNodes) {
            if (!node.isAllocated) {
                availableNodes.push_back(node.nodeId);
            }
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get available compute nodes: {}", e.what());
    }
    
    return availableNodes;
}

bool AdvancedPythonCppBridge::allocateComputeNode(int nodeId, const std::string& llmId) {
    if (!validateLLM(llmId) || !kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->allocateComputeNode(nodeId, llmId);
        if (success) {
            spdlog::info("Allocated compute node {} for LLM {}", nodeId, llmId);
        } else {
            spdlog::error("Failed to allocate compute node {} for LLM {}", nodeId, llmId);
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate compute node {} for LLM {}: {}", nodeId, llmId, e.what());
        return false;
    }
}

bool AdvancedPythonCppBridge::deallocateComputeNode(int nodeId, const std::string& llmId) {
    if (!validateLLM(llmId) || !kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->deallocateComputeNode(nodeId);
        if (success) {
            spdlog::info("Deallocated compute node {} for LLM {}", nodeId, llmId);
        } else {
            spdlog::error("Failed to deallocate compute node {} for LLM {}", nodeId, llmId);
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate compute node {} for LLM {}: {}", nodeId, llmId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedPythonCppBridge::getComputeNodeInfo(int nodeId) {
    std::map<std::string, std::string> info;
    
    if (!kernel_) {
        return info;
    }
    
    try {
        auto node = kernel_->getComputeNode(nodeId);
        if (node.nodeId == nodeId) {
            info["node_id"] = std::to_string(node.nodeId);
            info["type"] = std::to_string(static_cast<int>(node.type));
            info["memory_size"] = std::to_string(node.memorySize);
            info["compute_capability"] = std::to_string(node.computeCapability);
            info["is_allocated"] = node.isAllocated ? "true" : "false";
            info["is_active"] = node.isActive ? "true" : "false";
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get compute node info for node {}: {}", nodeId, e.what());
    }
    
    return info;
}

std::string AdvancedPythonCppBridge::scheduleTask(const std::string& llmId, const std::string& taskType, 
                                                const std::map<std::string, std::string>& parameters) {
    if (!validateLLM(llmId) || !kernel_) {
        return "";
    }
    
    try {
        // Create compute task
        ComputeTask task;
        task.taskId = generateTaskId();
        task.llmId = llmId;
        task.priority = TaskPriority::NORMAL;
        task.requiredMemory = 1024 * 1024; // 1MB default
        task.requiredCores = 1; // 1 core default
        task.taskFunction = [llmId, taskType, parameters]() {
            spdlog::info("Executing task {} for LLM {}", taskType, llmId);
            // Task execution logic would go here
        };
        
        // Schedule task
        std::string taskId = kernel_->scheduleTask(task);
        
        if (!taskId.empty()) {
            // Store task ID for this LLM
            llmTasks_[llmId].push_back(taskId);
            spdlog::info("Scheduled task {} for LLM {}", taskId, llmId);
        }
        
        return taskId;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to schedule task for LLM {}: {}", llmId, e.what());
        return "";
    }
}

bool AdvancedPythonCppBridge::cancelTask(const std::string& taskId) {
    if (!kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->cancelTask(taskId);
        if (success) {
            // Remove task from LLM task lists
            for (auto& pair : llmTasks_) {
                auto& tasks = pair.second;
                auto it = std::find(tasks.begin(), tasks.end(), taskId);
                if (it != tasks.end()) {
                    tasks.erase(it);
                    break;
                }
            }
            spdlog::info("Cancelled task {}", taskId);
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel task {}: {}", taskId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedPythonCppBridge::getTaskStatus(const std::string& taskId) {
    std::map<std::string, std::string> status;
    
    if (!kernel_) {
        return status;
    }
    
    try {
        auto task = kernel_->getTaskStatus(taskId);
        if (!task.taskId.empty()) {
            status["task_id"] = task.taskId;
            status["llm_id"] = task.llmId;
            status["priority"] = std::to_string(static_cast<int>(task.priority));
            status["required_memory"] = std::to_string(task.requiredMemory);
            status["required_cores"] = std::to_string(task.requiredCores);
            status["is_completed"] = task.isCompleted ? "true" : "false";
            status["result"] = task.result;
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get task status for task {}: {}", taskId, e.what());
    }
    
    return status;
}

std::vector<std::string> AdvancedPythonCppBridge::getActiveTasks(const std::string& llmId) {
    std::vector<std::string> activeTasks;
    
    if (!validateLLM(llmId)) {
        return activeTasks;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    auto it = llmTasks_.find(llmId);
    if (it != llmTasks_.end()) {
        activeTasks = it->second;
    }
    
    return activeTasks;
}

std::map<std::string, double> AdvancedPythonCppBridge::getPerformanceMetrics() {
    std::map<std::string, double> metrics;
    
    if (kernel_) {
        auto kernelMetrics = kernel_->getPerformanceMetrics();
        metrics.insert(kernelMetrics.begin(), kernelMetrics.end());
    }
    
    // Add bridge-specific metrics
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    metrics["registered_llms"] = static_cast<double>(llmConfigs_.size());
    metrics["active_llms"] = static_cast<double>(std::count_if(llmConfigs_.begin(), llmConfigs_.end(),
                                                              [this](const auto& pair) { return isLLMActive(pair.first); }));
    metrics["total_memory_arrays"] = static_cast<double>(llmMemoryArrays_.size());
    
    return metrics;
}

bool AdvancedPythonCppBridge::enableProfiling(const std::string& llmId) {
    if (!validateLLM(llmId)) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    llmProfiling_[llmId] = true;
    
    if (kernel_) {
        kernel_->enableProfiling();
    }
    
    spdlog::info("Enabled profiling for LLM {}", llmId);
    return true;
}

bool AdvancedPythonCppBridge::disableProfiling(const std::string& llmId) {
    if (!validateLLM(llmId)) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    llmProfiling_[llmId] = false;
    
    spdlog::info("Disabled profiling for LLM {}", llmId);
    return true;
}

std::map<std::string, double> AdvancedPythonCppBridge::getProfilingData(const std::string& llmId) {
    std::map<std::string, double> profilingData;
    
    if (!validateLLM(llmId)) {
        return profilingData;
    }
    
    try {
        // Get profiling data from kernel
        if (kernel_) {
            auto kernelMetrics = kernel_->getPerformanceMetrics();
            profilingData.insert(kernelMetrics.begin(), kernelMetrics.end());
        }
        
        // Add LLM-specific profiling data
        std::lock_guard<std::mutex> lock(bridgeMutex_);
        profilingData["is_profiling_enabled"] = llmProfiling_[llmId] ? 1.0 : 0.0;
        
        auto taskIt = llmTasks_.find(llmId);
        if (taskIt != llmTasks_.end()) {
            profilingData["active_tasks"] = static_cast<double>(taskIt->second.size());
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get profiling data for LLM {}: {}", llmId, e.what());
    }
    
    return profilingData;
}

pybind11::array_t<float> AdvancedPythonCppBridge::createSharedMemoryArray(size_t size, const std::string& llmId) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        spdlog::error("Bridge not initialized");
        return pybind11::array_t<float>();
    }
    
    try {
        // Create shared memory array
        pybind11::array_t<float> array(size);
        
        // Store array for this LLM
        llmMemoryArrays_[llmId] = array;
        
        spdlog::info("Created shared memory array of size {} for LLM {}", size, llmId);
        return array;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create shared memory array for LLM {}: {}", llmId, e.what());
        return pybind11::array_t<float>();
    }
}

bool AdvancedPythonCppBridge::destroySharedMemoryArray(pybind11::array_t<float> array, const std::string& llmId) {
    return deallocateMemoryArray(array, llmId);
}

void* AdvancedPythonCppBridge::getSharedMemoryPointer(pybind11::array_t<float> array) {
    return getMemoryPointer(array);
}

bool AdvancedPythonCppBridge::registerLLM(const std::string& llmId, const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        spdlog::error("Bridge not initialized");
        return false;
    }
    
    try {
        // Store LLM configuration
        llmConfigs_[llmId] = config;
        llmProfiling_[llmId] = false;
        
        spdlog::info("Registered LLM {} with {} configuration parameters", llmId, config.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register LLM {}: {}", llmId, e.what());
        return false;
    }
}

bool AdvancedPythonCppBridge::unregisterLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    
    if (!initialized_) {
        spdlog::error("Bridge not initialized");
        return false;
    }
    
    try {
        // Cleanup LLM resources
        cleanupLLMResources(llmId);
        
        // Remove LLM from all data structures
        llmConfigs_.erase(llmId);
        llmMemoryArrays_.erase(llmId);
        llmTasks_.erase(llmId);
        llmProfiling_.erase(llmId);
        
        spdlog::info("Unregistered LLM {}", llmId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedPythonCppBridge::getLLMConfig(const std::string& llmId) {
    std::map<std::string, std::string> config;
    
    if (!validateLLM(llmId)) {
        return config;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    auto it = llmConfigs_.find(llmId);
    if (it != llmConfigs_.end()) {
        config = it->second;
    }
    
    return config;
}

bool AdvancedPythonCppBridge::updateLLMConfig(const std::string& llmId, const std::map<std::string, std::string>& config) {
    if (!validateLLM(llmId)) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    llmConfigs_[llmId] = config;
    
    spdlog::info("Updated configuration for LLM {}", llmId);
    return true;
}

bool AdvancedPythonCppBridge::optimizeForLLM(const std::string& llmId, const std::map<std::string, std::string>& requirements) {
    if (!validateLLM(llmId) || !kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->optimizeForLLM(llmId, requirements);
        if (success) {
            spdlog::info("Optimized kernel for LLM {} with {} requirements", llmId, requirements.size());
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize for LLM {}: {}", llmId, e.what());
        return false;
    }
}

bool AdvancedPythonCppBridge::createVirtualComputeNode(const std::string& llmId, size_t memorySize, size_t coreCount) {
    if (!validateLLM(llmId) || !kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->createVirtualComputeNode(llmId, memorySize, coreCount);
        if (success) {
            spdlog::info("Created virtual compute node for LLM {} with {} cores and {} bytes memory", 
                        llmId, coreCount, memorySize);
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to create virtual compute node for LLM {}: {}", llmId, e.what());
        return false;
    }
}

bool AdvancedPythonCppBridge::destroyVirtualComputeNode(const std::string& llmId) {
    if (!validateLLM(llmId) || !kernel_) {
        return false;
    }
    
    try {
        bool success = kernel_->destroyVirtualComputeNode(llmId);
        if (success) {
            spdlog::info("Destroyed virtual compute node for LLM {}", llmId);
        }
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy virtual compute node for LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedPythonCppBridge::getSystemInfo() {
    std::map<std::string, std::string> info;
    
    try {
        // Get system information
        info["bridge_initialized"] = initialized_ ? "true" : "false";
        info["kernel_available"] = kernel_ ? "true" : "false";
        
        if (kernel_) {
            auto device = kernel_->getCurrentDevice();
            info["current_device"] = device.name;
            info["device_id"] = std::to_string(device.deviceId);
            info["total_memory_gb"] = std::to_string(device.totalMemory / (1024 * 1024 * 1024));
            info["free_memory_gb"] = std::to_string(device.freeMemory / (1024 * 1024 * 1024));
        }
        
        // Get bridge statistics
        std::lock_guard<std::mutex> lock(bridgeMutex_);
        info["registered_llms"] = std::to_string(llmConfigs_.size());
        info["active_llms"] = std::to_string(std::count_if(llmConfigs_.begin(), llmConfigs_.end(),
                                                          [this](const auto& pair) { return isLLMActive(pair.first); }));
        info["total_memory_arrays"] = std::to_string(llmMemoryArrays_.size());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system info: {}", e.what());
    }
    
    return info;
}

bool AdvancedPythonCppBridge::runDiagnostics() {
    spdlog::info("Running bridge diagnostics");
    
    try {
        // Check bridge initialization
        if (!initialized_) {
            spdlog::error("Diagnostic failed: Bridge not initialized");
            return false;
        }
        
        // Check kernel availability
        if (!kernel_) {
            spdlog::error("Diagnostic failed: Kernel not available");
            return false;
        }
        
        // Check kernel initialization
        if (!kernel_->isInitialized()) {
            spdlog::error("Diagnostic failed: Kernel not initialized");
            return false;
        }
        
        // Test basic functionality
        std::string testLLMId = "diagnostic_test";
        auto testArray = allocateMemoryArray(100, testLLMId);
        if (testArray.empty()) {
            spdlog::error("Diagnostic failed: Memory allocation test failed");
            return false;
        }
        
        deallocateMemoryArray(testArray, testLLMId);
        unregisterLLM(testLLMId);
        
        spdlog::info("Bridge diagnostics completed successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Bridge diagnostics failed: {}", e.what());
        return false;
    }
}

std::vector<std::string> AdvancedPythonCppBridge::getDiagnosticResults() {
    std::vector<std::string> results;
    
    try {
        // Run diagnostics and collect results
        bool success = runDiagnostics();
        results.push_back(success ? "Bridge diagnostics: PASSED" : "Bridge diagnostics: FAILED");
        
        // Add system info
        auto systemInfo = getSystemInfo();
        for (const auto& pair : systemInfo) {
            results.push_back(pair.first + ": " + pair.second);
        }
        
        // Add performance metrics
        auto metrics = getPerformanceMetrics();
        for (const auto& pair : metrics) {
            results.push_back(pair.first + ": " + std::to_string(pair.second));
        }
        
    } catch (const std::exception& e) {
        results.push_back("Diagnostic error: " + std::string(e.what()));
    }
    
    return results;
}

bool AdvancedPythonCppBridge::validateLLM(const std::string& llmId) {
    if (llmId.empty()) {
        spdlog::error("Invalid LLM ID: empty");
        return false;
    }
    
    std::lock_guard<std::mutex> lock(bridgeMutex_);
    return llmConfigs_.find(llmId) != llmConfigs_.end();
}

bool AdvancedPythonCppBridge::validateArray(pybind11::array_t<float> array) {
    if (array.empty()) {
        spdlog::error("Invalid array: empty");
        return false;
    }
    
    if (!array.data()) {
        spdlog::error("Invalid array: null data pointer");
        return false;
    }
    
    return true;
}

std::string AdvancedPythonCppBridge::generateTaskId() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(100000, 999999);
    
    std::stringstream ss;
    ss << "task_" << std::chrono::duration_cast<std::chrono::milliseconds>(
           std::chrono::system_clock::now().time_since_epoch()).count()
       << "_" << dis(gen);
    
    return ss.str();
}

void AdvancedPythonCppBridge::updateLLMResourceUsage(const std::string& llmId) {
    // Update resource usage statistics for the LLM
    // This would typically involve updating performance counters
}

void AdvancedPythonCppBridge::cleanupLLMResources(const std::string& llmId) {
    try {
        // Cancel all tasks for this LLM
        auto taskIt = llmTasks_.find(llmId);
        if (taskIt != llmTasks_.end()) {
            for (const auto& taskId : taskIt->second) {
                if (kernel_) {
                    kernel_->cancelTask(taskId);
                }
            }
        }
        
        // Deallocate memory arrays
        auto memoryIt = llmMemoryArrays_.find(llmId);
        if (memoryIt != llmMemoryArrays_.end()) {
            llmMemoryArrays_.erase(memoryIt);
        }
        
        // Destroy virtual compute nodes
        if (kernel_) {
            kernel_->destroyVirtualComputeNode(llmId);
        }
        
        spdlog::info("Cleaned up resources for LLM {}", llmId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup resources for LLM {}: {}", llmId, e.what());
    }
}

// PythonCppBridgeManager implementation
PythonCppBridgeManager::PythonCppBridgeManager()
    : bridgeInitialized_(false) {
    
    spdlog::info("PythonCppBridgeManager initialized");
}

PythonCppBridgeManager::~PythonCppBridgeManager() {
    shutdownBridge();
}

PythonCppBridgeManager& PythonCppBridgeManager::getInstance() {
    static PythonCppBridgeManager instance;
    return instance;
}

std::shared_ptr<PythonCppBridge> PythonCppBridgeManager::getBridge() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return bridge_;
}

bool PythonCppBridgeManager::initializeBridge() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (bridgeInitialized_) {
        spdlog::warn("Bridge already initialized");
        return true;
    }
    
    bridge_ = std::make_shared<AdvancedPythonCppBridge>();
    bool success = bridge_->initialize();
    
    if (success) {
        bridgeInitialized_ = true;
        spdlog::info("PythonCppBridgeManager initialized successfully");
    } else {
        spdlog::error("Failed to initialize PythonCppBridgeManager");
    }
    
    return success;
}

void PythonCppBridgeManager::shutdownBridge() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!bridgeInitialized_) {
        return;
    }
    
    if (bridge_) {
        bridge_->shutdown();
        bridge_.reset();
    }
    
    bridgeInitialized_ = false;
    spdlog::info("PythonCppBridgeManager shutdown completed");
}

bool PythonCppBridgeManager::isBridgeInitialized() const {
    return bridgeInitialized_;
}

pybind11::array_t<float> PythonCppBridgeManager::allocateMemoryArray(size_t size, const std::string& llmId) {
    if (!bridge_) {
        return pybind11::array_t<float>();
    }
    return bridge_->allocateMemoryArray(size, llmId);
}

bool PythonCppBridgeManager::deallocateMemoryArray(pybind11::array_t<float> array, const std::string& llmId) {
    if (!bridge_) {
        return false;
    }
    return bridge_->deallocateMemoryArray(array, llmId);
}

std::map<std::string, double> PythonCppBridgeManager::getResourceUsage(const std::string& llmId) {
    if (!bridge_) {
        return std::map<std::string, double>();
    }
    return bridge_->getResourceUsage(llmId);
}

std::vector<std::string> PythonCppBridgeManager::getActiveLLMs() {
    if (!bridge_) {
        return std::vector<std::string>();
    }
    return bridge_->getActiveLLMs();
}

bool PythonCppBridgeManager::registerLLM(const std::string& llmId, const std::map<std::string, std::string>& config) {
    if (!bridge_) {
        return false;
    }
    return bridge_->registerLLM(llmId, config);
}

bool PythonCppBridgeManager::unregisterLLM(const std::string& llmId) {
    if (!bridge_) {
        return false;
    }
    return bridge_->unregisterLLM(llmId);
}

void PythonCppBridgeManager::setBridgeConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    bridgeConfig_ = config;
}

std::map<std::string, std::string> PythonCppBridgeManager::getBridgeConfiguration() const {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return bridgeConfig_;
}

} // namespace core
} // namespace cogniware
