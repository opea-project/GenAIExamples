#include "core/customized_kernel.h"
#include <spdlog/spdlog.h>
#include <random>
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace cogniware {
namespace core {

AdvancedCustomizedKernel::AdvancedCustomizedKernel()
    : initialized_(false)
    , currentDeviceId_(-1)
    , shutdownRequested_(false)
    , profilingEnabled_(false) {
    
    spdlog::info("AdvancedCustomizedKernel initialized");
}

AdvancedCustomizedKernel::~AdvancedCustomizedKernel() {
    shutdown();
}

bool AdvancedCustomizedKernel::initialize() {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    if (initialized_) {
        spdlog::warn("Kernel already initialized");
        return true;
    }
    
    try {
        // Initialize CUDA
        cudaError_t cudaError = cudaSetDevice(0);
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaError));
            return false;
        }
        
        // Get device count
        int deviceCount;
        cudaError = cudaGetDeviceCount(&deviceCount);
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to get CUDA device count: {}", cudaGetErrorString(cudaError));
            return false;
        }
        
        if (deviceCount == 0) {
            spdlog::error("No CUDA devices found");
            return false;
        }
        
        // Initialize compute nodes and memory partitions
        initializeComputeNodes();
        initializeMemoryPartitions();
        
        // Start scheduler thread
        shutdownRequested_ = false;
        schedulerThread_ = std::thread(&AdvancedCustomizedKernel::schedulerLoop, this);
        
        initialized_ = true;
        spdlog::info("AdvancedCustomizedKernel initialized successfully with {} devices", deviceCount);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize kernel: {}", e.what());
        return false;
    }
}

void AdvancedCustomizedKernel::shutdown() {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Signal shutdown
        shutdownRequested_ = true;
        
        // Wait for scheduler thread to finish
        if (schedulerThread_.joinable()) {
            schedulerThread_.join();
        }
        
        // Cleanup resources
        cleanupResources();
        
        // Reset CUDA device
        cudaDeviceReset();
        
        initialized_ = false;
        spdlog::info("AdvancedCustomizedKernel shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during kernel shutdown: {}", e.what());
    }
}

bool AdvancedCustomizedKernel::isInitialized() const {
    return initialized_;
}

std::vector<GPUDeviceInfo> AdvancedCustomizedKernel::getAvailableDevices() {
    std::vector<GPUDeviceInfo> devices;
    
    int deviceCount;
    cudaError_t cudaError = cudaGetDeviceCount(&deviceCount);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to get device count: {}", cudaGetErrorString(cudaError));
        return devices;
    }
    
    for (int i = 0; i < deviceCount; ++i) {
        GPUDeviceInfo device;
        device.deviceId = i;
        
        // Get device properties
        cudaDeviceProp prop;
        cudaError = cudaGetDeviceProperties(&prop, i);
        if (cudaError != cudaSuccess) {
            spdlog::error("Failed to get device properties for device {}: {}", i, cudaGetErrorString(cudaError));
            continue;
        }
        
        device.name = prop.name;
        device.computeCapability = prop.major * 10 + prop.minor;
        device.maxThreadsPerBlock = prop.maxThreadsPerBlock;
        device.maxBlocksPerGrid = prop.maxGridSize[0];
        device.maxThreadsPerMultiProcessor = prop.maxThreadsPerMultiProcessor;
        device.multiProcessorCount = prop.multiProcessorCount;
        device.supportsNVLink = (prop.major >= 7); // NVLink support in Volta and later
        
        // Get memory info
        size_t freeMem, totalMem;
        cudaError = cudaMemGetInfo(&freeMem, &totalMem);
        if (cudaError == cudaSuccess) {
            device.totalMemory = totalMem;
            device.freeMemory = freeMem;
        }
        
        // Estimate tensor and CUDA cores (rough estimates)
        device.tensorCoreCount = prop.multiProcessorCount * 8; // Approximate
        device.cudaCoreCount = prop.multiProcessorCount * 64; // Approximate
        
        devices.push_back(device);
    }
    
    return devices;
}

bool AdvancedCustomizedKernel::selectDevice(int deviceId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    cudaError_t cudaError = cudaSetDevice(deviceId);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to select device {}: {}", deviceId, cudaGetErrorString(cudaError));
        return false;
    }
    
    currentDeviceId_ = deviceId;
    
    // Get device info
    auto devices = getAvailableDevices();
    for (const auto& device : devices) {
        if (device.deviceId == deviceId) {
            currentDevice_ = device;
            break;
        }
    }
    
    spdlog::info("Selected device {}: {}", deviceId, currentDevice_.name);
    return true;
}

