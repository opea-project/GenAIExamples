#include "virtual_compute_node_manager.h"
#include "cuda_memory_manager.h"
#include "cuda_kernel_manager.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <chrono>
#include <numeric>
#include <cmath>

namespace cogniware {

VirtualComputeNodeManager& VirtualComputeNodeManager::getInstance() {
    static VirtualComputeNodeManager instance;
    return instance;
}

bool VirtualComputeNodeManager::initialize(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_ = config;
    running_ = true;
    monitoringEnabled_ = false;

    // Set CUDA device
    cudaError_t status = cudaSetDevice(config.deviceId);
    if (status != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(status));
        return false;
    }

    // Initialize CUDA streams
    streams_.resize(config.numStreams);
    for (int i = 0; i < config.numStreams; ++i) {
        status = cudaStreamCreate(&streams_[i]);
        if (status != cudaSuccess) {
            spdlog::error("Failed to create CUDA stream: {}", cudaGetErrorString(status));
            return false;
        }
    }

    // Initialize memory manager
    MemoryPoolConfig memConfig;
    memConfig.deviceId = config.deviceId;
    memConfig.strategy = config.memoryStrategy;
    memConfig.initialPoolSize = config.memoryLimit;
    memConfig.minBlockSize = config.minBlockSize;
    memConfig.numStreamingBuffers = config.numStreams;
    
    if (!CUDAMemoryManager::getInstance().initialize(memConfig)) {
        spdlog::error("Failed to initialize memory manager");
        return false;
    }

    // Initialize kernel manager
    KernelConfig kernelConfig;
    kernelConfig.deviceId = config.deviceId;
    kernelConfig.useTensorCores = config.useTensorCores;
    kernelConfig.numStreams = config.numStreams;
    
    if (!CUDAKernelManager::getInstance().initialize(kernelConfig)) {
        spdlog::error("Failed to initialize kernel manager");
        return false;
    }

    // Start resource manager thread
    resourceManagerThread_ = std::thread(&VirtualComputeNodeManager::resourceManagerLoop, this);

    return true;
}

void VirtualComputeNodeManager::shutdown() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        running_ = false;
    }

    if (resourceManagerThread_.joinable()) {
        resourceManagerThread_.join();
    }

    // Stop all training
    for (const auto& model : activeModels_) {
        stopTraining(model.first);
    }

    // Cleanup CUDA streams
    for (auto stream : streams_) {
        cudaStreamDestroy(stream);
    }
    streams_.clear();

    // Cleanup managers
    CUDAKernelManager::getInstance().shutdown();
    CUDAMemoryManager::getInstance().shutdown();
}

bool VirtualComputeNodeManager::setNodeConfig(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (config.deviceId != config_.deviceId) {
        cudaError_t status = cudaSetDevice(config.deviceId);
        if (status != cudaSuccess) {
            spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(status));
            return false;
        }
    }

    if (config.numStreams != config_.numStreams) {
        // Cleanup existing streams
        for (auto stream : streams_) {
            cudaStreamDestroy(stream);
        }
        streams_.clear();

        // Create new streams
        streams_.resize(config.numStreams);
        for (int i = 0; i < config.numStreams; ++i) {
            cudaError_t status = cudaStreamCreate(&streams_[i]);
            if (status != cudaSuccess) {
                spdlog::error("Failed to create CUDA stream: {}", cudaGetErrorString(status));
                return false;
            }
        }
    }

    // Update memory manager config
    MemoryPoolConfig memConfig;
    memConfig.deviceId = config.deviceId;
    memConfig.strategy = config.memoryStrategy;
    memConfig.initialPoolSize = config.memoryLimit;
    memConfig.minBlockSize = config.minBlockSize;
    memConfig.numStreamingBuffers = config.numStreams;
    
    if (!CUDAMemoryManager::getInstance().initialize(memConfig)) {
        spdlog::error("Failed to update memory manager config");
        return false;
    }
    
    // Update kernel manager config
    KernelConfig kernelConfig;
    kernelConfig.deviceId = config.deviceId;
    kernelConfig.useTensorCores = config.useTensorCores;
    kernelConfig.numStreams = config.numStreams;
    
    if (!CUDAKernelManager::getInstance().setKernelConfig(kernelConfig)) {
        spdlog::error("Failed to update kernel manager config");
        return false;
    }
    
    config_ = config;
    return true;
}

