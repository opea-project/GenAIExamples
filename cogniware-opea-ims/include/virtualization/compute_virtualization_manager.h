#ifndef MSMARTCOMPUTE_COMPUTE_VIRTUALIZATION_MANAGER_H
#define MSMARTCOMPUTE_COMPUTE_VIRTUALIZATION_MANAGER_H

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
#include <queue>
#include <string>

namespace cogniware {

// Forward declarations
class ComputeUnitManager;
class ComputeScheduler;
class LoadBalancer;

/**
 * @brief Compute virtualization configuration
 */
struct ComputeVirtualizationConfig {
    int deviceId = 0;                    // Physical GPU device ID
    int maxVirtualComputeUnits = 16;     // Maximum number of virtual compute units
    std::string schedulingPolicy = "round_robin"; // Scheduling policy
    std::string loadBalancingStrategy = "least_loaded"; // Load balancing strategy
    int timeSlice = 100;                 // Time slice in milliseconds
    int monitoringInterval = 100;        // Monitoring interval in milliseconds
    bool enableDynamicScaling = true;    // Enable dynamic compute unit scaling
    bool enablePreemption = false;       // Enable kernel preemption
};

/**
 * @brief Virtual compute unit configuration
 */
struct VirtualComputeUnitConfig {
    int numComputeUnits;                 // Number of compute units
    int numStreams;                      // Number of CUDA streams
    int maxConcurrentKernels;            // Maximum concurrent kernels
    bool enableTensorCores;              // Enable tensor cores
    bool enableMixedPrecision;           // Enable mixed precision
    float computeShare;                  // Compute share (0.0-1.0)
    std::string name;                    // Virtual compute unit name
};

/**
 * @brief Kernel configuration
 */
struct KernelConfig {
    std::string kernelName;              // Kernel name
    dim3 gridDim;                        // Grid dimensions
    dim3 blockDim;                       // Block dimensions
    size_t sharedMemorySize;             // Shared memory size
    cudaStream_t stream;                 // CUDA stream
    int priority;                        // Kernel priority
    std::string kernelType;              // Kernel type (compute, memory, etc.)
};

/**
 * @brief Kernel execution status
 */
enum class KernelExecutionStatus {
    QUEUED,
    RUNNING,
    COMPLETED,
    FAILED,
    CANCELLED
};

/**
 * @brief Virtual compute unit status
 */
enum class VirtualComputeUnitStatus {
    NOT_FOUND,
    CREATED,
    RUNNING,
    PAUSED,
    ERROR,
    DESTROYED
};

/**
 * @brief Load balancing action type
 */
enum class LoadBalancingActionType {
    MIGRATE_KERNEL,
    ADJUST_COMPUTE_SHARE,
    SCALE_COMPUTE_UNITS,
    PREEMPT_KERNEL
};

/**
 * @brief Kernel execution tracking
 */
struct KernelExecution {
    KernelConfig kernelConfig;           // Kernel configuration
    int streamId;                        // Stream ID
    KernelExecutionStatus status;        // Execution status
    std::chrono::steady_clock::time_point startTime;  // Start time
    std::chrono::steady_clock::time_point endTime;    // End time
    int executionId;                     // Unique execution ID
};

/**
 * @brief Load information
 */
struct LoadInfo {
    int virtualGPUId;                    // Virtual GPU ID
    float computeUtilization;            // Compute utilization
    int activeKernels;                   // Active kernels
    float memoryUtilization;             // Memory utilization
    int queueLength;                     // Queue length
};

/**
 * @brief Load balancing action
 */
struct LoadBalancingAction {
    LoadBalancingActionType type;        // Action type
    int sourceGPUId;                     // Source GPU ID
    int targetGPUId;                     // Target GPU ID
    int kernelId;                        // Kernel ID
    float computeShare;                  // Compute share
    int numComputeUnits;                 // Number of compute units
};

/**
 * @brief Virtual compute unit
 */
struct VirtualComputeUnit {
    int virtualGPUId;                    // Virtual GPU ID
    VirtualComputeUnitConfig config;     // Configuration
    VirtualComputeUnitStatus status;     // Current status
    float computeUtilization;            // Compute utilization (0.0-1.0)
    float memoryUtilization;             // Memory utilization (0.0-1.0)
    int activeKernels;                   // Number of active kernels
    int totalKernelsExecuted;            // Total kernels executed
    
