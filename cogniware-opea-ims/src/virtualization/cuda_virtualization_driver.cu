#include "cuda_virtualization_driver.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <nvml.h>
#include <algorithm>
#include <chrono>
#include <thread>
#include <mutex>
#include <queue>
#include <unordered_map>
#include <memory>

namespace msmartcompute {

// CUDA Virtualization Driver Implementation
CUDAVirtualizationDriver& CUDAVirtualizationDriver::getInstance() {
    static CUDAVirtualizationDriver instance;
    return instance;
}

bool CUDAVirtualizationDriver::initialize(const VirtualizationConfig& config) {
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
    
    // Initialize cuBLAS
    cublasStatus_t cublasStatus = cublasCreate(&cublasHandle_);
    if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuBLAS handle: {}", cublasStatus);
        return false;
    }
    
    // Initialize cuDNN
    cudnnStatus_t cudnnStatus = cudnnCreate(&cudnnHandle_);
    if (cudnnStatus != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuDNN handle: {}", cudnnGetErrorString(cudnnStatus));
        return false;
    }
    
    // Create CUDA streams for virtualization
    streams_.resize(config_.numVirtualStreams);
    for (int i = 0; i < config_.numVirtualStreams; ++i) {
        cudaStatus = cudaStreamCreate(&streams_[i]);
        if (cudaStatus != cudaSuccess) {
            spdlog::error("Failed to create CUDA stream {}: {}", i, cudaGetErrorString(cudaStatus));
            return false;
        }
    }
    
    // Initialize virtual GPU contexts
    if (!initializeVirtualGPUContexts()) {
        spdlog::error("Failed to initialize virtual GPU contexts");
        return false;
    }
    
    // Initialize memory virtualization
    if (!initializeMemoryVirtualization()) {
        spdlog::error("Failed to initialize memory virtualization");
        return false;
    }
    
    // Initialize compute virtualization
    if (!initializeComputeVirtualization()) {
        spdlog::error("Failed to initialize compute virtualization");
        return false;
    }
    
    // Start monitoring thread
    running_ = true;
    monitoringThread_ = std::thread(&CUDAVirtualizationDriver::monitoringLoop, this);
    
    spdlog::info("CUDA Virtualization Driver initialized successfully");
    return true;
}

void CUDAVirtualizationDriver::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!running_) return;
    
    running_ = false;
    
    // Stop monitoring thread
    if (monitoringThread_.joinable()) {
        monitoringThread_.join();
    }
    
    // Cleanup virtual GPU contexts
    cleanupVirtualGPUContexts();
    
    // Cleanup memory virtualization
    cleanupMemoryVirtualization();
    
    // Cleanup compute virtualization
    cleanupComputeVirtualization();
    
    // Destroy CUDA streams
    for (auto stream : streams_) {
        cudaStreamDestroy(stream);
    }
    streams_.clear();
    
    // Destroy handles
    cudnnDestroy(cudnnHandle_);
    cublasDestroy(cublasHandle_);
    
    // Shutdown NVML
    nvmlShutdown();
    
    spdlog::info("CUDA Virtualization Driver shutdown completed");
}