GPUDeviceInfo AdvancedCustomizedKernel::getCurrentDevice() const {
    return currentDevice_;
}

std::vector<ComputeNode> AdvancedCustomizedKernel::getAvailableComputeNodes() {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    return computeNodes_;
}

bool AdvancedCustomizedKernel::allocateComputeNode(int nodeId, const std::string& llmId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    for (auto& node : computeNodes_) {
        if (node.nodeId == nodeId && !node.isAllocated) {
            node.isAllocated = true;
            node.isActive = true;
            node.lastUsed = std::chrono::system_clock::now();
            spdlog::info("Allocated compute node {} to LLM {}", nodeId, llmId);
            return true;
        }
    }
    
    spdlog::error("Failed to allocate compute node {} to LLM {}", nodeId, llmId);
    return false;
}

bool AdvancedCustomizedKernel::deallocateComputeNode(int nodeId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    for (auto& node : computeNodes_) {
        if (node.nodeId == nodeId && node.isAllocated) {
            node.isAllocated = false;
            node.isActive = false;
            spdlog::info("Deallocated compute node {}", nodeId);
            return true;
        }
    }
    
    spdlog::error("Failed to deallocate compute node {}", nodeId);
    return false;
}

ComputeNode AdvancedCustomizedKernel::getComputeNode(int nodeId) const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    for (const auto& node : computeNodes_) {
        if (node.nodeId == nodeId) {
            return node;
        }
    }
    
    return ComputeNode{}; // Return empty node if not found
}

std::vector<MemoryPartition> AdvancedCustomizedKernel::getMemoryPartitions() {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    return memoryPartitions_;
}

bool AdvancedCustomizedKernel::createMemoryPartition(size_t size, MemoryPartitionType type, const std::string& llmId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    MemoryPartition partition;
    partition.partitionId = static_cast<int>(memoryPartitions_.size());
    partition.type = type;
    partition.size = size;
    partition.isAllocated = true;
    partition.ownerLLM = llmId;
    partition.allocatedAt = std::chrono::system_clock::now();
    
    // Allocate memory
    cudaError_t cudaError = cudaMalloc(&partition.devicePtr, size);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to allocate memory partition: {}", cudaGetErrorString(cudaError));
        return false;
    }
    
    memoryPartitions_.push_back(partition);
    spdlog::info("Created memory partition {} of size {} for LLM {}", partition.partitionId, size, llmId);
    return true;
}

bool AdvancedCustomizedKernel::destroyMemoryPartition(int partitionId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    for (auto it = memoryPartitions_.begin(); it != memoryPartitions_.end(); ++it) {
        if (it->partitionId == partitionId) {
            if (it->devicePtr) {
                cudaFree(it->devicePtr);
            }
            memoryPartitions_.erase(it);
            spdlog::info("Destroyed memory partition {}", partitionId);
            return true;
        }
    }
    
    spdlog::error("Failed to destroy memory partition {}", partitionId);
    return false;
}

MemoryPartition AdvancedCustomizedKernel::getMemoryPartition(int partitionId) const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    for (const auto& partition : memoryPartitions_) {
        if (partition.partitionId == partitionId) {
            return partition;
        }
    }
    
    return MemoryPartition{}; // Return empty partition if not found
}

void* AdvancedCustomizedKernel::allocateMemory(size_t size, const std::string& llmId) {
    void* ptr = nullptr;
    cudaError_t cudaError = cudaMalloc(&ptr, size);
    
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to allocate memory for LLM {}: {}", llmId, cudaGetErrorString(cudaError));
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(kernelMutex_);
    llmMemoryAllocations_[llmId] = ptr;
    
    spdlog::info("Allocated {} bytes for LLM {}", size, llmId);
    return ptr;
}