    // CUDA resources
    std::vector<cudaStream_t> streams;   // CUDA streams
    cublasHandle_t cublasHandle;         // cuBLAS handle
    cudnnHandle_t cudnnHandle;           // cuDNN handle
    
    // Kernel management
    std::queue<KernelExecution> kernelQueue; // Kernel execution queue
    std::vector<KernelExecution> kernelExecutions; // Active kernel executions
};

/**
 * @brief Virtual compute unit information
 */
struct VirtualComputeUnitInfo {
    int virtualGPUId;                    // Virtual GPU ID
    VirtualComputeUnitStatus status;     // Current status
    float computeUtilization;            // Compute utilization
    float memoryUtilization;             // Memory utilization
    int activeKernels;                   // Active kernels
    int totalKernelsExecuted;            // Total kernels executed
    int numStreams;                      // Number of streams
    int numComputeUnits;                 // Number of compute units
    std::string name;                    // Virtual compute unit name
};

/**
 * @brief Compute Virtualization Manager
 * 
 * This class provides advanced compute virtualization capabilities for GPU compute units.
 * It includes features like:
 * - Virtual compute units for each virtual GPU
 * - Compute unit scheduling and management
 * - Load balancing across virtual compute units
 * - Kernel execution management
 * - Dynamic resource scaling
 */
class ComputeVirtualizationManager {
public:
    // Singleton pattern
    static ComputeVirtualizationManager& getInstance();
    
    // Disable copy constructor and assignment operator
    ComputeVirtualizationManager(const ComputeVirtualizationManager&) = delete;
    ComputeVirtualizationManager& operator=(const ComputeVirtualizationManager&) = delete;
    
    // Initialization and shutdown
    bool initialize(const ComputeVirtualizationConfig& config);
    void shutdown();
    
    // Virtual compute unit management
    bool createVirtualComputeUnit(int virtualGPUId, const VirtualComputeUnitConfig& config);
    bool destroyVirtualComputeUnit(int virtualGPUId);
    VirtualComputeUnitInfo getVirtualComputeUnitInfo(int virtualGPUId) const;
    std::vector<VirtualComputeUnitInfo> getAllVirtualComputeUnitInfo() const;
    
    // Kernel execution
    bool executeKernel(int virtualGPUId, const KernelConfig& kernelConfig, int streamId = 0);
    bool synchronize(int virtualGPUId, int streamId);
    bool cancelKernel(int virtualGPUId, int executionId);
    
    // Resource management
    bool setComputeShare(int virtualGPUId, float computeShare);
    bool enableTensorCores(int virtualGPUId);
    bool disableTensorCores(int virtualGPUId);
    bool scaleComputeUnits(int virtualGPUId, int numComputeUnits);
    
    // Monitoring and statistics
    float getGPUUtilization() const { return gpuUtilization_; }
    ComputeVirtualizationConfig getConfig() const { return config_; }
    bool isInitialized() const { return initialized_; }

private:
    // Private constructor for singleton
    ComputeVirtualizationManager() = default;
    ~ComputeVirtualizationManager() = default;
    
    // Configuration
    ComputeVirtualizationConfig config_;
    cudaDeviceProp deviceProps_;
    bool initialized_ = false;
    
    // NVML resources
    nvmlDevice_t nvmlDevice_;
    
    // Compute unit management
    std::unique_ptr<ComputeUnitManager> computeUnitManager_;
    
