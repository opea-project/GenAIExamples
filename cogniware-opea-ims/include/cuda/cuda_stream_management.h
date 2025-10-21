#pragma once

#include <cuda_runtime.h>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <map>
#include <string>
#include <chrono>
#include <functional>
#include <queue>
#include <thread>
#include <condition_variable>
#include <future>

namespace cogniware {
namespace cuda {

// CUDA stream priority levels
enum class CUDAStreamPriority {
    LOW = 0,                // Low priority
    NORMAL = 1,             // Normal priority
    HIGH = 2,               // High priority
    CRITICAL = 3           // Critical priority
};

// CUDA stream types
enum class CUDAStreamType {
    COMPUTE_STREAM,         // Compute stream
    MEMORY_STREAM,          // Memory transfer stream
    KERNEL_STREAM,          // Kernel execution stream
    COMMUNICATION_STREAM,   // Inter-GPU communication stream
    CUSTOM_STREAM           // Custom stream
};

// CUDA stream status
enum class CUDAStreamStatus {
    IDLE,                   // Stream is idle
    RUNNING,                // Stream is running
    WAITING,                // Stream is waiting
    COMPLETED,              // Stream has completed
    ERROR,                  // Stream encountered an error
    SUSPENDED               // Stream is suspended
};

// CUDA memory barrier types
enum class CUDAMemoryBarrierType {
    GLOBAL_BARRIER,         // Global memory barrier
    SHARED_BARRIER,         // Shared memory barrier
    CONSTANT_BARRIER,       // Constant memory barrier
    TEXTURE_BARRIER,        // Texture memory barrier
    SURFACE_BARRIER,         // Surface memory barrier
    CUSTOM_BARRIER          // Custom memory barrier
};

// CUDA stream configuration
struct CUDAStreamConfig {
    std::string streamId;                   // Stream identifier
    CUDAStreamType type;                    // Stream type
    CUDAStreamPriority priority;           // Stream priority
    int deviceId;                          // GPU device ID
    bool isNonBlocking;                    // Non-blocking flag
    bool enableProfiling;                   // Profiling enabled
    bool enableSynchronization;             // Synchronization enabled
    size_t maxConcurrentKernels;            // Maximum concurrent kernels
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// CUDA stream task
struct CUDAStreamTask {
    std::string taskId;                     // Task identifier
    std::string streamId;                   // Stream identifier
    std::function<void()> kernelFunction;   // Kernel function
    std::vector<void*> inputPointers;       // Input memory pointers
    std::vector<void*> outputPointers;      // Output memory pointers
    std::vector<size_t> inputSizes;         // Input memory sizes
    std::vector<size_t> outputSizes;       // Output memory sizes
    dim3 gridDim;                          // Grid dimensions
    dim3 blockDim;                         // Block dimensions
    size_t sharedMemSize;                  // Shared memory size
    CUDAStreamPriority priority;           // Task priority
    std::chrono::milliseconds timeout;     // Task timeout
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// CUDA stream result
struct CUDAStreamResult {
    std::string taskId;                     // Task identifier
    std::string streamId;                   // Stream identifier
    bool success;                           // Task success
    float executionTime;                    // Execution time (ms)
    float memoryBandwidth;                  // Memory bandwidth (GB/s)
    float computeThroughput;                // Compute throughput (GFLOPS)
    std::string error;                      // Error message if failed
    std::chrono::system_clock::time_point completedAt; // Completion time
};

// CUDA memory barrier
struct CUDAMemoryBarrier {
    std::string barrierId;                   // Barrier identifier
    CUDAMemoryBarrierType type;             // Barrier type
    std::vector<void*> memoryPointers;      // Memory pointers
    std::vector<size_t> memorySizes;       // Memory sizes
    bool isActive;                          // Barrier active status
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// CUDA stream interface
class CUDAStream {
public:
    virtual ~CUDAStream() = default;

    // Stream lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Stream management
    virtual std::string getStreamId() const = 0;
    virtual CUDAStreamStatus getStatus() const = 0;
    virtual CUDAStreamConfig getConfig() const = 0;
    virtual bool updateConfig(const CUDAStreamConfig& config) = 0;