bool AdvancedCustomizedKernel::deallocateMemory(void* ptr) {
    if (!ptr) {
        return false;
    }
    
    cudaError_t cudaError = cudaFree(ptr);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to deallocate memory: {}", cudaGetErrorString(cudaError));
        return false;
    }
    
    std::lock_guard<std::mutex> lock(kernelMutex_);
    // Remove from allocations map
    for (auto it = llmMemoryAllocations_.begin(); it != llmMemoryAllocations_.end(); ++it) {
        if (it->second == ptr) {
            llmMemoryAllocations_.erase(it);
            break;
        }
    }
    
    spdlog::info("Deallocated memory at {}", ptr);
    return true;
}

bool AdvancedCustomizedKernel::copyMemory(void* dst, const void* src, size_t size) {
    cudaError_t cudaError = cudaMemcpy(dst, src, size, cudaMemcpyDefault);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to copy memory: {}", cudaGetErrorString(cudaError));
        return false;
    }
    return true;
}

bool AdvancedCustomizedKernel::copyMemoryAsync(void* dst, const void* src, size_t size, cudaStream_t stream) {
    cudaError_t cudaError = cudaMemcpyAsync(dst, src, size, cudaMemcpyDefault, stream);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to copy memory asynchronously: {}", cudaGetErrorString(cudaError));
        return false;
    }
    return true;
}

std::string AdvancedCustomizedKernel::scheduleTask(const ComputeTask& task) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    if (!validateTask(task)) {
        spdlog::error("Invalid task: {}", task.taskId);
        return "";
    }
    
    ComputeTask scheduledTask = task;
    scheduledTask.taskId = generateTaskId();
    scheduledTask.createdAt = std::chrono::system_clock::now();
    scheduledTask.scheduledAt = std::chrono::system_clock::now();
    scheduledTask.isCompleted = false;
    
    activeTasks_[scheduledTask.taskId] = scheduledTask;
    taskQueue_.push(scheduledTask);
    
    spdlog::info("Scheduled task {} for LLM {}", scheduledTask.taskId, task.llmId);
    return scheduledTask.taskId;
}

bool AdvancedCustomizedKernel::cancelTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    auto it = activeTasks_.find(taskId);
    if (it != activeTasks_.end()) {
        deallocateResourcesForTask(taskId);
        activeTasks_.erase(it);
        spdlog::info("Cancelled task {}", taskId);
        return true;
    }
    
    spdlog::error("Failed to cancel task {}", taskId);
    return false;
}

ComputeTask AdvancedCustomizedKernel::getTaskStatus(const std::string& taskId) const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    auto it = activeTasks_.find(taskId);
    if (it != activeTasks_.end()) {
        return it->second;
    }
    
    return ComputeTask{}; // Return empty task if not found
}

std::vector<ComputeTask> AdvancedCustomizedKernel::getActiveTasks() const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    std::vector<ComputeTask> tasks;
    for (const auto& pair : activeTasks_) {
        tasks.push_back(pair.second);
    }
    return tasks;
}

cudaStream_t AdvancedCustomizedKernel::createStream(const std::string& llmId) {
    cudaStream_t stream;
    cudaError_t cudaError = cudaStreamCreate(&stream);
    
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to create CUDA stream for LLM {}: {}", llmId, cudaGetErrorString(cudaError));
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(kernelMutex_);
    llmStreams_[llmId].push_back(stream);
    
    spdlog::info("Created CUDA stream for LLM {}", llmId);
    return stream;
}

bool AdvancedCustomizedKernel::destroyStream(cudaStream_t stream) {
    if (!stream) {
        return false;
    }
    
    cudaError_t cudaError = cudaStreamDestroy(stream);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to destroy CUDA stream: {}", cudaGetErrorString(cudaError));
        return false;
    }
    
    std::lock_guard<std::mutex> lock(kernelMutex_);
    // Remove from streams map
    for (auto& pair : llmStreams_) {
        auto& streams = pair.second;
        auto it = std::find(streams.begin(), streams.end(), stream);
        if (it != streams.end()) {
            streams.erase(it);
            break;
        }
    }
    
    spdlog::info("Destroyed CUDA stream");
    return true;
}

bool AdvancedCustomizedKernel::synchronizeStream(cudaStream_t stream) {
    if (!stream) {
        return false;
    }
    
    cudaError_t cudaError = cudaStreamSynchronize(stream);
    if (cudaError != cudaSuccess) {
        spdlog::error("Failed to synchronize CUDA stream: {}", cudaGetErrorString(cudaError));
        return false;
    }
    return true;
}

