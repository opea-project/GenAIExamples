#ifndef MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_MANAGER_H
#define MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_MANAGER_H

#include <cuda_runtime.h>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <string>
#include <thread>
#include <atomic>
#include <queue>
#include <functional>
#include <chrono>

namespace cogniware {

/**
 * @brief Resource utilization thresholds
 */
struct ResourceThresholds {
    float memoryUtilization;
    float gpuUtilization;
    float cpuUtilization;
    float tensorCoreUtilization;
    float storageUtilization;
};

/**
 * @brief Resource scaling factors
 */
struct ResourceScaling {
    float memoryScaleFactor;
    float gpuScaleFactor;
    float cpuScaleFactor;
    float tensorCoreScaleFactor;
    float storageScaleFactor;
};

/**
 * @brief Virtual node configuration
 */
struct VirtualNodeConfig {
    int deviceId;
    size_t memoryLimit;
    int maxConcurrentModels;
    bool useTensorCores;
    bool useMixedPrecision;
    float memoryUtilizationTarget;
    int batchSize;
    int numStreams;
    
    // Advanced configuration
    ResourceThresholds thresholds;
    ResourceScaling scaling;
    size_t minMemoryAllocation;
    size_t maxMemoryAllocation;
    int minTensorCores;
    int maxTensorCores;
    int minCPUThreads;
    int maxCPUThreads;
    size_t minStorageSpace;
    size_t maxStorageSpace;
    bool enableAutoScaling;
    int scalingCheckInterval;  // in milliseconds
};

/**
 * @brief Model configuration
 */
struct ModelConfig {
    std::string modelId;
    size_t memoryRequirement;
    int priority;
    bool useTensorCores;
    bool useMixedPrecision;
    int batchSize;
    
    // Advanced configuration
    float minAccuracy;
    float maxAccuracy;
    int minEpochs;
    int maxEpochs;
    bool enableDynamicBatchSize;
    bool enableGradientAccumulation;
    int gradientAccumulationSteps;
};

/**
 * @brief Virtual node status
 */
struct VirtualNodeStatus {
    size_t totalMemory;
    size_t usedMemory;
    size_t freeMemory;
    int activeModels;
    float gpuUtilization;
    std::vector<std::string> runningModels;
    
    // Advanced monitoring
    float cpuUtilization;
    float tensorCoreUtilization;
    float storageUtilization;
    size_t totalStorage;
    size_t usedStorage;
    size_t freeStorage;
    int totalTensorCores;
    int usedTensorCores;
    int freeTensorCores;
    int totalCPUThreads;
    int usedCPUThreads;
    int freeCPUThreads;
    std::vector<float> modelAccuracies;
    std::vector<int> modelEpochs;
    std::vector<float> modelLosses;
    std::vector<float> modelLearningRates;
    std::vector<float> modelGradients;
    std::vector<float> modelWeights;
    std::vector<float> modelBiases;
    std::vector<float> modelActivations;
    std::vector<float> modelDropouts;
    std::vector<float> modelBatchSizes;
    std::vector<float> modelMemoryUsage;
    std::vector<float> modelGPUUsage;
    std::vector<float> modelCPUUsage;
    std::vector<float> modelTensorCoreUsage;
    std::vector<float> modelStorageUsage;
};

/**
 * @brief Virtual compute node manager class
 */
class VirtualComputeNodeManager {
public:
    static VirtualComputeNodeManager& getInstance();

    // Node management
    bool initialize(const VirtualNodeConfig& config);
    void shutdown();
    bool setNodeConfig(const VirtualNodeConfig& config);
    VirtualNodeConfig getNodeConfig() const;
    VirtualNodeStatus getNodeStatus() const;

    // Model management
    bool loadModel(const ModelConfig& config);
    bool unloadModel(const std::string& modelId);
    bool startTraining(const std::string& modelId);
    bool stopTraining(const std::string& modelId);
    bool pauseTraining(const std::string& modelId);
    bool resumeTraining(const std::string& modelId);

    // Resource management
    bool allocateResources(const std::string& modelId);
    void releaseResources(const std::string& modelId);
    bool checkResourceAvailability(const ModelConfig& config) const;
    void optimizeResourceUsage();

    // Monitoring
    void setStatusCallback(std::function<void(const VirtualNodeStatus&)> callback);
    void enableMonitoring(bool enable);
    void printNodeStats() const;

private:
    VirtualComputeNodeManager() = default;
    ~VirtualComputeNodeManager() = default;
    VirtualComputeNodeManager(const VirtualComputeNodeManager&) = delete;
    VirtualComputeNodeManager& operator=(const VirtualComputeNodeManager&) = delete;

    // Resource management
    void resourceManagerLoop();
    void processModelQueue();
    void balanceLoad();
    void optimizeMemoryUsage();
    void updateNodeStatus();

    // Resource optimization
    void optimizeResourceAllocation();
    void scaleResources();
    void balanceResourceUtilization();
    void optimizeModelConfigurations();
    void adjustBatchSizes();
    void manageGradientAccumulation();
    void optimizeMemoryLayout();
    void defragmentResources();
    void cleanupUnusedResources();
    
    // Resource monitoring
    void monitorResourceUtilization();
    void trackModelMetrics();
    void analyzePerformanceMetrics();
    void predictResourceNeeds();
    void generateResourceReport();
    
    // Resource scaling
    bool canScaleResources() const;
    void scaleMemory();
    void scaleTensorCores();
    void scaleCPUThreads();
    void scaleStorage();
    
    // Resource thresholds
    bool checkResourceThresholds() const;
    bool isMemoryUtilizationHigh() const;
    bool isGPUUtilizationHigh() const;
    bool isCPUUtilizationHigh() const;
    bool isTensorCoreUtilizationHigh() const;
    bool isStorageUtilizationHigh() const;
    
    // Resource metrics
    struct ResourceMetrics {
        float memoryUtilization;
        float gpuUtilization;
        float cpuUtilization;
        float tensorCoreUtilization;
        float storageUtilization;
        std::vector<float> modelMetrics;
    };
    
    ResourceMetrics currentMetrics_;
    std::vector<ResourceMetrics> historicalMetrics_;
    
    // Resource scaling state
    struct ScalingState {
        bool isScaling;
        std::chrono::steady_clock::time_point lastScalingTime;
        int scalingAttempts;
        float scalingFactor;
    };
    
    ScalingState scalingState_;
    
    // Resource monitoring state
    struct MonitoringState {
        bool isMonitoring;
        std::chrono::steady_clock::time_point lastMonitoringTime;
        int monitoringInterval;
        std::vector<float> utilizationHistory;
    };
    
    MonitoringState monitoringState_;

    // Model management
    struct ModelInfo {
        ModelConfig config;
        bool isTraining;
        bool isPaused;
        cudaStream_t stream;
        void* modelData;
    };

    // Configuration
    VirtualNodeConfig config_;
    std::mutex mutex_;
    std::atomic<bool> running_;

    // Resource management
    std::thread resourceManagerThread_;
    std::queue<std::string> modelQueue_;
    std::unordered_map<std::string, ModelInfo> activeModels_;
    std::vector<cudaStream_t> streams_;

    // Monitoring
    bool monitoringEnabled_;
    std::function<void(const VirtualNodeStatus&)> statusCallback_;
    VirtualNodeStatus currentStatus_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_VIRTUAL_COMPUTE_NODE_MANAGER_H 