#include "compute_virtualization_manager.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <nvml.h>
#include <algorithm>
#include <chrono>
#include <thread>
#include <mutex>
#include <queue>
#include <unordered_map>
#include <memory>

namespace msmartcompute {

ComputeVirtualizationManager& ComputeVirtualizationManager::getInstance() {
    static ComputeVirtualizationManager instance;
    return instance;
}

bool ComputeVirtualizationManager::initialize(const ComputeVirtualizationConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_ = config;
    
    // Initialize NVML for GPU monitoring
    nvmlReturn_t nvmlStatus = nvmlInit();
    if (nvmlStatus != NVML_SUCCESS) {
        spdlog::error("Failed to initialize NVML: {}", nvmlErrorString(nvmlStatus));
        return false;
    }
    
    // Get number of GPUs
    unsigned int deviceCount;
    nvmlStatus = nvmlDeviceGetCount(&deviceCount);
    if (nvmlStatus != NVML_SUCCESS) {
        spdlog::error("Failed to get device count: {}", nvmlErrorString(nvmlStatus));
        return false;
    }
    
    if (config_.deviceId >= deviceCount) {
        spdlog::error("Invalid device ID: {} (max: {})", config_.deviceId, deviceCount - 1);
        return false;
    }
    
    // Initialize CUDA
    cudaError_t cudaStatus = cudaSetDevice(config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    // Get device properties
    cudaDeviceProp prop;
    cudaStatus = cudaGetDeviceProperties(&prop, config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to get device properties: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    deviceProps_ = prop;
    
    // Initialize NVML device handle
    nvmlStatus = nvmlDeviceGetHandleByIndex(config_.deviceId, &nvmlDevice_);
    if (nvmlStatus != NVML_SUCCESS) {
        spdlog::error("Failed to get NVML device handle: {}", nvmlErrorString(nvmlStatus));
        return false;
    }
    
    // Initialize compute units
    if (!initializeComputeUnits()) {
        spdlog::error("Failed to initialize compute units");
        return false;
    }
    
    // Initialize scheduler
    if (!initializeScheduler()) {
        spdlog::error("Failed to initialize scheduler");
        return false;
    }
    
    // Initialize load balancer
    if (!initializeLoadBalancer()) {
        spdlog::error("Failed to initialize load balancer");
        return false;
    }
    
    // Start monitoring thread
    running_ = true;
    monitoringThread_ = std::thread(&ComputeVirtualizationManager::monitoringLoop, this);
    
    spdlog::info("Compute Virtualization Manager initialized successfully");
    return true;
}

void ComputeVirtualizationManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!running_) return;
    
    running_ = false;
    
    // Stop monitoring thread
    if (monitoringThread_.joinable()) {
        monitoringThread_.join();
    }
    
    // Cleanup compute units
    cleanupComputeUnits();
    
    // Cleanup scheduler
    cleanupScheduler();
    
    // Cleanup load balancer
    cleanupLoadBalancer();
    
    // Shutdown NVML
    nvmlShutdown();
    
    spdlog::info("Compute Virtualization Manager shutdown completed");
}

bool ComputeVirtualizationManager::createVirtualComputeUnit(int virtualGPUId, const VirtualComputeUnitConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if virtual compute unit already exists
    if (virtualComputeUnits_.find(virtualGPUId) != virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} already exists", virtualGPUId);
        return false;
    }
    
    // Create virtual compute unit
    VirtualComputeUnit unit;
    unit.virtualGPUId = virtualGPUId;
    unit.config = config;
    unit.status = VirtualComputeUnitStatus::CREATED;
    unit.computeUtilization = 0.0f;
    unit.memoryUtilization = 0.0f;
    unit.activeKernels = 0;
    unit.totalKernelsExecuted = 0;
    
    // Allocate compute resources
    if (!allocateComputeResources(unit)) {
        spdlog::error("Failed to allocate compute resources for virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Create CUDA streams
    unit.streams.resize(config.numStreams);
    for (int i = 0; i < config.numStreams; ++i) {
        cudaError_t status = cudaStreamCreate(&unit.streams[i]);
        if (status != cudaSuccess) {
            spdlog::error("Failed to create stream for virtual GPU {}: {}", 
                         virtualGPUId, cudaGetErrorString(status));
            return false;
        }
    }
    
    // Create cuBLAS handle
    cublasStatus_t cublasStatus = cublasCreate(&unit.cublasHandle);
    if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuBLAS handle for virtual GPU {}: {}", 
                     virtualGPUId, cublasStatus);
        return false;
    }
    