VirtualNodeConfig VirtualComputeNodeManager::getNodeConfig() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

VirtualNodeStatus VirtualComputeNodeManager::getNodeStatus() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return currentStatus_;
}

bool VirtualComputeNodeManager::loadModel(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (activeModels_.size() >= config_.maxConcurrentModels) {
        spdlog::warn("Maximum number of concurrent models reached");
        modelQueue_.push(config.modelId);
        return false;
    }

    if (!checkResourceAvailability(config)) {
        spdlog::warn("Insufficient resources for model: {}", config.modelId);
        modelQueue_.push(config.modelId);
        return false;
    }

    ModelInfo info;
    info.config = config;
    info.isTraining = false;
    info.isPaused = false;
    info.stream = streams_[activeModels_.size() % streams_.size()];
    info.modelData = nullptr;

    activeModels_[config.modelId] = info;
    updateNodeStatus();

    return true;
}

bool VirtualComputeNodeManager::unloadModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        spdlog::error("Model not found: {}", modelId);
        return false;
    }

    if (it->second.isTraining) {
        stopTraining(modelId);
    }

    releaseResources(modelId);
    activeModels_.erase(it);
    updateNodeStatus();

    // Process queued models
    processModelQueue();

    return true;
}

bool VirtualComputeNodeManager::startTraining(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        spdlog::error("Model not found: {}", modelId);
        return false;
    }

    if (it->second.isTraining) {
        spdlog::warn("Model is already training: {}", modelId);
        return false;
    }

    if (!allocateResources(it->second.config)) {
        spdlog::error("Failed to allocate resources for model: {}", modelId);
        return false;
    }

    it->second.isTraining = true;
    it->second.isPaused = false;
    updateNodeStatus();

    return true;
}

bool VirtualComputeNodeManager::stopTraining(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        spdlog::error("Model not found: {}", modelId);
        return false;
    }

    if (!it->second.isTraining) {
        spdlog::warn("Model is not training: {}", modelId);
        return false;
    }

    releaseResources(modelId);
    it->second.isTraining = false;
    it->second.isPaused = false;
    updateNodeStatus();

    return true;
}

bool VirtualComputeNodeManager::pauseTraining(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        spdlog::error("Model not found: {}", modelId);
        return false;
    }

    if (!it->second.isTraining) {
        spdlog::warn("Model is not training: {}", modelId);
        return false;
    }

    if (it->second.isPaused) {
        spdlog::warn("Model is already paused: {}", modelId);
        return false;
    }

    it->second.isPaused = true;
    updateNodeStatus();

    return true;
}

bool VirtualComputeNodeManager::resumeTraining(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        spdlog::error("Model not found: {}", modelId);
        return false;
    }

    if (!it->second.isTraining) {
        spdlog::warn("Model is not training: {}", modelId);
        return false;
    }

    if (!it->second.isPaused) {
        spdlog::warn("Model is not paused: {}", modelId);
        return false;
    }

    it->second.isPaused = false;
    updateNodeStatus();

    return true;
}

bool VirtualComputeNodeManager::allocateResources(const ModelConfig& config) {
    const auto& modelId = config.modelId;
    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        return false;
    }

    const auto& modelConfig = config;
    void* modelData = CUDAMemoryManager::getInstance().allocate(
        modelConfig.memoryRequirement,
        "model_" + modelId,
        it->second.stream
    );

    if (!modelData) {
        spdlog::error("Failed to allocate memory for model: {}", modelId);
        return false;
    }

    it->second.modelData = modelData;
    return true;
}