    // Scheduler
    std::unique_ptr<ComputeScheduler> scheduler_;
    
    // Load balancer
    std::unique_ptr<LoadBalancer> loadBalancer_;
    
    // Virtual compute units
    std::unordered_map<int, VirtualComputeUnit> virtualComputeUnits_;
    
    // Monitoring
    float gpuUtilization_ = 0.0f;
    std::thread monitoringThread_;
    mutable std::mutex mutex_;
    bool running_ = false;
    
    // Initialization helpers
    bool initializeComputeUnits();
    bool initializeScheduler();
    bool initializeLoadBalancer();
    
    // Cleanup helpers
    void cleanupComputeUnits();
    void cleanupScheduler();
    void cleanupLoadBalancer();
    
    // Monitoring
    void monitoringLoop();
    void updateGPUUtilization();
    void updateComputeUnitStatistics();
    void performLoadBalancing();
    void processKernelQueue();
    
    // Resource management
    bool allocateComputeResources(VirtualComputeUnit& unit);
    void freeComputeResources(VirtualComputeUnit& unit);
    bool checkComputeResourceAvailability(const VirtualComputeUnit& unit, const KernelConfig& kernelConfig);
    
    // Kernel management
    void updateKernelExecutionStatus(VirtualComputeUnit& unit, int streamId);
    bool canExecuteKernel(const VirtualComputeUnit& unit, const KernelExecution& execution);
    bool executeKernelOnDevice(VirtualComputeUnit& unit, KernelExecution& execution);
    
    // Load balancing
    void applyLoadBalancingAction(const LoadBalancingAction& action);
    void migrateKernel(int sourceGPUId, int targetGPUId, int kernelId);
    
    // Error handling
    void logError(const std::string& operation, const std::string& error) const;
    void logWarning(const std::string& operation, const std::string& warning) const;
};

/**
 * @brief Compute Unit Manager
 */
class ComputeUnitManager {
public:
    ComputeUnitManager() = default;
    ~ComputeUnitManager() = default;
    
    bool initialize(int numPhysicalComputeUnits, int maxVirtualComputeUnits);
    void shutdown();
    
    bool allocateComputeUnits(int virtualGPUId, int numComputeUnits);
    bool freeComputeUnits(int virtualGPUId);
    int getAvailableComputeUnits() const;
    int getTotalComputeUnits() const;

private:
    int numPhysicalComputeUnits_ = 0;
    int maxVirtualComputeUnits_ = 0;
    int availableComputeUnits_ = 0;
    std::unordered_map<int, int> virtualGPUAllocations_;
    mutable std::mutex mutex_;
};

/**
 * @brief Compute Scheduler
 */
class ComputeScheduler {
public:
    ComputeScheduler() = default;
    ~ComputeScheduler() = default;
    
    bool initialize(const std::string& policy, int timeSlice);
    void shutdown();
    
    void updateComputeShare(int virtualGPUId, float computeShare);
    int selectNextVirtualGPU();
    bool shouldPreempt(int currentVirtualGPUId, int newVirtualGPUId) const;

private:
    std::string policy_ = "round_robin";
    int timeSlice_ = 100;
    std::unordered_map<int, float> computeShares_;
    int currentVirtualGPU_ = -1;
    mutable std::mutex mutex_;
};

/**
 * @brief Load Balancer
 */
class LoadBalancer {
public:
    LoadBalancer() = default;
    ~LoadBalancer() = default;
    
    bool initialize(const std::string& strategy);
    void shutdown();
    
    std::vector<LoadBalancingAction> balance(const std::vector<LoadInfo>& loadInfos);
    bool shouldRebalance(const std::vector<LoadInfo>& loadInfos) const;

private:
    std::string strategy_ = "least_loaded";
    float rebalanceThreshold_ = 0.2f;
    mutable std::mutex mutex_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_COMPUTE_VIRTUALIZATION_MANAGER_H 