    // Task operations
    virtual std::future<CUDAStreamResult> executeTaskAsync(const CUDAStreamTask& task) = 0;
    virtual CUDAStreamResult executeTask(const CUDAStreamTask& task) = 0;
    virtual bool cancelTask(const std::string& taskId) = 0;
    virtual std::vector<std::string> getActiveTasks() const = 0;
    virtual bool isTaskActive(const std::string& taskId) const = 0;

    // Memory barrier operations
    virtual std::string createMemoryBarrier(const CUDAMemoryBarrier& barrier) = 0;
    virtual bool destroyMemoryBarrier(const std::string& barrierId) = 0;
    virtual bool synchronizeMemoryBarrier(const std::string& barrierId) = 0;
    virtual std::vector<std::string> getActiveBarriers() const = 0;
    virtual bool isBarrierActive(const std::string& barrierId) const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setPriority(CUDAStreamPriority priority) = 0;
    virtual CUDAStreamPriority getPriority() const = 0;
    virtual bool setType(CUDAStreamType type) = 0;
    virtual CUDAStreamType getType() const = 0;
};

// Advanced CUDA stream implementation
class AdvancedCUDAStream : public CUDAStream {
public:
    AdvancedCUDAStream(const CUDAStreamConfig& config);
    ~AdvancedCUDAStream() override;

    // Stream lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Stream management
    std::string getStreamId() const override;
    CUDAStreamStatus getStatus() const override;
    CUDAStreamConfig getConfig() const override;
    bool updateConfig(const CUDAStreamConfig& config) override;

    // Task operations
    std::future<CUDAStreamResult> executeTaskAsync(const CUDAStreamTask& task) override;
    CUDAStreamResult executeTask(const CUDAStreamTask& task) override;
    bool cancelTask(const std::string& taskId) override;
    std::vector<std::string> getActiveTasks() const override;
    bool isTaskActive(const std::string& taskId) const override;

    // Memory barrier operations
    std::string createMemoryBarrier(const CUDAMemoryBarrier& barrier) override;
    bool destroyMemoryBarrier(const std::string& barrierId) override;
    bool synchronizeMemoryBarrier(const std::string& barrierId) override;
    std::vector<std::string> getActiveBarriers() const override;
    bool isBarrierActive(const std::string& barrierId) const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setPriority(CUDAStreamPriority priority) override;
    CUDAStreamPriority getPriority() const override;
    bool setType(CUDAStreamType type) override;
    CUDAStreamType getType() const override;

    // Advanced features
    bool synchronize();
    bool waitForCompletion();
    bool pause();
    bool resume();
    bool reset();
    bool optimize();
    std::map<std::string, std::string> getResourceInfo() const;
    bool validateResources() const;
    bool setMaxConcurrentKernels(size_t maxKernels);
    size_t getMaxConcurrentKernels() const;
    bool setDevice(int deviceId);
    int getDevice() const;

private:
    // Internal state
    CUDAStreamConfig config_;
    CUDAStreamStatus status_;
    bool initialized_;
    CUDAStreamPriority priority_;
    CUDAStreamType streamType_;
    std::mutex streamMutex_;
    std::atomic<bool> profilingEnabled_;

    // Task tracking
    std::map<std::string, std::future<CUDAStreamResult>> activeTasks_;
    std::map<std::string, std::atomic<bool>> taskCancelled_;
    std::mutex taskMutex_;