void VirtualComputeNodeManager::releaseResources(const std::string& modelId) {
    auto it = activeModels_.find(modelId);
    if (it == activeModels_.end()) {
        return;
    }

    if (it->second.modelData) {
        CUDAMemoryManager::getInstance().free(it->second.modelData);
        it->second.modelData = nullptr;
    }
}

bool VirtualComputeNodeManager::checkResourceAvailability(const ModelConfig& config) const {
    size_t freeMemory = CUDAMemoryManager::getInstance().getFreeMemory();
    return freeMemory >= config.memoryRequirement;
}

void VirtualComputeNodeManager::optimizeResourceUsage() {
    std::lock_guard<std::mutex> lock(mutex_);

    // Defragment memory if utilization is high
    float utilization = static_cast<float>(currentStatus_.usedMemory) / currentStatus_.totalMemory;
    if (utilization > config_.memoryUtilizationTarget) {
        CUDAMemoryManager::getInstance().defragment();
    }

    // Balance load across streams
    balanceLoad();
}

void VirtualComputeNodeManager::resourceManagerLoop() {
    while (running_) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            processModelQueue();
            optimizeResourceUsage();
            updateNodeStatus();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void VirtualComputeNodeManager::processModelQueue() {
    while (!modelQueue_.empty()) {
        const std::string& modelId = modelQueue_.front();
        auto it = activeModels_.find(modelId);
        
        if (it != activeModels_.end() && checkResourceAvailability(it->second.config)) {
            if (allocateResources(it->second.config)) {
                modelQueue_.pop();
                continue;
            }
        }
        break;
    }
}

void VirtualComputeNodeManager::balanceLoad() {
    // Distribute models across streams based on priority
    std::vector<std::pair<std::string, int>> modelPriorities;
    for (const auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            modelPriorities.push_back({model.first, model.second.config.priority});
        }
    }

    std::sort(modelPriorities.begin(), modelPriorities.end(),
        [](const auto& a, const auto& b) { return a.second > b.second; });

    for (size_t i = 0; i < modelPriorities.size(); ++i) {
        auto it = activeModels_.find(modelPriorities[i].first);
        if (it != activeModels_.end()) {
            it->second.stream = streams_[i % streams_.size()];
        }
    }
}

void VirtualComputeNodeManager::optimizeMemoryUsage() {
    // Implement memory optimization strategies
    // 1. Release unused memory
    // 2. Compact memory blocks
    // 3. Adjust batch sizes if needed
}

void VirtualComputeNodeManager::updateNodeStatus() {
    currentStatus_.totalMemory = CUDAMemoryManager::getInstance().getTotalMemory();
    currentStatus_.usedMemory = CUDAMemoryManager::getInstance().getUsedMemory();
    currentStatus_.freeMemory = CUDAMemoryManager::getInstance().getFreeMemory();
    currentStatus_.activeModels = activeModels_.size();
    currentStatus_.runningModels.clear();

    for (const auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            currentStatus_.runningModels.push_back(model.first);
        }
    }

    // Get GPU utilization
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, config_.deviceId);
    currentStatus_.gpuUtilization = prop.clockRate * prop.multiProcessorCount;

    if (monitoringEnabled_ && statusCallback_) {
        statusCallback_(currentStatus_);
    }
}

void VirtualComputeNodeManager::setStatusCallback(std::function<void(const VirtualNodeStatus&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    statusCallback_ = callback;
}

void VirtualComputeNodeManager::enableMonitoring(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    monitoringEnabled_ = enable;
}

void VirtualComputeNodeManager::printNodeStats() const {
    std::lock_guard<std::mutex> lock(mutex_);

    spdlog::info("Virtual Node Stats:");
    spdlog::info("  Device ID: {}", config_.deviceId);
    spdlog::info("  Total Memory: {} bytes", currentStatus_.totalMemory);
    spdlog::info("  Used Memory: {} bytes", currentStatus_.usedMemory);
    spdlog::info("  Free Memory: {} bytes", currentStatus_.freeMemory);
    spdlog::info("  Active Models: {}", currentStatus_.activeModels);
    spdlog::info("  GPU Utilization: {:.2f}%", currentStatus_.gpuUtilization);
    spdlog::info("  Running Models:");
    for (const auto& modelId : currentStatus_.runningModels) {
        spdlog::info("    - {}", modelId);
    }
}

void VirtualComputeNodeManager::optimizeResourceAllocation() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!config_.enableAutoScaling) {
        return;
    }

    // Check resource utilization
    if (checkResourceThresholds()) {
        scaleResources();
    }

    // Optimize memory layout
    optimizeMemoryLayout();

    // Balance resource utilization
    balanceResourceUtilization();

    // Optimize model configurations
    optimizeModelConfigurations();
}

