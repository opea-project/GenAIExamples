#ifndef MSMARTCOMPUTE_ENHANCED_DRIVER_H
#define MSMARTCOMPUTE_ENHANCED_DRIVER_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <nvml.h>
#include <thread>
#include <mutex>
#include <vector>
#include <string>
#include <memory>

namespace cogniware {

// Enhanced Driver Configuration
struct EnhancedDriverConfig {
    int deviceId = 0;
    int numStreams = 4;
    int monitoringInterval = 100; // milliseconds
    bool enableTensorCores = true;
    bool enableMixedPrecision = true;
    int optimizationLevel = 2;
    size_t maxMemoryPoolSize = 1024 * 1024 * 1024; // 1GB
};

// Enhanced Driver Statistics
struct EnhancedDriverStats {
    float gpuUtilization = 0.0f;
    float memoryUtilization = 0.0f;
    float temperature = 0.0f;
    float powerUsage = 0.0f;
    
    struct KernelStats {
        float executionTime = 0.0f;
        float memoryBandwidth = 0.0f;
        float computeThroughput = 0.0f;
        int occupancy = 0;
    } kernelStats;
};

// Enhanced Driver Class
class EnhancedDriver {
public:
    static EnhancedDriver& getInstance();
    
    // Disable copy constructor and assignment operator
    EnhancedDriver(const EnhancedDriver&) = delete;
    EnhancedDriver& operator=(const EnhancedDriver&) = delete;
    
    // Initialization and shutdown
    bool initialize(const EnhancedDriverConfig& config);
    void shutdown();
    
    // Core execution methods
    bool executeMatrixMultiply(
        const void* A, const void* B, void* C,
        int M, int N, int K,
        cudaDataType_t dataType,
        float alpha = 1.0f, float beta = 0.0f,
        int streamId = 0
    );
    
    bool executeConvolution(
        const void* input, const void* filter, void* output,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding,
        cudaDataType_t dataType,
        int streamId = 0
    );
    
    bool executeAttention(
        const void* query, const void* key, const void* value,
        void* output, void* attentionWeights,
        int batchSize, int seqLength, int numHeads, int headDim,
        float scale = 1.0f,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    bool executeActivation(
        void* data, int size,
        const std::string& activationType,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    bool executeLayerNorm(
        void* output, const void* input, const void* gamma, const void* beta,
        int batchSize, int seqLength, int hiddenSize,
        float epsilon = 1e-5f,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    bool executeDropout(
        void* output, const void* input, void* mask,
        int size, float dropoutRate, unsigned int seed,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    bool executeOptimizer(
        void* params, const void* gradients, void* m, void* v,
        int size, float learningRate, float beta1, float beta2, float epsilon, int step,
        const std::string& optimizerType,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    bool executeLoss(
        void* loss, const void* predictions, const void* targets,
        int batchSize, int numClasses,
        const std::string& lossType,
        cudaDataType_t dataType = CUDA_R_32F,
        int streamId = 0
    );
    
    // Synchronization
    bool synchronize(int streamId);
    bool synchronizeAll();
    
    // Statistics and monitoring
    EnhancedDriverStats getStats() const;
    
    // Configuration
    EnhancedDriverConfig getConfig() const { return config_; }
    bool isInitialized() const { return initialized_; }

private:
    EnhancedDriver() = default;
    ~EnhancedDriver() = default;
    
    // Internal state
    bool initialized_ = false;
    bool running_ = false;
    EnhancedDriverConfig config_;
    
    // CUDA handles
    cublasHandle_t cublasHandle_ = nullptr;
    cudnnHandle_t cudnnHandle_ = nullptr;
    std::vector<cudaStream_t> streams_;
    
    // NVML monitoring
    nvmlDevice_t nvmlDevice_ = nullptr;
    float gpuUtilization_ = 0.0f;
    float memoryUtilization_ = 0.0f;
    float temperature_ = 0.0f;
    float powerUsage_ = 0.0f;
    
    // Threading
    std::thread monitoringThread_;
    mutable std::mutex mutex_;
    
    // Internal methods
    void monitoringLoop();
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_ENHANCED_DRIVER_H 