    // Create cuDNN handle
    cudnnStatus_t cudnnStatus = cudnnCreate(&unit.cudnnHandle);
    if (cudnnStatus != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuDNN handle for virtual GPU {}: {}", 
                     virtualGPUId, cudnnGetErrorString(cudnnStatus));
        return false;
    }
    
    // Set tensor core mode if enabled
    if (config.enableTensorCores) {
        cublasStatus = cublasSetMathMode(unit.cublasHandle, CUBLAS_TENSOR_OP_MATH);
        if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
            spdlog::warn("Failed to enable tensor cores for virtual GPU {}: {}", 
                        virtualGPUId, cublasStatus);
        }
    }
    
    virtualComputeUnits_[virtualGPUId] = unit;
    
    spdlog::info("Virtual compute unit created for GPU {} with {} compute units", 
                 virtualGPUId, config.numComputeUnits);
    return true;
}

bool ComputeVirtualizationManager::destroyVirtualComputeUnit(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    // Destroy cuDNN handle
    cudnnDestroy(unit.cudnnHandle);
    
    // Destroy cuBLAS handle
    cublasDestroy(unit.cublasHandle);
    
    // Destroy CUDA streams
    for (auto stream : unit.streams) {
        cudaStreamDestroy(stream);
    }
    unit.streams.clear();
    
    // Free compute resources
    freeComputeResources(unit);
    
    virtualComputeUnits_.erase(it);
    
    spdlog::info("Virtual compute unit destroyed for GPU {}", virtualGPUId);
    return true;
}

bool ComputeVirtualizationManager::executeKernel(int virtualGPUId, 
                                                const KernelConfig& kernelConfig,
                                                int streamId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    if (streamId >= unit.streams.size()) {
        spdlog::error("Invalid stream ID {} for virtual GPU {}", streamId, virtualGPUId);
        return false;
    }
    
    // Check compute resource availability
    if (!checkComputeResourceAvailability(unit, kernelConfig)) {
        spdlog::error("Insufficient compute resources for kernel execution in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Schedule kernel execution
    KernelExecution execution;
    execution.kernelConfig = kernelConfig;
    execution.streamId = streamId;
    execution.startTime = std::chrono::steady_clock::now();
    execution.status = KernelExecutionStatus::QUEUED;
    
    // Add to execution queue
    unit.kernelQueue.push(execution);
    
    // Update statistics
    unit.activeKernels++;
    unit.totalKernelsExecuted++;
    
    // Update compute utilization
    unit.computeUtilization = std::min(1.0f, unit.computeUtilization + 0.05f);
    
    spdlog::debug("Kernel queued for execution in virtual GPU {} on stream {}", virtualGPUId, streamId);
    return true;
}

bool ComputeVirtualizationManager::synchronize(int virtualGPUId, int streamId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    if (streamId >= unit.streams.size()) {
        spdlog::error("Invalid stream ID {} for virtual GPU {}", streamId, virtualGPUId);
        return false;
    }
    
    // Synchronize stream
    cudaError_t status = cudaStreamSynchronize(unit.streams[streamId]);
    if (status != cudaSuccess) {
        spdlog::error("Failed to synchronize stream {} in virtual GPU {}: {}", 
                     streamId, virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    // Update kernel execution status
    updateKernelExecutionStatus(unit, streamId);
    
    return true;
}

VirtualComputeUnitInfo ComputeVirtualizationManager::getVirtualComputeUnitInfo(int virtualGPUId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    VirtualComputeUnitInfo info;
    info.virtualGPUId = virtualGPUId;
    info.status = VirtualComputeUnitStatus::NOT_FOUND;
    info.computeUtilization = 0.0f;
    info.memoryUtilization = 0.0f;
    info.activeKernels = 0;
    info.totalKernelsExecuted = 0;
    info.numStreams = 0;
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        return info;
    }
    
    const VirtualComputeUnit& unit = it->second;
    info.status = unit.status;
    info.computeUtilization = unit.computeUtilization;
    info.memoryUtilization = unit.memoryUtilization;
    info.activeKernels = unit.activeKernels;
    info.totalKernelsExecuted = unit.totalKernelsExecuted;
    info.numStreams = unit.streams.size();
    info.numComputeUnits = unit.config.numComputeUnits;
    
    return info;
}

std::vector<VirtualComputeUnitInfo> ComputeVirtualizationManager::getAllVirtualComputeUnitInfo() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<VirtualComputeUnitInfo> infos;
    infos.reserve(virtualComputeUnits_.size());
    
    for (const auto& pair : virtualComputeUnits_) {
        infos.push_back(getVirtualComputeUnitInfo(pair.first));
    }
    
    return infos;
}

bool ComputeVirtualizationManager::setComputeShare(int virtualGPUId, float computeShare) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    if (computeShare < 0.0f || computeShare > 1.0f) {
        spdlog::error("Invalid compute share: {} (must be between 0.0 and 1.0)", computeShare);
        return false;
    }
    
    unit.config.computeShare = computeShare;
    
    // Update scheduler
    scheduler_->updateComputeShare(virtualGPUId, computeShare);
    
    spdlog::info("Compute share updated for virtual GPU {}: {:.2f}%", virtualGPUId, computeShare * 100.0f);
    return true;
}

bool ComputeVirtualizationManager::enableTensorCores(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    cublasStatus_t status = cublasSetMathMode(unit.cublasHandle, CUBLAS_TENSOR_OP_MATH);
    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to enable tensor cores for virtual GPU {}: {}", virtualGPUId, status);
        return false;
    }
    
    unit.config.enableTensorCores = true;
    
    spdlog::info("Tensor cores enabled for virtual GPU {}", virtualGPUId);
    return true;
}