void VirtualComputeNodeManager::scaleResources() {
    if (!canScaleResources()) {
        return;
    }

    // Scale memory if utilization is high
    if (isMemoryUtilizationHigh()) {
        scaleMemory();
    }

    // Scale tensor cores if utilization is high
    if (isTensorCoreUtilizationHigh()) {
        scaleTensorCores();
    }

    // Scale CPU threads if utilization is high
    if (isCPUUtilizationHigh()) {
        scaleCPUThreads();
    }

    // Scale storage if utilization is high
    if (isStorageUtilizationHigh()) {
        scaleStorage();
    }
}

void VirtualComputeNodeManager::balanceResourceUtilization() {
    // Calculate average utilization
    float avgUtilization = (currentMetrics_.memoryUtilization +
                          currentMetrics_.gpuUtilization +
                          currentMetrics_.cpuUtilization +
                          currentMetrics_.tensorCoreUtilization) / 4.0f;

    // Adjust resource allocation based on utilization
    for (auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            // Adjust batch size
            if (model.second.config.enableDynamicBatchSize) {
                adjustBatchSizes();
            }

            // Manage gradient accumulation
            if (model.second.config.enableGradientAccumulation) {
                manageGradientAccumulation();
            }
        }
    }
}

void VirtualComputeNodeManager::optimizeModelConfigurations() {
    for (auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            // Optimize model parameters based on performance metrics
            auto& metrics = currentMetrics_.modelMetrics;
            if (!metrics.empty()) {
                float avgMetric = std::accumulate(metrics.begin(), metrics.end(), 0.0f) / metrics.size();
                
                // Adjust learning rate
                if (avgMetric > 0.85f) {
                    // Reduce learning rate
                    model.second.config.minAccuracy *= 0.95f;
                } else if (avgMetric < 0.5f) {
                    // Increase learning rate
                    model.second.config.minAccuracy *= 1.05f;
                }

                // Adjust batch size
                if (model.second.config.enableDynamicBatchSize) {
                    if (avgMetric > 0.85f) {
                        model.second.config.batchSize = std::min(
                            model.second.config.batchSize * 2,
                            config_.batchSize
                        );
                    } else if (avgMetric < 0.5f) {
                        model.second.config.batchSize = std::max(
                            model.second.config.batchSize / 2,
                            1
                        );
                    }
                }
            }
        }
    }
}

void VirtualComputeNodeManager::adjustBatchSizes() {
    for (auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            float utilization = currentMetrics_.gpuUtilization;
            
            if (utilization > 0.85f) {
                // Reduce batch size to decrease GPU utilization
                model.second.config.batchSize = std::max(
                    model.second.config.batchSize / 2,
                    1
                );
            } else if (utilization < 0.5f) {
                // Increase batch size to increase GPU utilization
                model.second.config.batchSize = std::min(
                    model.second.config.batchSize * 2,
                    config_.batchSize
                );
            }
        }
    }
}

void VirtualComputeNodeManager::manageGradientAccumulation() {
    for (auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            float utilization = currentMetrics_.memoryUtilization;
            
            if (utilization > 0.85f) {
                // Increase gradient accumulation steps to reduce memory usage
                model.second.config.gradientAccumulationSteps = std::min(
                    model.second.config.gradientAccumulationSteps * 2,
                    32
                );
            } else if (utilization < 0.5f) {
                // Decrease gradient accumulation steps to increase memory usage
                model.second.config.gradientAccumulationSteps = std::max(
                    model.second.config.gradientAccumulationSteps / 2,
                    1
                );
            }
        }
    }
}

