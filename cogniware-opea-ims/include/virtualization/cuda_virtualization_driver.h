#ifndef MSMARTCOMPUTE_CUDA_VIRTUALIZATION_DRIVER_H
#define MSMARTCOMPUTE_CUDA_VIRTUALIZATION_DRIVER_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <nvml.h>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <thread>
#include <chrono>
#include <string>

namespace cogniware {

// Forward declarations
struct VirtualizationConfig;
struct VirtualGPUConfig;
struct VirtualGPUContext;
struct VirtualGPUInfo;
struct MemoryAllocation;

/**
 * @brief Virtual GPU status enumeration
 */
enum class VirtualGPUStatus {
    NOT_FOUND,
    CREATED,
    RUNNING,
    PAUSED,
    ERROR,
    DESTROYED
};

/**
 * @brief Virtualization configuration
 */
struct VirtualizationConfig {
    int deviceId = 0;                    // Physical GPU device ID
    int maxVirtualGPUs = 8;              // Maximum number of virtual GPUs
    int numVirtualStreams = 16;          // Number of virtual CUDA streams
    int monitoringInterval = 100;        // Monitoring interval in milliseconds
    bool enableMemoryVirtualization = true;
    bool enableComputeVirtualization = true;
    bool enableTensorCores = true;
    bool enableMixedPrecision = true;
};

/**
 * @brief Virtual GPU configuration
 */
struct VirtualGPUConfig {
    int virtualGPUId;                    // Unique virtual GPU ID
    size_t memoryLimit;                  // Memory limit in bytes
    int numStreams;                      // Number of CUDA streams
    bool enableTensorCores;              // Enable tensor cores
    bool enableMixedPrecision;           // Enable mixed precision
    float computeShare;                  // Compute share (0.0-1.0)
    std::string name;                    // Virtual GPU name
};

/**
 * @brief Memory allocation tracking
 */
struct MemoryAllocation {
    void* ptr;                           // Memory pointer
    size_t size;                         // Allocation size
    std::chrono::steady_clock::time_point timestamp;  // Allocation timestamp
    std::string tag;                     // Allocation tag
};

/**
 * @brief Virtual GPU context
 */
struct VirtualGPUContext {
    VirtualGPUConfig config;             // Virtual GPU configuration
    VirtualGPUStatus status;             // Current status
    size_t memoryAllocated;              // Currently allocated memory
    size_t memoryLimit;                  // Memory limit
    float memoryUtilization;             // Memory utilization (0.0-1.0)
    float computeUtilization;            // Compute utilization (0.0-1.0)
    int activeStreams;                   // Number of active streams
    
    // CUDA resources
    void* memoryPool;                    // Memory pool
    std::vector<cudaStream_t> streams;   // CUDA streams
    cublasHandle_t cublasHandle;         // cuBLAS handle
    cudnnHandle_t cudnnHandle;           // cuDNN handle
    
    // Memory tracking
    std::vector<MemoryAllocation> memoryAllocations;
};

/**
 * @brief Virtual GPU information
 */
struct VirtualGPUInfo {
    int virtualGPUId;                    // Virtual GPU ID
    VirtualGPUStatus status;             // Current status
    size_t memoryAllocated;              // Allocated memory
    size_t memoryLimit;                  // Memory limit
    float memoryUtilization;             // Memory utilization
    float computeUtilization;            // Compute utilization
    int activeStreams;                   // Active streams
    int numStreams;                      // Total streams
    std::string name;                    // Virtual GPU name
};

/**
 * @brief CUDA Virtualization Driver
 * 
 * This class provides GPU virtualization capabilities for CUDA applications.
 * It allows multiple virtual GPUs to run on a single physical GPU with
 * resource isolation and management.
 */
class CUDAVirtualizationDriver {
public:
    // Singleton pattern
    static CUDAVirtualizationDriver& getInstance();
    
    // Disable copy constructor and assignment operator
    CUDAVirtualizationDriver(const CUDAVirtualizationDriver&) = delete;
    CUDAVirtualizationDriver& operator=(const CUDAVirtualizationDriver&) = delete;
    
    // Initialization and shutdown
    bool initialize(const VirtualizationConfig& config);
    void shutdown();
    
    // Virtual GPU management
    bool createVirtualGPU(const VirtualGPUConfig& config);
    bool destroyVirtualGPU(int virtualGPUId);
    VirtualGPUStatus getVirtualGPUStatus(int virtualGPUId) const;
    VirtualGPUInfo getVirtualGPUInfo(int virtualGPUId) const;
    std::vector<VirtualGPUInfo> getAllVirtualGPUInfo() const;
    