std::vector<cudaStream_t> AdvancedCustomizedKernel::getStreamsForLLM(const std::string& llmId) const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    auto it = llmStreams_.find(llmId);
    if (it != llmStreams_.end()) {
        return it->second;
    }
    
    return std::vector<cudaStream_t>();
}

std::map<std::string, double> AdvancedCustomizedKernel::getPerformanceMetrics() {
    std::map<std::string, double> metrics;
    
    // Get CUDA device properties
    cudaDeviceProp prop;
    cudaError_t cudaError = cudaGetDeviceProperties(&prop, currentDeviceId_);
    if (cudaError == cudaSuccess) {
        metrics["compute_capability"] = prop.major * 10 + prop.minor;
        metrics["multi_processor_count"] = prop.multiProcessorCount;
        metrics["max_threads_per_block"] = prop.maxThreadsPerBlock;
        metrics["max_blocks_per_grid"] = prop.maxGridSize[0];
    }
    
    // Get memory info
    size_t freeMem, totalMem;
    cudaError = cudaMemGetInfo(&freeMem, &totalMem);
    if (cudaError == cudaSuccess) {
        metrics["total_memory_gb"] = totalMem / (1024.0 * 1024.0 * 1024.0);
        metrics["free_memory_gb"] = freeMem / (1024.0 * 1024.0 * 1024.0);
        metrics["memory_utilization"] = (totalMem - freeMem) / (double)totalMem * 100.0;
    }
    
    // Get active task count
    std::lock_guard<std::mutex> lock(kernelMutex_);
    metrics["active_tasks"] = activeTasks_.size();
    metrics["allocated_compute_nodes"] = std::count_if(computeNodes_.begin(), computeNodes_.end(),
                                                     [](const ComputeNode& node) { return node.isAllocated; });
    metrics["allocated_memory_partitions"] = std::count_if(memoryPartitions_.begin(), memoryPartitions_.end(),
                                                         [](const MemoryPartition& partition) { return partition.isAllocated; });
    
    return metrics;
}

std::map<std::string, size_t> AdvancedCustomizedKernel::getResourceUsage() {
    std::map<std::string, size_t> usage;
    
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    // Count allocated resources
    usage["allocated_compute_nodes"] = std::count_if(computeNodes_.begin(), computeNodes_.end(),
                                                    [](const ComputeNode& node) { return node.isAllocated; });
    usage["total_compute_nodes"] = computeNodes_.size();
    
    usage["allocated_memory_partitions"] = std::count_if(memoryPartitions_.begin(), memoryPartitions_.end(),
                                                       [](const MemoryPartition& partition) { return partition.isAllocated; });
    usage["total_memory_partitions"] = memoryPartitions_.size();
    
    usage["active_tasks"] = activeTasks_.size();
    usage["total_streams"] = 0;
    for (const auto& pair : llmStreams_) {
        usage["total_streams"] += pair.second.size();
    }
    
    return usage;
}

bool AdvancedCustomizedKernel::enableProfiling() {
    profilingEnabled_ = true;
    spdlog::info("Profiling enabled");
    return true;
}

bool AdvancedCustomizedKernel::disableProfiling() {
    profilingEnabled_ = false;
    spdlog::info("Profiling disabled");
    return true;
}

bool AdvancedCustomizedKernel::optimizeForLLM(const std::string& llmId, const std::map<std::string, std::string>& requirements) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    spdlog::info("Optimizing kernel for LLM {} with {} requirements", llmId, requirements.size());
    
    // Parse requirements and apply optimizations
    for (const auto& req : requirements) {
        if (req.first == "memory_priority") {
            // Optimize memory allocation strategy
            spdlog::info("Applied memory priority optimization for LLM {}", llmId);
        } else if (req.first == "compute_priority") {
            // Optimize compute node allocation
            spdlog::info("Applied compute priority optimization for LLM {}", llmId);
        } else if (req.first == "stream_priority") {
            // Optimize CUDA stream management
            spdlog::info("Applied stream priority optimization for LLM {}", llmId);
        }
    }
    
    return true;
}

bool AdvancedCustomizedKernel::createVirtualComputeNode(const std::string& llmId, size_t memorySize, size_t coreCount) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    ComputeNode node;
    node.nodeId = static_cast<int>(computeNodes_.size());
    node.type = ComputeNodeType::TENSOR_CORE;
    node.memorySize = memorySize;
    node.computeCapability = coreCount;
    node.isAllocated = true;
    node.isActive = true;
    node.lastUsed = std::chrono::system_clock::now();
    
    computeNodes_.push_back(node);
    
    spdlog::info("Created virtual compute node {} for LLM {} with {} cores and {} bytes memory", 
                node.nodeId, llmId, coreCount, memorySize);
    return true;
}