void VirtualComputeNodeManager::optimizeMemoryLayout() {
    // Defragment memory if utilization is high
    if (isMemoryUtilizationHigh()) {
        CUDAMemoryManager::getInstance().defragment();
    }

    // Clean up unused resources
    cleanupUnusedResources();
}

void VirtualComputeNodeManager::cleanupUnusedResources() {
    for (auto it = activeModels_.begin(); it != activeModels_.end();) {
        if (!it->second.isTraining && !it->second.isPaused) {
            releaseResources(it->first);
            it = activeModels_.erase(it);
        } else {
            ++it;
        }
    }
}

void VirtualComputeNodeManager::monitorResourceUtilization() {
    if (!monitoringState_.isMonitoring) {
        return;
    }

    auto now = std::chrono::steady_clock::now();
    if (now - monitoringState_.lastMonitoringTime < 
        std::chrono::milliseconds(monitoringState_.monitoringInterval)) {
        return;
    }

    // Update current metrics
    updateResourceMetrics();

    // Track historical metrics
    historicalMetrics_.push_back(currentMetrics_);
    if (historicalMetrics_.size() > 100) {
        historicalMetrics_.erase(historicalMetrics_.begin());
    }

    // Analyze performance metrics
    analyzePerformanceMetrics();

    // Predict resource needs
    predictResourceNeeds();

    // Generate resource report
    generateResourceReport();

    monitoringState_.lastMonitoringTime = now;
}

void VirtualComputeNodeManager::updateResourceMetrics() {
    // Update memory metrics
    currentMetrics_.memoryUtilization = static_cast<float>(currentStatus_.usedMemory) / 
                                      currentStatus_.totalMemory;

    // Update GPU metrics
    currentMetrics_.gpuUtilization = currentStatus_.gpuUtilization;

    // Update CPU metrics
    currentMetrics_.cpuUtilization = currentStatus_.cpuUtilization;

    // Update tensor core metrics
    currentMetrics_.tensorCoreUtilization = currentStatus_.tensorCoreUtilization;

    // Update storage metrics
    currentMetrics_.storageUtilization = static_cast<float>(currentStatus_.usedStorage) / 
                                       currentStatus_.totalStorage;

    // Update model metrics
    currentMetrics_.modelMetrics.clear();
    for (const auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            float modelMetric = (model.second.config.minAccuracy + 
                               model.second.config.maxAccuracy) / 2.0f;
            currentMetrics_.modelMetrics.push_back(modelMetric);
        }
    }
}

void VirtualComputeNodeManager::analyzePerformanceMetrics() {
    if (historicalMetrics_.empty()) {
        return;
    }

    // Calculate moving averages
    std::vector<float> memoryUtilizations;
    std::vector<float> gpuUtilizations;
    std::vector<float> cpuUtilizations;
    std::vector<float> tensorCoreUtilizations;
    std::vector<float> storageUtilizations;

    for (const auto& metrics : historicalMetrics_) {
        memoryUtilizations.push_back(metrics.memoryUtilization);
        gpuUtilizations.push_back(metrics.gpuUtilization);
        cpuUtilizations.push_back(metrics.cpuUtilization);
        tensorCoreUtilizations.push_back(metrics.tensorCoreUtilization);
        storageUtilizations.push_back(metrics.storageUtilization);
    }

    // Calculate trends
    float memoryTrend = calculateTrend(memoryUtilizations);
    float gpuTrend = calculateTrend(gpuUtilizations);
    float cpuTrend = calculateTrend(cpuUtilizations);
    float tensorCoreTrend = calculateTrend(tensorCoreUtilizations);
    float storageTrend = calculateTrend(storageUtilizations);

    // Update scaling state based on trends
    if (memoryTrend > 0.1f || gpuTrend > 0.1f || cpuTrend > 0.1f || 
        tensorCoreTrend > 0.1f || storageTrend > 0.1f) {
        scalingState_.scalingFactor = 1.1f;
    } else if (memoryTrend < -0.1f || gpuTrend < -0.1f || cpuTrend < -0.1f || 
               tensorCoreTrend < -0.1f || storageTrend < -0.1f) {
        scalingState_.scalingFactor = 0.9f;
    }
}

