#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <map>
#include <queue>
#include <thread>
#include <condition_variable>
#include <chrono>
#include <functional>
#include <future>
#include <spdlog/spdlog.h>

namespace cogniware {
namespace scheduler {

// Task priority levels
enum class TaskPriority {
    LOW = 0,                // Low priority
    NORMAL = 1,             // Normal priority
    HIGH = 2,               // High priority
    CRITICAL = 3,           // Critical priority
    URGENT = 4              // Urgent priority
};

// Task status
enum class TaskStatus {
    PENDING,                // Task is pending
    QUEUED,                 // Task is queued
    RUNNING,                // Task is running
    COMPLETED,              // Task has completed
    FAILED,                 // Task has failed
    CANCELLED,              // Task was cancelled
    SUSPENDED               // Task is suspended
};

// Scheduler types
enum class SchedulerType {
    FIFO,                   // First In, First Out
    PRIORITY,               // Priority-based
    WEIGHTED,               // Weight-based
    ROUND_ROBIN,            // Round-robin
    LEAST_LOADED,           // Least loaded
    CUSTOM                  // Custom scheduler
};

// Task configuration
struct TaskConfig {
    std::string taskId;                     // Task identifier
    std::string taskName;                   // Task name
    std::string taskType;                   // Task type
    TaskPriority priority;                  // Task priority
    float weight;                           // Task weight (0.0 to 1.0)
    std::string assignedNode;              // Assigned compute node
    std::chrono::milliseconds timeout;     // Task timeout
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point scheduledAt; // Scheduled time
};

// Task execution request
struct TaskExecutionRequest {
    std::string requestId;                  // Request identifier
    std::string taskId;                     // Task identifier
    std::function<void()> taskFunction;     // Task function
    std::vector<std::string> dependencies; // Task dependencies
    TaskPriority priority;                  // Task priority
    float weight;                           // Task weight
    std::chrono::milliseconds timeout;     // Request timeout
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// Task execution result
struct TaskExecutionResult {
    std::string requestId;                  // Request identifier
    std::string taskId;                     // Task identifier
    bool success;                           // Execution success
    TaskStatus status;                      // Task status
    float executionTime;                    // Execution time (ms)
    float cpuUtilization;                   // CPU utilization
    float memoryUtilization;                // Memory utilization
    std::string error;                      // Error message if failed
    std::chrono::system_clock::time_point completedAt; // Completion time
};

// Compute node information
struct ComputeNodeInfo {
    std::string nodeId;                     // Node identifier
    std::string nodeName;                   // Node name
    std::string nodeType;                   // Node type
    int totalCores;                         // Total CPU cores
    int availableCores;                     // Available CPU cores
    size_t totalMemory;                     // Total memory (bytes)
    size_t availableMemory;                 // Available memory (bytes)
    float cpuUtilization;                   // CPU utilization (0.0 to 1.0)
    float memoryUtilization;                // Memory utilization (0.0 to 1.0)
    int activeTasks;                        // Number of active tasks
    int maxTasks;                           // Maximum tasks
    bool isOnline;                          // Node online status
    std::chrono::system_clock::time_point lastUpdated; // Last update time
};

// Scheduler configuration
struct SchedulerConfig {
    std::string schedulerId;                // Scheduler identifier
    SchedulerType type;                     // Scheduler type
    int maxQueueSize;                       // Maximum queue size
    int maxConcurrentTasks;                 // Maximum concurrent tasks
    std::chrono::milliseconds taskTimeout; // Default task timeout
    bool enableLoadBalancing;               // Enable load balancing
    bool enableAutoScaling;                 // Enable auto scaling
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// Compute node scheduler interface
class ComputeNodeScheduler {
public:
    virtual ~ComputeNodeScheduler() = default;

    // Scheduler lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Scheduler management
    virtual std::string getSchedulerId() const = 0;
    virtual SchedulerConfig getConfig() const = 0;
    virtual bool updateConfig(const SchedulerConfig& config) = 0;

    // Task management
    virtual std::future<TaskExecutionResult> submitTaskAsync(const TaskExecutionRequest& request) = 0;
    virtual TaskExecutionResult submitTask(const TaskExecutionRequest& request) = 0;
    virtual bool cancelTask(const std::string& taskId) = 0;
    virtual bool suspendTask(const std::string& taskId) = 0;
    virtual bool resumeTask(const std::string& taskId) = 0;
    virtual std::vector<std::string> getActiveTasks() const = 0;
    virtual bool isTaskActive(const std::string& taskId) const = 0;