    // Memory management
    bool allocateMemory(int virtualGPUId, size_t size, void** ptr);
    bool freeMemory(int virtualGPUId, void* ptr);
    bool copyMemory(int virtualGPUId, void* dst, const void* src, size_t size, cudaMemcpyKind kind);
    bool memset(int virtualGPUId, void* ptr, int value, size_t size);
    
    // Compute operations
    bool matrixMultiply(int virtualGPUId,
                       const void* A, const void* B, void* C,
                       int m, int n, int k,
                       cudaDataType_t dataType,
                       int streamId = 0);
    
    bool convolutionForward(int virtualGPUId,
                           const void* input, const void* filter, void* output,
                           int batchSize, int inChannels, int outChannels,
                           int height, int width, int kernelSize,
                           int stride, int padding,
                           cudaDataType_t dataType,
                           int streamId = 0);
    
    bool activationForward(int virtualGPUId,
                          const void* input, void* output,
                          int batchSize, int channels, int height, int width,
                          const std::string& activationType,
                          cudaDataType_t dataType,
                          int streamId = 0);
    
    bool batchNormalization(int virtualGPUId,
                           void* data, const void* gamma, const void* beta,
                           void* runningMean, void* runningVar,
                           int batchSize, int channels, int spatialSize,
                           float momentum, float epsilon,
                           cudaDataType_t dataType,
                           int streamId = 0);
    
    bool selfAttention(int virtualGPUId,
                      const void* query, const void* key, const void* value,
                      void* output,
                      int batchSize, int seqLen, int headSize, int numHeads,
                      cudaDataType_t dataType,
                      int streamId = 0);
    
    // Stream management
    bool synchronizeStream(int virtualGPUId, int streamId);
    bool queryStream(int virtualGPUId, int streamId);
    bool waitForStream(int virtualGPUId, int streamId);
    
    // Resource monitoring
    float getGPUUtilization() const { return gpuUtilization_; }
    size_t getTotalMemory() const { return totalMemory_; }
    size_t getUsedMemory() const { return usedMemory_; }
    size_t getFreeMemory() const { return freeMemory_; }
    
    // Configuration
    VirtualizationConfig getConfig() const { return config_; }
    bool isMemoryVirtualizationEnabled() const { return memoryVirtualizationEnabled_; }
    bool isComputeVirtualizationEnabled() const { return computeVirtualizationEnabled_; }

private:
    // Private constructor for singleton
    CUDAVirtualizationDriver() = default;
    ~CUDAVirtualizationDriver() = default;
    
    // Configuration
    VirtualizationConfig config_;
    cudaDeviceProp deviceProps_;
    
    // NVML resources
    nvmlDevice_t nvmlDevice_;
    
    // CUDA resources
    cublasHandle_t cublasHandle_;
    cudnnHandle_t cudnnHandle_;
    std::vector<cudaStream_t> streams_;
    
    // Virtual GPU management
    std::unordered_map<int, VirtualGPUContext> virtualGPUs_;
    std::vector<VirtualGPUContext> virtualGPUContexts_;
    
    // Memory virtualization
    bool memoryVirtualizationEnabled_ = false;
    size_t totalMemory_ = 0;
    size_t usedMemory_ = 0;
    size_t freeMemory_ = 0;
    
    // Compute virtualization
    bool computeVirtualizationEnabled_ = false;
    float gpuUtilization_ = 0.0f;
    
    // Threading
    std::thread monitoringThread_;
    mutable std::mutex mutex_;
    bool running_ = false;
    
    // Initialization helpers
    bool initializeVirtualGPUContexts();
    bool initializeMemoryVirtualization();
    bool initializeComputeVirtualization();
    
    // Cleanup helpers
    void cleanupVirtualGPUContexts();
    void cleanupMemoryVirtualization();
    void cleanupComputeVirtualization();
    
    // Monitoring
    void monitoringLoop();
    void updateGPUUtilization();
    void updateMemoryUsage();
    void updateVirtualGPUStatus();
    
    // Utility functions
    cudnnDataType_t getCudnnDataType(cudaDataType_t dataType) const;
    
    // Memory management helpers
    bool checkMemoryLimit(int virtualGPUId, size_t size) const;
    void updateMemoryTracking(int virtualGPUId, void* ptr, size_t size, bool isAllocation);
    
    // Stream validation
    bool validateStream(int virtualGPUId, int streamId) const;
    
    // Error handling
    void logError(const std::string& operation, const std::string& error) const;
    void logWarning(const std::string& operation, const std::string& warning) const;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_VIRTUALIZATION_DRIVER_H 