#include "enhanced_driver.h"
#include "enhanced_cuda_kernels.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <nvml.h>

namespace cogniware {

EnhancedDriver& EnhancedDriver::getInstance() {
    static EnhancedDriver instance;
    return instance;
}

bool EnhancedDriver::initialize(const EnhancedDriverConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_ = config;
    
    // Initialize CUDA
    cudaError_t cudaStatus = cudaSetDevice(config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    // Initialize enhanced kernel manager
    if (!EnhancedCUDAKernelManager::getInstance().initialize()) {
        spdlog::error("Failed to initialize enhanced kernel manager");
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
    
    // Create CUDA streams
    streams_.resize(config_.numStreams);
    for (int i = 0; i < config_.numStreams; ++i) {
        cudaStatus = cudaStreamCreate(&streams_[i]);
        if (cudaStatus != cudaSuccess) {
            spdlog::error("Failed to create CUDA stream {}: {}", i, cudaGetErrorString(cudaStatus));
            return false;
        }
    }
    
    // Initialize NVML for monitoring
    nvmlReturn_t nvmlStatus = nvmlInit();
    if (nvmlStatus != NVML_SUCCESS) {
        spdlog::warn("Failed to initialize NVML: {}", nvmlErrorString(nvmlStatus));
    } else {
        nvmlStatus = nvmlDeviceGetHandleByIndex(config_.deviceId, &nvmlDevice_);
        if (nvmlStatus != NVML_SUCCESS) {
            spdlog::warn("Failed to get NVML device handle: {}", nvmlErrorString(nvmlStatus));
        }
    }
    
    // Start monitoring thread
    running_ = true;
    monitoringThread_ = std::thread(&EnhancedDriver::monitoringLoop, this);
    
    spdlog::info("Enhanced Driver initialized successfully");
    return true;
}

void EnhancedDriver::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!running_) return;
    
    running_ = false;
    
    // Stop monitoring thread
    if (monitoringThread_.joinable()) {
        monitoringThread_.join();
    }
    
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
    
    spdlog::info("Enhanced Driver shutdown completed");
}

bool EnhancedDriver::executeMatrixMultiply(
    const void* A, const void* B, void* C,
    int M, int N, int K,
    cudaDataType_t dataType,
    float alpha, float beta,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().matrixMultiply(
        A, B, C, M, N, K, dataType, alpha, beta, streams_[streamId]
    );
}

bool EnhancedDriver::executeConvolution(
    const void* input, const void* filter, void* output,
    int batchSize, int inChannels, int outChannels,
    int height, int width, int kernelSize,
    int stride, int padding,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().convolutionForward(
        input, filter, output, batchSize, inChannels, outChannels,
        height, width, kernelSize, stride, padding, dataType, streams_[streamId]
    );
}

bool EnhancedDriver::executeAttention(
    const void* query, const void* key, const void* value,
    void* output, void* attentionWeights,
    int batchSize, int seqLength, int numHeads, int headDim,
    float scale,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().multiHeadAttention(
        query, key, value, output, attentionWeights,
        batchSize, seqLength, numHeads, headDim, scale, dataType, streams_[streamId]
    );
}

bool EnhancedDriver::executeActivation(
    void* data, int size,
    const std::string& activationType,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().applyActivation(
        data, size, activationType, dataType, streams_[streamId]
    );
}

bool EnhancedDriver::executeLayerNorm(
    void* output, const void* input, const void* gamma, const void* beta,
    int batchSize, int seqLength, int hiddenSize,
    float epsilon,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().layerNormalization(
        output, input, gamma, beta, batchSize, seqLength, hiddenSize,
        epsilon, dataType, streams_[streamId]
    );
}

bool EnhancedDriver::executeDropout(
    void* output, const void* input, void* mask,
    int size, float dropoutRate, unsigned int seed,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    return EnhancedCUDAKernelManager::getInstance().dropout(
        output, input, mask, size, dropoutRate, seed, dataType, streams_[streamId]
    );
}

bool EnhancedDriver::executeOptimizer(
    void* params, const void* gradients, void* m, void* v,
    int size, float learningRate, float beta1, float beta2, float epsilon, int step,
    const std::string& optimizerType,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    if (optimizerType == "adam") {
        return EnhancedCUDAKernelManager::getInstance().adamOptimizer(
            params, gradients, m, v, size, learningRate, beta1, beta2, epsilon, step,
            dataType, streams_[streamId]
        );
    } else if (optimizerType == "sgd") {
        return EnhancedCUDAKernelManager::getInstance().sgdOptimizer(
            params, gradients, size, learningRate, 0.0f, dataType, streams_[streamId]
        );
    } else {
        spdlog::error("Unsupported optimizer type: {}", optimizerType);
        return false;
    }
}

bool EnhancedDriver::executeLoss(
    void* loss, const void* predictions, const void* targets,
    int batchSize, int numClasses,
    const std::string& lossType,
    cudaDataType_t dataType,
    int streamId
) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    if (lossType == "cross_entropy") {
        return EnhancedCUDAKernelManager::getInstance().crossEntropyLoss(
            loss, predictions, static_cast<const int*>(targets),
            batchSize, numClasses, dataType, streams_[streamId]
        );
    } else if (lossType == "mse") {
        return EnhancedCUDAKernelManager::getInstance().mseLoss(
            loss, predictions, targets, batchSize * numClasses, dataType, streams_[streamId]
        );
    } else {
        spdlog::error("Unsupported loss type: {}", lossType);
        return false;
    }
}