    // Compute node management
    virtual bool registerNode(const ComputeNodeInfo& nodeInfo) = 0;
    virtual bool unregisterNode(const std::string& nodeId) = 0;
    virtual std::vector<ComputeNodeInfo> getAvailableNodes() const = 0;
    virtual ComputeNodeInfo getNodeInfo(const std::string& nodeId) const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setSchedulerType(SchedulerType type) = 0;
    virtual SchedulerType getSchedulerType() const = 0;
    virtual bool setMaxQueueSize(int maxSize) = 0;
    virtual int getMaxQueueSize() const = 0;
};

// Advanced compute node scheduler implementation
class AdvancedComputeNodeScheduler : public ComputeNodeScheduler {
public:
    AdvancedComputeNodeScheduler(const SchedulerConfig& config);
    ~AdvancedComputeNodeScheduler() override;

    // Scheduler lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Scheduler management
    std::string getSchedulerId() const override;
    SchedulerConfig getConfig() const override;
    bool updateConfig(const SchedulerConfig& config) override;

    // Task management
    std::future<TaskExecutionResult> submitTaskAsync(const TaskExecutionRequest& request) override;
    TaskExecutionResult submitTask(const TaskExecutionRequest& request) override;
    bool cancelTask(const std::string& taskId) override;
    bool suspendTask(const std::string& taskId) override;
    bool resumeTask(const std::string& taskId) override;
    std::vector<std::string> getActiveTasks() const override;
    bool isTaskActive(const std::string& taskId) const override;

    // Compute node management
    bool registerNode(const ComputeNodeInfo& nodeInfo) override;
    bool unregisterNode(const std::string& nodeId) override;
    std::vector<ComputeNodeInfo> getAvailableNodes() const override;
    ComputeNodeInfo getNodeInfo(const std::string& nodeId) const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setSchedulerType(SchedulerType type) override;
    SchedulerType getSchedulerType() const override;
    bool setMaxQueueSize(int maxSize) override;
    int getMaxQueueSize() const override;

    // Advanced features
    bool optimizeScheduling();
    bool balanceLoad();
    bool scaleNodes();
    std::map<std::string, std::string> getSchedulerInfo() const;
    bool validateConfiguration() const;
    bool setTaskWeight(const std::string& taskId, float weight);
    float getTaskWeight(const std::string& taskId) const;
    bool setNodeCapacity(const std::string& nodeId, int maxTasks);
    int getNodeCapacity(const std::string& nodeId) const;

private:
    // Internal state
    SchedulerConfig config_;
    bool initialized_;
    SchedulerType schedulerType_;
    std::mutex schedulerMutex_;
    std::atomic<bool> profilingEnabled_;

    // Task management
    std::queue<TaskExecutionRequest> taskQueue_;
    std::map<std::string, std::future<TaskExecutionResult>> activeTasks_;
    std::map<std::string, TaskStatus> taskStatus_;
    std::map<std::string, float> taskWeights_;
    std::mutex taskMutex_;

    // Compute node management
    std::map<std::string, ComputeNodeInfo> computeNodes_;
    std::mutex nodeMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // Scheduler thread
    std::thread schedulerThread_;
    std::atomic<bool> stopScheduler_;