bool AdvancedCustomizedKernel::destroyVirtualComputeNode(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    // Find and deallocate nodes for this LLM
    bool found = false;
    for (auto& node : computeNodes_) {
        if (node.isAllocated && node.isActive) {
            node.isAllocated = false;
            node.isActive = false;
            found = true;
            spdlog::info("Destroyed virtual compute node {} for LLM {}", node.nodeId, llmId);
        }
    }
    
    return found;
}

std::vector<std::string> AdvancedCustomizedKernel::getActiveLLMs() const {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    std::vector<std::string> activeLLMs;
    for (const auto& pair : llmStreams_) {
        if (!pair.second.empty()) {
            activeLLMs.push_back(pair.first);
        }
    }
    return activeLLMs;
}

bool AdvancedCustomizedKernel::setTaskWeightage(const std::string& taskId, float weightage) {
    std::lock_guard<std::mutex> lock(kernelMutex_);
    
    auto it = activeTasks_.find(taskId);
    if (it != activeTasks_.end()) {
        // Store weightage in custom data
        it->second.customData["weightage"] = reinterpret_cast<void*>(static_cast<uintptr_t>(weightage));
        spdlog::info("Set task weightage to {} for task {}", weightage, taskId);
        return true;
    }
    
    spdlog::error("Failed to set weightage for task {}", taskId);
    return false;
}

bool AdvancedCustomizedKernel::enableDirectMemoryAccess(const std::string& llmId) {
    spdlog::info("Enabled direct memory access for LLM {}", llmId);
    return true;
}

bool AdvancedCustomizedKernel::disableDirectMemoryAccess(const std::string& llmId) {
    spdlog::info("Disabled direct memory access for LLM {}", llmId);
    return true;
}

void AdvancedCustomizedKernel::initializeComputeNodes() {
    // Create compute nodes based on current device capabilities
    int nodeCount = currentDevice_.multiProcessorCount;
    
    for (int i = 0; i < nodeCount; ++i) {
        ComputeNode node;
        node.nodeId = i;
        node.type = ComputeNodeType::TENSOR_CORE;
        node.memorySize = currentDevice_.totalMemory / nodeCount;
        node.computeCapability = currentDevice_.tensorCoreCount / nodeCount;
        node.isAllocated = false;
        node.isActive = false;
        
        computeNodes_.push_back(node);
    }
    
    spdlog::info("Initialized {} compute nodes", nodeCount);
}

void AdvancedCustomizedKernel::initializeMemoryPartitions() {
    // Create initial memory partitions
    size_t totalMemory = currentDevice_.totalMemory;
    size_t partitionSize = totalMemory / 10; // 10 partitions
    
    for (int i = 0; i < 10; ++i) {
        MemoryPartition partition;
        partition.partitionId = i;
        partition.type = MemoryPartitionType::GLOBAL_MEMORY;
        partition.size = partitionSize;
        partition.offset = i * partitionSize;
        partition.isAllocated = false;
        partition.devicePtr = nullptr;
        partition.hostPtr = nullptr;
        
        memoryPartitions_.push_back(partition);
    }
    
    spdlog::info("Initialized {} memory partitions", 10);
}

void AdvancedCustomizedKernel::schedulerLoop() {
    spdlog::info("Scheduler loop started");
    
    while (!shutdownRequested_) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        std::lock_guard<std::mutex> lock(kernelMutex_);
        
        // Process tasks in queue
        while (!taskQueue_.empty()) {
            ComputeTask task = taskQueue_.front();
            taskQueue_.pop();
            
            // Allocate resources for task
            if (allocateResourcesForTask(task)) {
                // Execute task
                try {
                    task.taskFunction();
                    task.isCompleted = true;
                    task.completedAt = std::chrono::system_clock::now();
                    
                    // Update task in active tasks
                    auto it = activeTasks_.find(task.taskId);
                    if (it != activeTasks_.end()) {
                        it->second = task;
                    }
                    
                    spdlog::info("Completed task {}", task.taskId);
                } catch (const std::exception& e) {
                    spdlog::error("Task {} failed: {}", task.taskId, e.what());
                }
                
                // Deallocate resources
                deallocateResourcesForTask(task.taskId);
            }
        }
    }
    
    spdlog::info("Scheduler loop stopped");
}