bool ComputeVirtualizationManager::disableTensorCores(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualComputeUnits_.find(virtualGPUId);
    if (it == virtualComputeUnits_.end()) {
        spdlog::error("Virtual compute unit for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualComputeUnit& unit = it->second;
    
    cublasStatus_t status = cublasSetMathMode(unit.cublasHandle, CUBLAS_DEFAULT_MATH);
    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to disable tensor cores for virtual GPU {}: {}", virtualGPUId, status);
        return false;
    }
    
    unit.config.enableTensorCores = false;
    
    spdlog::info("Tensor cores disabled for virtual GPU {}", virtualGPUId);
    return true;
}

bool ComputeVirtualizationManager::initializeComputeUnits() {
    // Initialize compute unit management
    computeUnitManager_ = std::make_unique<ComputeUnitManager>();
    
    if (!computeUnitManager_->initialize(deviceProps_.multiProcessorCount, config_.maxVirtualComputeUnits)) {
        spdlog::error("Failed to initialize compute unit manager");
        return false;
    }
    
    spdlog::info("Compute units initialized with {} physical compute units", deviceProps_.multiProcessorCount);
    return true;
}

bool ComputeVirtualizationManager::initializeScheduler() {
    // Initialize compute scheduler
    scheduler_ = std::make_unique<ComputeScheduler>();
    
    if (!scheduler_->initialize(config_.schedulingPolicy, config_.timeSlice)) {
        spdlog::error("Failed to initialize compute scheduler");
        return false;
    }
    
    spdlog::info("Compute scheduler initialized with policy {}", config_.schedulingPolicy);
    return true;
}

bool ComputeVirtualizationManager::initializeLoadBalancer() {
    // Initialize load balancer
    loadBalancer_ = std::make_unique<LoadBalancer>();
    
    if (!loadBalancer_->initialize(config_.loadBalancingStrategy)) {
        spdlog::error("Failed to initialize load balancer");
        return false;
    }
    
    spdlog::info("Load balancer initialized with strategy {}", config_.loadBalancingStrategy);
    return true;
}

void ComputeVirtualizationManager::cleanupComputeUnits() {
    if (computeUnitManager_) {
        computeUnitManager_->shutdown();
        computeUnitManager_.reset();
    }
}

void ComputeVirtualizationManager::cleanupScheduler() {
    if (scheduler_) {
        scheduler_->shutdown();
        scheduler_.reset();
    }
}

void ComputeVirtualizationManager::cleanupLoadBalancer() {
    if (loadBalancer_) {
        loadBalancer_->shutdown();
        loadBalancer_.reset();
    }
}

void ComputeVirtualizationManager::monitoringLoop() {
    while (running_) {
        // Update GPU utilization
        updateGPUUtilization();
        
        // Update compute unit statistics
        updateComputeUnitStatistics();
        
        // Perform load balancing
        performLoadBalancing();
        
        // Process kernel queue
        processKernelQueue();
        
        // Sleep for monitoring interval
        std::this_thread::sleep_for(std::chrono::milliseconds(config_.monitoringInterval));
    }
}

void ComputeVirtualizationManager::updateGPUUtilization() {
    unsigned int utilization;
    nvmlReturn_t status = nvmlDeviceGetUtilizationRates(nvmlDevice_, &utilization);
    if (status == NVML_SUCCESS) {
        gpuUtilization_ = static_cast<float>(utilization) / 100.0f;
    }
}

void ComputeVirtualizationManager::updateComputeUnitStatistics() {
    for (auto& pair : virtualComputeUnits_) {
        VirtualComputeUnit& unit = pair.second;
        
        // Update compute utilization (decay over time)
        unit.computeUtilization = std::max(0.0f, unit.computeUtilization - 0.01f);
        
        // Update active kernels count
        unit.activeKernels = 0;
        for (auto stream : unit.streams) {
            cudaError_t status = cudaStreamQuery(stream);
            if (status == cudaErrorNotReady) {
                unit.activeKernels++;
            }
        }
    }
}

void ComputeVirtualizationManager::performLoadBalancing() {
    if (!loadBalancer_) return;
    
    // Get current load distribution
    std::vector<LoadInfo> loadInfos;
    for (const auto& pair : virtualComputeUnits_) {
        const VirtualComputeUnit& unit = pair.second;
        LoadInfo info;
        info.virtualGPUId = unit.virtualGPUId;
        info.computeUtilization = unit.computeUtilization;
        info.activeKernels = unit.activeKernels;
        loadInfos.push_back(info);
    }
    
    // Perform load balancing
    auto balancingActions = loadBalancer_->balance(loadInfos);
    
    // Apply balancing actions
    for (const auto& action : balancingActions) {
        applyLoadBalancingAction(action);
    }
}

void ComputeVirtualizationManager::processKernelQueue() {
    for (auto& pair : virtualComputeUnits_) {
        VirtualComputeUnit& unit = pair.second;
        
        while (!unit.kernelQueue.empty()) {
            KernelExecution& execution = unit.kernelQueue.front();
            
            // Check if kernel can be executed
            if (canExecuteKernel(unit, execution)) {
                // Execute kernel
                if (executeKernelOnDevice(unit, execution)) {
                    execution.status = KernelExecutionStatus::RUNNING;
                    execution.startTime = std::chrono::steady_clock::now();
                } else {
                    execution.status = KernelExecutionStatus::FAILED;
                }
                
                unit.kernelQueue.pop();
            } else {
                // Kernel cannot be executed yet, keep in queue
                break;
            }
        }
    }
}

bool ComputeVirtualizationManager::allocateComputeResources(VirtualComputeUnit& unit) {
    // Allocate compute units from the manager
    if (!computeUnitManager_->allocateComputeUnits(unit.virtualGPUId, unit.config.numComputeUnits)) {
        spdlog::error("Failed to allocate compute units for virtual GPU {}", unit.virtualGPUId);
        return false;
    }
    
    return true;
}

void ComputeVirtualizationManager::freeComputeResources(VirtualComputeUnit& unit) {
    // Free compute units
    computeUnitManager_->freeComputeUnits(unit.virtualGPUId);
}

bool ComputeVirtualizationManager::checkComputeResourceAvailability(const VirtualComputeUnit& unit, 
                                                                   const KernelConfig& kernelConfig) {
    // Check if enough compute resources are available
    return unit.activeKernels < unit.config.maxConcurrentKernels;
}

void ComputeVirtualizationManager::updateKernelExecutionStatus(VirtualComputeUnit& unit, int streamId) {
    // Update kernel execution status based on stream completion
    for (auto& execution : unit.kernelExecutions) {
        if (execution.streamId == streamId && execution.status == KernelExecutionStatus::RUNNING) {
            execution.status = KernelExecutionStatus::COMPLETED;
            execution.endTime = std::chrono::steady_clock::now();
            unit.activeKernels--;
        }
    }
}

bool ComputeVirtualizationManager::canExecuteKernel(const VirtualComputeUnit& unit, 
                                                   const KernelExecution& execution) {
    // Check if kernel can be executed based on resource availability
    return unit.activeKernels < unit.config.maxConcurrentKernels;
}

bool ComputeVirtualizationManager::executeKernelOnDevice(VirtualComputeUnit& unit, 
                                                        KernelExecution& execution) {
    // Execute kernel on the device
    // This is a simplified implementation - in practice, you would launch actual CUDA kernels
    cudaError_t status = cudaSuccess; // Placeholder for actual kernel execution
    
    if (status != cudaSuccess) {
        spdlog::error("Failed to execute kernel on virtual GPU {}: {}", 
                     unit.virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    return true;
}

void ComputeVirtualizationManager::applyLoadBalancingAction(const LoadBalancingAction& action) {
    // Apply load balancing action
    switch (action.type) {
        case LoadBalancingActionType::MIGRATE_KERNEL:
            migrateKernel(action.sourceGPUId, action.targetGPUId, action.kernelId);
            break;
        case LoadBalancingActionType::ADJUST_COMPUTE_SHARE:
            setComputeShare(action.targetGPUId, action.computeShare);
            break;
        default:
            spdlog::warn("Unknown load balancing action type");
            break;
    }
}

void ComputeVirtualizationManager::migrateKernel(int sourceGPUId, int targetGPUId, int kernelId) {
    // Migrate kernel from source to target GPU
    spdlog::info("Migrating kernel {} from virtual GPU {} to {}", kernelId, sourceGPUId, targetGPUId);
    // Implementation would involve moving kernel execution context
}

} // namespace msmartcompute 