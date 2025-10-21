#ifndef MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_H
#define MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <queue>
#include <functional>

namespace cogniware {

// Forward declarations
class VirtualMemoryManager;
class TensorCoreManager;
class ModelManager;

/**
 * @brief Virtual compute node configuration
 */
struct VirtualNodeConfig {
    size_t memoryLimit;           // Memory limit in bytes
    size_t computeUnits;          // Number of compute units
    size_t tensorCores;           // Number of tensor cores
    bool enableMixedPrecision;    // Enable mixed precision computation
    size_t maxConcurrentModels;   // Maximum number of concurrent models
    size_t batchSize;             // Default batch size
    float memoryUtilization;      // Target memory utilization (0.0-1.0)
};

/**
 * @brief Virtual compute node status
 */
struct VirtualNodeStatus {
    size_t usedMemory;
    size_t availableMemory;
    size_t activeModels;
    float gpuUtilization;
    float memoryUtilization;
    std::vector<std::string> runningModels;
};

/**
 * @brief Virtual compute node class
 */
class VirtualComputeNode {
public:
    VirtualComputeNode(const VirtualNodeConfig& config);
    ~VirtualComputeNode();

    // Node management
    bool initialize();
    void shutdown();
    VirtualNodeStatus getStatus() const;
    bool allocateResources(const std::string& modelId, size_t requiredMemory);
    void releaseResources(const std::string& modelId);

    // Model management
    bool loadModel(const std::string& modelId, const std::string& modelPath);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;

    // Training control
    bool startTraining(const std::string& modelId);
    void stopTraining(const std::string& modelId);
    void pauseTraining(const std::string& modelId);
    void resumeTraining(const std::string& modelId);

    // Memory management
    void* allocateMemory(size_t size);
    void freeMemory(void* ptr);
    size_t getAvailableMemory() const;

    // Tensor core management
    bool enableTensorCores(const std::string& modelId);
    void disableTensorCores(const std::string& modelId);
    bool areTensorCoresEnabled(const std::string& modelId) const;

private:
    // Resource management
    void manageResources();
    bool checkResourceAvailability(size_t requiredMemory) const;
    void optimizeMemoryUsage();
    void balanceLoad();

    // CUDA resources
    cudaStream_t stream_;
    cublasHandle_t cublasHandle_;
    cudnnHandle_t cudnnHandle_;
    int deviceId_;

    // Configuration and state
    VirtualNodeConfig config_;
    VirtualNodeStatus status_;
    std::unordered_map<std::string, size_t> modelMemoryUsage_;
    std::unordered_map<std::string, bool> modelTensorCoreStatus_;
    std::queue<std::string> modelQueue_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool isRunning_;

    // Component managers
    std::unique_ptr<VirtualMemoryManager> memoryManager_;
    std::unique_ptr<TensorCoreManager> tensorCoreManager_;
    std::unique_ptr<ModelManager> modelManager_;

    // Worker thread
    std::thread resourceManagerThread_;
    void resourceManagerLoop();
};

/**
 * @brief Virtual memory manager class
 */
class VirtualMemoryManager {
public:
    VirtualMemoryManager(size_t totalMemory, float utilizationTarget);
    ~VirtualMemoryManager();

    void* allocate(size_t size);
    void free(void* ptr);
    size_t getAvailableMemory() const;
    void optimizeMemoryUsage();
    void setUtilizationTarget(float target);

private:
    struct MemoryBlock {
        void* ptr;
        size_t size;
        bool inUse;
    };

    std::vector<MemoryBlock> memoryBlocks_;
    size_t totalMemory_;
    size_t usedMemory_;
    float utilizationTarget_;
    std::mutex mutex_;

    void defragmentMemory();
    bool canAllocate(size_t size) const;
    void* findBestFit(size_t size);
};

/**
 * @brief Tensor core manager class
 */
class TensorCoreManager {
public:
    TensorCoreManager(size_t numTensorCores);
    ~TensorCoreManager();

    bool enableForModel(const std::string& modelId);
    void disableForModel(const std::string& modelId);
    bool isEnabledForModel(const std::string& modelId) const;
    void optimizeTensorCoreUsage();

private:
    size_t numTensorCores_;
    std::unordered_map<std::string, bool> modelTensorCoreStatus_;
    std::mutex mutex_;
};

/**
 * @brief Model manager class
 */
class ModelManager {
public:
    ModelManager(size_t maxConcurrentModels);
    ~ModelManager();

    bool loadModel(const std::string& modelId, const std::string& modelPath);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;
    void queueModel(const std::string& modelId);
    std::string dequeueModel();

private:
    size_t maxConcurrentModels_;
    std::unordered_map<std::string, bool> loadedModels_;
    std::queue<std::string> modelQueue_;
    std::mutex mutex_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_H 