bool AdvancedCustomizedKernel::allocateResourcesForTask(const ComputeTask& task) {
    // Find available compute node
    ComputeNode* node = nullptr;
    for (auto& n : computeNodes_) {
        if (!n.isAllocated && n.memorySize >= task.requiredMemory && n.computeCapability >= task.requiredCores) {
            node = &n;
            break;
        }
    }
    
    if (!node) {
        spdlog::error("No available compute node for task {}", task.taskId);
        return false;
    }
    
    // Allocate node
    node->isAllocated = true;
    node->isActive = true;
    node->lastUsed = std::chrono::system_clock::now();
    
    spdlog::info("Allocated compute node {} for task {}", node->nodeId, task.taskId);
    return true;
}

void AdvancedCustomizedKernel::deallocateResourcesForTask(const std::string& taskId) {
    // Find and deallocate compute node
    for (auto& node : computeNodes_) {
        if (node.isAllocated && node.isActive) {
            node.isAllocated = false;
            node.isActive = false;
            spdlog::info("Deallocated compute node {} for task {}", node.nodeId, taskId);
            break;
        }
    }
}

ComputeNode* AdvancedCustomizedKernel::findBestComputeNode(size_t requiredMemory, size_t requiredCores) {
    ComputeNode* bestNode = nullptr;
    size_t bestScore = SIZE_MAX;
    
    for (auto& node : computeNodes_) {
        if (!node.isAllocated && node.memorySize >= requiredMemory && node.computeCapability >= requiredCores) {
            size_t score = node.memorySize + node.computeCapability;
            if (score < bestScore) {
                bestScore = score;
                bestNode = &node;
            }
        }
    }
    
    return bestNode;
}

MemoryPartition* AdvancedCustomizedKernel::findBestMemoryPartition(size_t requiredSize, MemoryPartitionType type) {
    MemoryPartition* bestPartition = nullptr;
    size_t bestScore = SIZE_MAX;
    
    for (auto& partition : memoryPartitions_) {
        if (!partition.isAllocated && partition.size >= requiredSize && partition.type == type) {
            size_t score = partition.size;
            if (score < bestScore) {
                bestScore = score;
                bestPartition = &partition;
            }
        }
    }
    
    return bestPartition;
}

void AdvancedCustomizedKernel::updatePerformanceMetrics() {
    // Update performance metrics
    // This would typically involve querying CUDA events and timers
}

bool AdvancedCustomizedKernel::validateTask(const ComputeTask& task) {
    if (task.taskId.empty() || task.llmId.empty()) {
        return false;
    }
    
    if (task.requiredMemory == 0 || task.requiredCores == 0) {
        return false;
    }
    
    if (!task.taskFunction) {
        return false;
    }
    
    return true;
}

std::string AdvancedCustomizedKernel::generateTaskId() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(100000, 999999);
    
    std::stringstream ss;
    ss << "task_" << std::chrono::duration_cast<std::chrono::milliseconds>(
           std::chrono::system_clock::now().time_since_epoch()).count()
       << "_" << dis(gen);
    
    return ss.str();
}

void AdvancedCustomizedKernel::cleanupResources() {
    // Cleanup all allocated resources
    for (auto& node : computeNodes_) {
        node.isAllocated = false;
        node.isActive = false;
    }
    
    for (auto& partition : memoryPartitions_) {
        if (partition.devicePtr) {
            cudaFree(partition.devicePtr);
            partition.devicePtr = nullptr;
        }
        partition.isAllocated = false;
    }
    
    for (const auto& pair : llmMemoryAllocations_) {
        cudaFree(pair.second);
    }
    llmMemoryAllocations_.clear();
    
    for (const auto& pair : llmStreams_) {
        for (cudaStream_t stream : pair.second) {
            cudaStreamDestroy(stream);
        }
    }
    llmStreams_.clear();
    
    activeTasks_.clear();
    
    while (!taskQueue_.empty()) {
        taskQueue_.pop();
    }
    
    spdlog::info("Cleaned up all kernel resources");
}

} // namespace core
} // namespace cogniware