bool CUDAVirtualizationDriver::createVirtualGPU(const VirtualGPUConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if virtual GPU ID already exists
    if (virtualGPUs_.find(config.virtualGPUId) != virtualGPUs_.end()) {
        spdlog::error("Virtual GPU with ID {} already exists", config.virtualGPUId);
        return false;
    }
    
    // Create virtual GPU context
    VirtualGPUContext context;
    context.config = config;
    context.status = VirtualGPUStatus::CREATED;
    context.memoryAllocated = 0;
    context.computeUtilization = 0.0f;
    context.memoryUtilization = 0.0f;
    context.activeStreams = 0;
    
    // Allocate memory for virtual GPU
    if (config.memoryLimit > 0) {
        cudaError_t status = cudaMalloc(&context.memoryPool, config.memoryLimit);
        if (status != cudaSuccess) {
            spdlog::error("Failed to allocate memory for virtual GPU {}: {}", 
                         config.virtualGPUId, cudaGetErrorString(status));
            return false;
        }
        context.memoryLimit = config.memoryLimit;
    }
    
    // Create CUDA streams for virtual GPU
    context.streams.resize(config.numStreams);
    for (int i = 0; i < config.numStreams; ++i) {
        cudaError_t status = cudaStreamCreate(&context.streams[i]);
        if (status != cudaSuccess) {
            spdlog::error("Failed to create stream for virtual GPU {}: {}", 
                         config.virtualGPUId, cudaGetErrorString(status));
            return false;
        }
    }
    
    // Create cuBLAS handle for virtual GPU
    cublasStatus_t cublasStatus = cublasCreate(&context.cublasHandle);
    if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuBLAS handle for virtual GPU {}: {}", 
                     config.virtualGPUId, cublasStatus);
        return false;
    }
    
    // Create cuDNN handle for virtual GPU
    cudnnStatus_t cudnnStatus = cudnnCreate(&context.cudnnHandle);
    if (cudnnStatus != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuDNN handle for virtual GPU {}: {}", 
                     config.virtualGPUId, cudnnGetErrorString(cudnnStatus));
        return false;
    }
    
    // Set tensor core mode if enabled
    if (config.enableTensorCores) {
        cublasStatus = cublasSetMathMode(context.cublasHandle, CUBLAS_TENSOR_OP_MATH);
        if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
            spdlog::warn("Failed to enable tensor cores for virtual GPU {}: {}", 
                        config.virtualGPUId, cublasStatus);
        }
    }
    
    virtualGPUs_[config.virtualGPUId] = context;
    
    spdlog::info("Virtual GPU {} created successfully", config.virtualGPUId);
    return true;
}