bool EnhancedDriver::synchronize(int streamId) {
    if (streamId >= streams_.size()) {
        spdlog::error("Invalid stream ID: {}", streamId);
        return false;
    }
    
    cudaError_t status = cudaStreamSynchronize(streams_[streamId]);
    if (status != cudaSuccess) {
        spdlog::error("Failed to synchronize stream {}: {}", streamId, cudaGetErrorString(status));
        return false;
    }
    
    return true;
}

bool EnhancedDriver::synchronizeAll() {
    cudaError_t status = cudaDeviceSynchronize();
    if (status != cudaSuccess) {
        spdlog::error("Failed to synchronize device: {}", cudaGetErrorString(status));
        return false;
    }
    
    return true;
}

EnhancedDriverStats EnhancedDriver::getStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    EnhancedDriverStats stats;
    stats.gpuUtilization = gpuUtilization_;
    stats.memoryUtilization = memoryUtilization_;
    stats.temperature = temperature_;
    stats.powerUsage = powerUsage_;
    stats.kernelStats = EnhancedCUDAKernelManager::getInstance().getKernelStats();
    
    return stats;
}

void EnhancedDriver::monitoringLoop() {
    while (running_) {
        // Update GPU utilization
        if (nvmlDevice_) {
            unsigned int utilization;
            nvmlReturn_t status = nvmlDeviceGetUtilizationRates(nvmlDevice_, &utilization);
            if (status == NVML_SUCCESS) {
                gpuUtilization_ = static_cast<float>(utilization) / 100.0f;
            }
            
            // Update memory utilization
            nvmlMemory_t memory;
            status = nvmlDeviceGetMemoryInfo(nvmlDevice_, &memory);
            if (status == NVML_SUCCESS) {
                memoryUtilization_ = static_cast<float>(memory.used) / memory.total;
            }
            
            // Update temperature
            unsigned int temp;
            status = nvmlDeviceGetTemperature(nvmlDevice_, NVML_TEMPERATURE_GPU, &temp);
            if (status == NVML_SUCCESS) {
                temperature_ = static_cast<float>(temp);
            }
            
            // Update power usage
            unsigned int power;
            status = nvmlDeviceGetPowerUsage(nvmlDevice_, &power);
            if (status == NVML_SUCCESS) {
                powerUsage_ = static_cast<float>(power) / 1000.0f; // Convert to Watts
            }
        }
        
        // Sleep for monitoring interval
        std::this_thread::sleep_for(std::chrono::milliseconds(config_.monitoringInterval));
    }
}

} // namespace cogniware 