    // Memory barrier tracking
    std::map<std::string, CUDAMemoryBarrier> memoryBarriers_;
    std::mutex barrierMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // CUDA resources
    cudaStream_t cudaStream_;
    cudaEvent_t streamEvent_;
    int deviceId_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool validateTask(const CUDAStreamTask& task);
    void updatePerformanceMetrics();
    CUDAStreamResult executeTaskInternal(const CUDAStreamTask& task);
    void cleanupTask(const std::string& taskId);
    std::string generateTaskId();
    std::string generateBarrierId();
    bool validateBarrier(const CUDAMemoryBarrier& barrier);
    bool executeKernel(const CUDAStreamTask& task);
    bool synchronizeMemory(const CUDAMemoryBarrier& barrier);
    float calculateExecutionTime(const std::chrono::high_resolution_clock::time_point& start,
                                const std::chrono::high_resolution_clock::time_point& end);
    float calculateMemoryBandwidth(const CUDAStreamTask& task, float executionTime);
    float calculateComputeThroughput(const CUDAStreamTask& task, float executionTime);
};

// CUDA stream manager
class CUDAStreamManager {
public:
    CUDAStreamManager();
    ~CUDAStreamManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Stream management
    std::shared_ptr<CUDAStream> createStream(const CUDAStreamConfig& config);
    bool destroyStream(const std::string& streamId);
    std::shared_ptr<CUDAStream> getStream(const std::string& streamId);
    std::vector<std::shared_ptr<CUDAStream>> getAllStreams();
    std::vector<std::shared_ptr<CUDAStream>> getStreamsByType(CUDAStreamType type);
    std::vector<std::shared_ptr<CUDAStream>> getStreamsByPriority(CUDAStreamPriority priority);

    // Task management
    std::future<CUDAStreamResult> executeTaskAsync(const CUDAStreamTask& task);
    CUDAStreamResult executeTask(const CUDAStreamTask& task);
    bool cancelTask(const std::string& taskId);
    bool cancelAllTasks();
    std::vector<std::string> getActiveTasks();
    std::vector<std::string> getActiveTasksByStream(const std::string& streamId);

    // Memory barrier management
    std::string createMemoryBarrier(const CUDAMemoryBarrier& barrier);
    bool destroyMemoryBarrier(const std::string& barrierId);
    bool synchronizeMemoryBarrier(const std::string& barrierId);
    std::vector<std::string> getActiveBarriers();
    std::vector<std::string> getActiveBarriersByStream(const std::string& streamId);

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleStreams();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getStreamCounts();
    std::map<std::string, double> getTaskMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMaxStreams(int maxStreams);
    int getMaxStreams() const;
    void setSchedulingStrategy(const std::string& strategy);
    std::string getSchedulingStrategy() const;
    void setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<CUDAStream>> streams_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    int maxStreams_;
    std::string schedulingStrategy_;
    std::string loadBalancingStrategy_;

    // Task tracking
    std::map<std::string, std::string> taskToStream_;
    std::map<std::string, std::chrono::system_clock::time_point> taskStartTime_;

    // Memory barrier tracking
    std::map<std::string, std::string> barrierToStream_;
    std::map<std::string, std::chrono::system_clock::time_point> barrierStartTime_;

    // Helper methods
    bool validateStreamCreation(const CUDAStreamConfig& config);
    bool validateTaskExecution(const CUDAStreamTask& task);
    std::string generateStreamId();
    bool cleanupStream(const std::string& streamId);
    void updateSystemMetrics();
    bool findBestStream(const CUDAStreamTask& task, std::string& bestStreamId);
    bool executeOnStream(const std::string& streamId, const CUDAStreamTask& task);
    std::vector<std::string> selectStreamsForTask(const CUDAStreamTask& task);
    bool validateSystemConfiguration();
    bool optimizeSystemConfiguration();
    bool balanceSystemLoad();
};

// Global CUDA stream management system
class GlobalCUDAStreamManagementSystem {
public:
    static GlobalCUDAStreamManagementSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<CUDAStreamManager> getStreamManager();
    std::shared_ptr<CUDAStream> createStream(const CUDAStreamConfig& config);
    bool destroyStream(const std::string& streamId);
    std::shared_ptr<CUDAStream> getStream(const std::string& streamId);

    // Quick access methods
    std::future<CUDAStreamResult> executeTaskAsync(const CUDAStreamTask& task);
    CUDAStreamResult executeTask(const CUDAStreamTask& task);
    std::vector<std::shared_ptr<CUDAStream>> getAllStreams();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalCUDAStreamManagementSystem();
    ~GlobalCUDAStreamManagementSystem();

    std::shared_ptr<CUDAStreamManager> streamManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace cuda
} // namespace cogniware