bool CUDAVirtualizationDriver::destroyVirtualGPU(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        spdlog::error("Virtual GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualGPUContext& context = it->second;
    
    // Destroy cuDNN handle
    cudnnDestroy(context.cudnnHandle);
    
    // Destroy cuBLAS handle
    cublasDestroy(context.cublasHandle);
    
    // Destroy CUDA streams
    for (auto stream : context.streams) {
        cudaStreamDestroy(stream);
    }
    context.streams.clear();
    
    // Free memory pool
    if (context.memoryPool) {
        cudaFree(context.memoryPool);
        context.memoryPool = nullptr;
    }
    
    virtualGPUs_.erase(it);
    
    spdlog::info("Virtual GPU {} destroyed successfully", virtualGPUId);
    return true;
}

bool CUDAVirtualizationDriver::allocateMemory(int virtualGPUId, size_t size, void** ptr) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        spdlog::error("Virtual GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualGPUContext& context = it->second;
    
    // Check memory limit
    if (context.memoryAllocated + size > context.memoryLimit) {
        spdlog::error("Memory allocation failed: insufficient memory in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Allocate memory
    cudaError_t status = cudaMalloc(ptr, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to allocate memory in virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    // Update memory tracking
    context.memoryAllocated += size;
    context.memoryUtilization = static_cast<float>(context.memoryAllocated) / context.memoryLimit;
    
    // Track allocation
    MemoryAllocation alloc;
    alloc.ptr = *ptr;
    alloc.size = size;
    alloc.timestamp = std::chrono::steady_clock::now();
    context.memoryAllocations.push_back(alloc);
    
    return true;
}

bool CUDAVirtualizationDriver::freeMemory(int virtualGPUId, void* ptr) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        spdlog::error("Virtual GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualGPUContext& context = it->second;
    
    // Find and remove allocation
    auto allocIt = std::find_if(context.memoryAllocations.begin(), 
                               context.memoryAllocations.end(),
                               [ptr](const MemoryAllocation& alloc) {
                                   return alloc.ptr == ptr;
                               });
    
    if (allocIt == context.memoryAllocations.end()) {
        spdlog::error("Memory allocation not found in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Free memory
    cudaError_t status = cudaFree(ptr);
    if (status != cudaSuccess) {
        spdlog::error("Failed to free memory in virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    // Update memory tracking
    context.memoryAllocated -= allocIt->size;
    context.memoryUtilization = static_cast<float>(context.memoryAllocated) / context.memoryLimit;
    context.memoryAllocations.erase(allocIt);
    
    return true;
}

bool CUDAVirtualizationDriver::matrixMultiply(int virtualGPUId,
                                             const void* A, const void* B, void* C,
                                             int m, int n, int k,
                                             cudaDataType_t dataType,
                                             int streamId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        spdlog::error("Virtual GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualGPUContext& context = it->second;
    
    if (streamId >= context.streams.size()) {
        spdlog::error("Invalid stream ID {} for virtual GPU {}", streamId, virtualGPUId);
        return false;
    }
    
    // Set stream for cuBLAS
    cublasSetStream(context.cublasHandle, context.streams[streamId]);
    
    const float alpha = 1.0f;
    const float beta = 0.0f;
    
    cublasOperation_t transA = CUBLAS_OP_N;
    cublasOperation_t transB = CUBLAS_OP_N;
    
    cublasStatus_t status;
    if (dataType == CUDA_R_16F && context.config.enableMixedPrecision) {
        status = cublasHgemm(
            context.cublasHandle, transA, transB,
            m, n, k,
            reinterpret_cast<const __half*>(&alpha),
            reinterpret_cast<const __half*>(A), m,
            reinterpret_cast<const __half*>(B), k,
            reinterpret_cast<const __half*>(&beta),
            reinterpret_cast<__half*>(C), m
        );
    } else {
        status = cublasSgemm(
            context.cublasHandle, transA, transB,
            m, n, k,
            &alpha,
            reinterpret_cast<const float*>(A), m,
            reinterpret_cast<const float*>(B), k,
            &beta,
            reinterpret_cast<float*>(C), m
        );
    }
    
    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Matrix multiplication failed in virtual GPU {}: {}", 
                     virtualGPUId, cublasGetErrorString(status));
        return false;
    }
    
    // Update compute utilization
    context.computeUtilization = std::min(1.0f, context.computeUtilization + 0.1f);
    
    return true;
}

bool CUDAVirtualizationDriver::convolutionForward(int virtualGPUId,
                                                 const void* input, const void* filter, void* output,
                                                 int batchSize, int inChannels, int outChannels,
                                                 int height, int width, int kernelSize,
                                                 int stride, int padding,
                                                 cudaDataType_t dataType,
                                                 int streamId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        spdlog::error("Virtual GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualGPUContext& context = it->second;
    
    if (streamId >= context.streams.size()) {
        spdlog::error("Invalid stream ID {} for virtual GPU {}", streamId, virtualGPUId);
        return false;
    }
    
    // Set stream for cuDNN
    cudnnSetStream(context.cudnnHandle, context.streams[streamId]);
    
    cudnnTensorDescriptor_t inputDesc, outputDesc;
    cudnnFilterDescriptor_t filterDesc;
    cudnnConvolutionDescriptor_t convDesc;
    cudnnConvolutionFwdAlgo_t algo;
    size_t workspaceSize = 0;
    void* workspace = nullptr;
    
    // Create descriptors
    cudnnCreateTensorDescriptor(&inputDesc);
    cudnnCreateTensorDescriptor(&outputDesc);
    cudnnCreateFilterDescriptor(&filterDesc);
    cudnnCreateConvolutionDescriptor(&convDesc);
    
    // Set tensor descriptors
    cudnnSetTensor4dDescriptor(
        inputDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        batchSize,
        inChannels,
        height,
        width
    );
    
    cudnnSetFilter4dDescriptor(
        filterDesc,
        getCudnnDataType(dataType),
        CUDNN_TENSOR_NCHW,
        outChannels,
        inChannels,
        kernelSize,
        kernelSize
    );
    
    cudnnSetConvolution2dDescriptor(
        convDesc,
        padding, padding,
        stride, stride,
        1, 1,
        CUDNN_CROSS_CORRELATION,
        getCudnnDataType(dataType)
    );
    
    // Get output dimensions
    int outHeight, outWidth;
    cudnnGetConvolution2dForwardOutputDim(
        convDesc,
        inputDesc,
        filterDesc,
        &batchSize,
        &outChannels,
        &outHeight,
        &outWidth
    );
    
    cudnnSetTensor4dDescriptor(
        outputDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        batchSize,
        outChannels,
        outHeight,
        outWidth
    );
    
    // Find best algorithm
    cudnnConvolutionFwdAlgoPerf_t perfResults;
    int returnedAlgoCount;
    cudnnFindConvolutionForwardAlgorithm(
        context.cudnnHandle,
        inputDesc,
        filterDesc,
        convDesc,
        outputDesc,
        1,
        &returnedAlgoCount,
        &perfResults
    );
    algo = perfResults.algo;
    
    // Get workspace size
    cudnnGetConvolutionForwardWorkspaceSize(
        context.cudnnHandle,
        inputDesc,
        filterDesc,
        convDesc,
        outputDesc,
        algo,
        &workspaceSize
    );
    
    if (workspaceSize > 0) {
        cudaMalloc(&workspace, workspaceSize);
    }
    
    // Perform convolution
    const float alpha = 1.0f;
    const float beta = 0.0f;
    
    cudnnStatus_t status = cudnnConvolutionForward(
        context.cudnnHandle,
        &alpha,
        inputDesc, input,
        filterDesc, filter,
        convDesc,
        algo,
        workspace,
        workspaceSize,
        &beta,
        outputDesc, output
    );
    
    // Cleanup
    if (workspace) {
        cudaFree(workspace);
    }
    cudnnDestroyTensorDescriptor(inputDesc);
    cudnnDestroyTensorDescriptor(outputDesc);
    cudnnDestroyFilterDescriptor(filterDesc);
    cudnnDestroyConvolutionDescriptor(convDesc);
    
    if (status != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Convolution forward failed in virtual GPU {}: {}", 
                     virtualGPUId, cudnnGetErrorString(status));
        return false;
    }
    
    // Update compute utilization
    context.computeUtilization = std::min(1.0f, context.computeUtilization + 0.15f);
    
    return true;
}

VirtualGPUStatus CUDAVirtualizationDriver::getVirtualGPUStatus(int virtualGPUId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        return VirtualGPUStatus::NOT_FOUND;
    }
    
    return it->second.status;
}

VirtualGPUInfo CUDAVirtualizationDriver::getVirtualGPUInfo(int virtualGPUId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    VirtualGPUInfo info;
    info.virtualGPUId = virtualGPUId;
    info.status = VirtualGPUStatus::NOT_FOUND;
    
    auto it = virtualGPUs_.find(virtualGPUId);
    if (it == virtualGPUs_.end()) {
        return info;
    }
    
    const VirtualGPUContext& context = it->second;
    info.status = context.status;
    info.memoryAllocated = context.memoryAllocated;
    info.memoryLimit = context.memoryLimit;
    info.memoryUtilization = context.memoryUtilization;
    info.computeUtilization = context.computeUtilization;
    info.activeStreams = context.activeStreams;
    info.numStreams = context.streams.size();
    
    return info;
}

std::vector<VirtualGPUInfo> CUDAVirtualizationDriver::getAllVirtualGPUInfo() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<VirtualGPUInfo> infos;
    infos.reserve(virtualGPUs_.size());
    
    for (const auto& pair : virtualGPUs_) {
        infos.push_back(getVirtualGPUInfo(pair.first));
    }
    
    return infos;
}

bool CUDAVirtualizationDriver::initializeVirtualGPUContexts() {
    // Initialize virtual GPU context management
    virtualGPUContexts_.reserve(config_.maxVirtualGPUs);
    
    spdlog::info("Virtual GPU contexts initialized");
    return true;
}

bool CUDAVirtualizationDriver::initializeMemoryVirtualization() {
    // Initialize memory virtualization system
    memoryVirtualizationEnabled_ = true;
    
    // Get total GPU memory
    size_t totalMemory;
    cudaError_t status = cudaMemGetInfo(&freeMemory_, &totalMemory);
    if (status != cudaSuccess) {
        spdlog::error("Failed to get GPU memory info: {}", cudaGetErrorString(status));
        return false;
    }
    
    totalMemory_ = totalMemory;
    usedMemory_ = totalMemory - freeMemory_;
    
    spdlog::info("Memory virtualization initialized - Total: {} MB, Used: {} MB", 
                 totalMemory_ / (1024 * 1024), usedMemory_ / (1024 * 1024));
    return true;
}

bool CUDAVirtualizationDriver::initializeComputeVirtualization() {
    // Initialize compute virtualization system
    computeVirtualizationEnabled_ = true;
    
    // Get GPU compute capability
    spdlog::info("Compute virtualization initialized - Compute Capability: {}.{}", 
                 deviceProps_.major, deviceProps_.minor);
    return true;
}

void CUDAVirtualizationDriver::cleanupVirtualGPUContexts() {
    // Cleanup all virtual GPU contexts
    for (auto& pair : virtualGPUs_) {
        VirtualGPUContext& context = pair.second;
        
        // Destroy cuDNN handle
        cudnnDestroy(context.cudnnHandle);
        
        // Destroy cuBLAS handle
        cublasDestroy(context.cublasHandle);
        
        // Destroy CUDA streams
        for (auto stream : context.streams) {
            cudaStreamDestroy(stream);
        }
        
        // Free memory pool
        if (context.memoryPool) {
            cudaFree(context.memoryPool);
        }
    }
    
    virtualGPUs_.clear();
    virtualGPUContexts_.clear();
}

void CUDAVirtualizationDriver::cleanupMemoryVirtualization() {
    memoryVirtualizationEnabled_ = false;
    totalMemory_ = 0;
    usedMemory_ = 0;
    freeMemory_ = 0;
}

void CUDAVirtualizationDriver::cleanupComputeVirtualization() {
    computeVirtualizationEnabled_ = false;
}

void CUDAVirtualizationDriver::monitoringLoop() {
    while (running_) {
        // Update GPU utilization
        updateGPUUtilization();
        
        // Update memory usage
        updateMemoryUsage();
        
        // Update virtual GPU status
        updateVirtualGPUStatus();
        
        // Sleep for monitoring interval
        std::this_thread::sleep_for(std::chrono::milliseconds(config_.monitoringInterval));
    }
}

void CUDAVirtualizationDriver::updateGPUUtilization() {
    unsigned int utilization;
    nvmlReturn_t status = nvmlDeviceGetUtilizationRates(nvmlDevice_, &utilization);
    if (status == NVML_SUCCESS) {
        gpuUtilization_ = static_cast<float>(utilization) / 100.0f;
    }
}

void CUDAVirtualizationDriver::updateMemoryUsage() {
    size_t free, total;
    cudaError_t status = cudaMemGetInfo(&free, &total);
    if (status == cudaSuccess) {
        freeMemory_ = free;
        totalMemory_ = total;
        usedMemory_ = total - free;
    }
}

void CUDAVirtualizationDriver::updateVirtualGPUStatus() {
    for (auto& pair : virtualGPUs_) {
        VirtualGPUContext& context = pair.second;
        
        // Update compute utilization (decay over time)
        context.computeUtilization = std::max(0.0f, context.computeUtilization - 0.01f);
        
        // Update active streams count
        context.activeStreams = 0;
        for (auto stream : context.streams) {
            cudaError_t status = cudaStreamQuery(stream);
            if (status == cudaErrorNotReady) {
                context.activeStreams++;
            }
        }
    }
}

cudnnDataType_t CUDAVirtualizationDriver::getCudnnDataType(cudaDataType_t dataType) const {
    switch (dataType) {
        case CUDA_R_16F:
            return CUDNN_DATA_HALF;
        case CUDA_R_32F:
            return CUDNN_DATA_FLOAT;
        case CUDA_R_64F:
            return CUDNN_DATA_DOUBLE;
        default:
            return CUDNN_DATA_FLOAT;
    }
}

} // namespace msmartcompute 