float VirtualComputeNodeManager::calculateTrend(const std::vector<float>& values) {
    if (values.size() < 2) {
        return 0.0f;
    }

    float sum = 0.0f;
    for (size_t i = 1; i < values.size(); ++i) {
        sum += values[i] - values[i-1];
    }

    return sum / (values.size() - 1);
}

void VirtualComputeNodeManager::predictResourceNeeds() {
    if (historicalMetrics_.empty()) {
        return;
    }

    // Predict future resource needs based on historical data
    float predictedMemoryUtilization = predictNextValue(
        [](const ResourceMetrics& m) { return m.memoryUtilization; }
    );
    float predictedGPUUtilization = predictNextValue(
        [](const ResourceMetrics& m) { return m.gpuUtilization; }
    );
    float predictedCPUUtilization = predictNextValue(
        [](const ResourceMetrics& m) { return m.cpuUtilization; }
    );
    float predictedTensorCoreUtilization = predictNextValue(
        [](const ResourceMetrics& m) { return m.tensorCoreUtilization; }
    );
    float predictedStorageUtilization = predictNextValue(
        [](const ResourceMetrics& m) { return m.storageUtilization; }
    );

    // Update scaling state based on predictions
    if (predictedMemoryUtilization > 0.85f || predictedGPUUtilization > 0.85f ||
        predictedCPUUtilization > 0.85f || predictedTensorCoreUtilization > 0.85f ||
        predictedStorageUtilization > 0.85f) {
        scalingState_.scalingFactor = 1.2f;
    }
}

float VirtualComputeNodeManager::predictNextValue(
    std::function<float(const ResourceMetrics&)> getter) {
    if (historicalMetrics_.size() < 2) {
        return 0.0f;
    }

    std::vector<float> values;
    for (const auto& metrics : historicalMetrics_) {
        values.push_back(getter(metrics));
    }

    // Simple linear regression
    float sumX = 0.0f;
    float sumY = 0.0f;
    float sumXY = 0.0f;
    float sumXX = 0.0f;
    int n = values.size();

    for (int i = 0; i < n; ++i) {
        sumX += i;
        sumY += values[i];
        sumXY += i * values[i];
        sumXX += i * i;
    }

    float slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    float intercept = (sumY - slope * sumX) / n;

    return slope * n + intercept;
}

void VirtualComputeNodeManager::generateResourceReport() {
    spdlog::info("Resource Utilization Report:");
    spdlog::info("  Memory Utilization: {:.2f}%", currentMetrics_.memoryUtilization * 100.0f);
    spdlog::info("  GPU Utilization: {:.2f}%", currentMetrics_.gpuUtilization * 100.0f);
    spdlog::info("  CPU Utilization: {:.2f}%", currentMetrics_.cpuUtilization * 100.0f);
    spdlog::info("  Tensor Core Utilization: {:.2f}%", currentMetrics_.tensorCoreUtilization * 100.0f);
    spdlog::info("  Storage Utilization: {:.2f}%", currentMetrics_.storageUtilization * 100.0f);
    
    spdlog::info("Active Models: {}", activeModels_.size());
    for (const auto& model : activeModels_) {
        if (model.second.isTraining && !model.second.isPaused) {
            spdlog::info("  Model {}:", model.first);
            spdlog::info("    Batch Size: {}", model.second.config.batchSize);
            spdlog::info("    Gradient Accumulation Steps: {}", 
                        model.second.config.gradientAccumulationSteps);
        }
    }
}

} // namespace cogniware 