    // Helper methods
    void schedulerLoop();
    bool validateTaskRequest(const TaskExecutionRequest& request);
    void updatePerformanceMetrics();
    TaskExecutionResult executeTaskInternal(const TaskExecutionRequest& request);
    void cleanupTask(const std::string& taskId);
    std::string generateTaskId();
    std::string selectBestNode(const TaskExecutionRequest& request);
    bool assignTaskToNode(const std::string& taskId, const std::string& nodeId);
    void updateNodeUtilization(const std::string& nodeId);
    float calculateNodeScore(const ComputeNodeInfo& node, const TaskExecutionRequest& request);
    bool canNodeHandleTask(const ComputeNodeInfo& node, const TaskExecutionRequest& request);
    void processTaskQueue();
    void handleTaskCompletion(const std::string& taskId, const TaskExecutionResult& result);
    void handleTaskFailure(const std::string& taskId, const std::string& error);
    void rebalanceTasks();
    void cleanupCompletedTasks();
    std::string generateRequestId();
    bool validateNodeInfo(const ComputeNodeInfo& nodeInfo);
    void updateTaskStatus(const std::string& taskId, TaskStatus status);
    float calculateTaskPriority(const TaskExecutionRequest& request);
    void optimizeTaskQueue();
    void scaleUpNodes();
    void scaleDownNodes();
    bool isNodeOverloaded(const ComputeNodeInfo& node);
    bool isNodeUnderloaded(const ComputeNodeInfo& node);
};

// Compute node scheduler manager
class ComputeNodeSchedulerManager {
public:
    ComputeNodeSchedulerManager();
    ~ComputeNodeSchedulerManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Scheduler management
    std::shared_ptr<ComputeNodeScheduler> createScheduler(const SchedulerConfig& config);
    bool destroyScheduler(const std::string& schedulerId);
    std::shared_ptr<ComputeNodeScheduler> getScheduler(const std::string& schedulerId);
    std::vector<std::shared_ptr<ComputeNodeScheduler>> getAllSchedulers();
    std::vector<std::shared_ptr<ComputeNodeScheduler>> getSchedulersByType(SchedulerType type);

    // Task management
    std::future<TaskExecutionResult> submitTaskAsync(const TaskExecutionRequest& request);
    TaskExecutionResult submitTask(const TaskExecutionRequest& request);
    bool cancelTask(const std::string& taskId);
    bool cancelAllTasks();
    std::vector<std::string> getActiveTasks();
    std::vector<std::string> getActiveTasksByScheduler(const std::string& schedulerId);

    // Compute node management
    bool registerNode(const ComputeNodeInfo& nodeInfo);
    bool unregisterNode(const std::string& nodeId);
    std::vector<ComputeNodeInfo> getAvailableNodes();
    ComputeNodeInfo getNodeInfo(const std::string& nodeId);

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleSchedulers();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getSchedulerCounts();
    std::map<std::string, double> getTaskMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMaxSchedulers(int maxSchedulers);
    int getMaxSchedulers() const;
    void setSchedulingStrategy(const std::string& strategy);
    std::string getSchedulingStrategy() const;
    void setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<ComputeNodeScheduler>> schedulers_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    int maxSchedulers_;
    std::string schedulingStrategy_;
    std::string loadBalancingStrategy_;

    // Task tracking
    std::map<std::string, std::string> taskToScheduler_;
    std::map<std::string, std::chrono::system_clock::time_point> taskStartTime_;

    // Compute node tracking
    std::map<std::string, std::vector<std::string>> nodeToSchedulers_;

    // Helper methods
    bool validateSchedulerCreation(const SchedulerConfig& config);
    bool validateTaskSubmission(const TaskExecutionRequest& request);
    std::string generateSchedulerId();
    bool cleanupScheduler(const std::string& schedulerId);
    void updateSystemMetrics();
    bool findBestScheduler(const TaskExecutionRequest& request, std::string& bestSchedulerId);
    bool executeOnScheduler(const std::string& schedulerId, const TaskExecutionRequest& request);
    std::vector<std::string> selectSchedulersForTask(const TaskExecutionRequest& request);
    bool validateSystemConfiguration();
    bool optimizeSystemConfiguration();
    bool balanceSystemLoad();
};

// Global compute node scheduler system
class GlobalComputeNodeSchedulerSystem {
public:
    static GlobalComputeNodeSchedulerSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<ComputeNodeSchedulerManager> getSchedulerManager();
    std::shared_ptr<ComputeNodeScheduler> createScheduler(const SchedulerConfig& config);
    bool destroyScheduler(const std::string& schedulerId);
    std::shared_ptr<ComputeNodeScheduler> getScheduler(const std::string& schedulerId);

    // Quick access methods
    std::future<TaskExecutionResult> submitTaskAsync(const TaskExecutionRequest& request);
    TaskExecutionResult submitTask(const TaskExecutionRequest& request);
    std::vector<std::shared_ptr<ComputeNodeScheduler>> getAllSchedulers();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalComputeNodeSchedulerSystem();
    ~GlobalComputeNodeSchedulerSystem();

    std::shared_ptr<ComputeNodeSchedulerManager> schedulerManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace scheduler
} // namespace cogniware
