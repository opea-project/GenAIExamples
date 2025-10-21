#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <map>
#include <thread>
#include <condition_variable>
#include <chrono>
#include <functional>
#include <future>
#include <spdlog/spdlog.h>

namespace cogniware {
namespace orchestration {

// Orchestration types
enum class OrchestrationType {
    PARALLEL,               // Parallel processing
    SEQUENTIAL,             // Sequential processing
    PIPELINE,               // Pipeline processing
    HYBRID                  // Hybrid processing
};

// LLM status
enum class LLMStatus {
    IDLE,                   // LLM is idle
    LOADING,                // LLM is loading
    READY,                  // LLM is ready
    EXECUTING,              // LLM is executing
    COMPLETED,              // LLM has completed
    ERROR,                  // LLM has error
    SUSPENDED               // LLM is suspended
};

// Task priority
enum class TaskPriority {
    LOW = 0,                // Low priority
    NORMAL = 1,             // Normal priority
    HIGH = 2,               // High priority
    CRITICAL = 3,           // Critical priority
    URGENT = 4              // Urgent priority
};

// Orchestration configuration
struct OrchestrationConfig {
    std::string orchestratorId;             // Orchestrator identifier
    OrchestrationType type;                  // Orchestration type
    int maxConcurrentLLMs;                   // Maximum concurrent LLMs
    int maxQueueSize;                        // Maximum queue size
    std::chrono::milliseconds timeout;      // Default timeout
    bool enableLoadBalancing;                // Enable load balancing
    bool enableResultAggregation;           // Enable result aggregation
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// LLM task
struct LLMTask {
    std::string taskId;                      // Task identifier
    std::string llmId;                       // LLM identifier
    std::string prompt;                      // Input prompt
    std::string response;                    // Output response
    TaskPriority priority;                   // Task priority
    std::chrono::milliseconds timeout;      // Task timeout
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point completedAt; // Completion time
};

// LLM instance
struct LLMInstance {
    std::string llmId;                       // LLM identifier
    std::string modelName;                   // Model name
    std::string modelPath;                   // Model path
    LLMStatus status;                        // LLM status
    float utilization;                       // Utilization (0.0 to 1.0)
    int activeTasks;                          // Number of active tasks
    int maxTasks;                            // Maximum tasks
    std::chrono::system_clock::time_point lastUpdated; // Last update time
};

// Result aggregation
struct AggregatedResult {
    std::string requestId;                   // Request identifier
    std::vector<std::string> responses;     // Individual responses
    std::string aggregatedResponse;          // Aggregated response
    float confidence;                        // Confidence score
    std::chrono::system_clock::time_point aggregatedAt; // Aggregation time
};

// Multi-LLM orchestrator interface
class MultiLLMOrchestrator {
public:
    virtual ~MultiLLMOrchestrator() = default;

    // Orchestrator lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Orchestrator management
    virtual std::string getOrchestratorId() const = 0;
    virtual OrchestrationConfig getConfig() const = 0;
    virtual bool updateConfig(const OrchestrationConfig& config) = 0;

    // LLM management
    virtual bool registerLLM(const LLMInstance& llmInstance) = 0;
    virtual bool unregisterLLM(const std::string& llmId) = 0;
    virtual std::vector<LLMInstance> getRegisteredLLMs() const = 0;
    virtual LLMInstance getLLMInstance(const std::string& llmId) const = 0;

    // Task management
    virtual std::future<AggregatedResult> processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) = 0;
    virtual AggregatedResult processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) = 0;
    virtual bool cancelRequest(const std::string& requestId) = 0;
    virtual std::vector<std::string> getActiveRequests() const = 0;
    virtual bool isRequestActive(const std::string& requestId) const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setOrchestrationType(OrchestrationType type) = 0;
    virtual OrchestrationType getOrchestrationType() const = 0;
    virtual bool setMaxConcurrentLLMs(int maxLLMs) = 0;
    virtual int getMaxConcurrentLLMs() const = 0;
};

// Advanced multi-LLM orchestrator implementation
class AdvancedMultiLLMOrchestrator : public MultiLLMOrchestrator {
public:
    AdvancedMultiLLMOrchestrator(const OrchestrationConfig& config);
    ~AdvancedMultiLLMOrchestrator() override;

    // Orchestrator lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Orchestrator management
    std::string getOrchestratorId() const override;
    OrchestrationConfig getConfig() const override;
    bool updateConfig(const OrchestrationConfig& config) override;

    // LLM management
    bool registerLLM(const LLMInstance& llmInstance) override;
    bool unregisterLLM(const std::string& llmId) override;
    std::vector<LLMInstance> getRegisteredLLMs() const override;
    LLMInstance getLLMInstance(const std::string& llmId) const override;

    // Task management
    std::future<AggregatedResult> processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) override;
    AggregatedResult processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) override;
    bool cancelRequest(const std::string& requestId) override;
    std::vector<std::string> getActiveRequests() const override;
    bool isRequestActive(const std::string& requestId) const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setOrchestrationType(OrchestrationType type) override;
    OrchestrationType getOrchestrationType() const override;
    bool setMaxConcurrentLLMs(int maxLLMs) override;
    int getMaxConcurrentLLMs() const override;

    // Advanced features
    bool optimizeOrchestration();
    bool balanceLoad();
    bool aggregateResults();
    std::map<std::string, std::string> getOrchestratorInfo() const;
    bool validateConfiguration() const;
    bool setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;
    bool setResultAggregationStrategy(const std::string& strategy);
    std::string getResultAggregationStrategy() const;

private:
    // Internal state
    OrchestrationConfig config_;
    bool initialized_;
    OrchestrationType orchestrationType_;
    std::mutex orchestratorMutex_;
    std::atomic<bool> profilingEnabled_;

    // LLM management
    std::map<std::string, LLMInstance> registeredLLMs_;
    std::mutex llmMutex_;

    // Task management
    std::map<std::string, std::future<AggregatedResult>> activeRequests_;
    std::map<std::string, std::vector<LLMTask>> requestTasks_;
    std::mutex taskMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // Orchestrator thread
    std::thread orchestratorThread_;
    std::atomic<bool> stopOrchestrator_;

    // Load balancing
    std::string loadBalancingStrategy_;
    std::string resultAggregationStrategy_;

    // Helper methods
    void orchestratorLoop();
    bool validateLLMInstance(const LLMInstance& llmInstance);
    void updatePerformanceMetrics();
    AggregatedResult processRequestInternal(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    void cleanupRequest(const std::string& requestId);
    std::string generateRequestId();
    std::string selectBestLLM(const std::string& prompt, const std::map<std::string, std::string>& parameters);
    bool assignTaskToLLM(const std::string& taskId, const std::string& llmId);
    void updateLLMUtilization(const std::string& llmId);
    float calculateLLMScore(const LLMInstance& llm, const std::string& prompt);
    bool canLLMHandleTask(const LLMInstance& llm);
    void processRequestQueue();
    void handleRequestCompletion(const std::string& requestId, const AggregatedResult& result);
    void handleRequestFailure(const std::string& requestId, const std::string& error);
    void rebalanceLLMs();
    void cleanupCompletedRequests();
    std::string generateTaskId();
    bool validateRequestParameters(const std::map<std::string, std::string>& parameters);
    void updateRequestStatus(const std::string& requestId, const std::string& status);
    float calculateRequestPriority(const std::string& prompt, const std::map<std::string, std::string>& parameters);
    void optimizeRequestQueue();
    void scaleUpLLMs();
    void scaleDownLLMs();
    bool isLLMOverloaded(const LLMInstance& llm);
    bool isLLMUnderloaded(const LLMInstance& llm);
    AggregatedResult aggregateResults(const std::vector<std::string>& responses);
    float calculateConfidence(const std::vector<std::string>& responses);
    std::string generateAggregatedResponse(const std::vector<std::string>& responses);
};

// Multi-LLM orchestrator manager
class MultiLLMOrchestratorManager {
public:
    MultiLLMOrchestratorManager();
    ~MultiLLMOrchestratorManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Orchestrator management
    std::shared_ptr<MultiLLMOrchestrator> createOrchestrator(const OrchestrationConfig& config);
    bool destroyOrchestrator(const std::string& orchestratorId);
    std::shared_ptr<MultiLLMOrchestrator> getOrchestrator(const std::string& orchestratorId);
    std::vector<std::shared_ptr<MultiLLMOrchestrator>> getAllOrchestrators();
    std::vector<std::shared_ptr<MultiLLMOrchestrator>> getOrchestratorsByType(OrchestrationType type);

    // Request management
    std::future<AggregatedResult> processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    AggregatedResult processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    bool cancelRequest(const std::string& requestId);
    bool cancelAllRequests();
    std::vector<std::string> getActiveRequests();
    std::vector<std::string> getActiveRequestsByOrchestrator(const std::string& orchestratorId);

    // LLM management
    bool registerLLM(const LLMInstance& llmInstance);
    bool unregisterLLM(const std::string& llmId);
    std::vector<LLMInstance> getRegisteredLLMs();
    LLMInstance getLLMInstance(const std::string& llmId);

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleOrchestrators();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getOrchestratorCounts();
    std::map<std::string, double> getRequestMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMaxOrchestrators(int maxOrchestrators);
    int getMaxOrchestrators() const;
    void setOrchestrationStrategy(const std::string& strategy);
    std::string getOrchestrationStrategy() const;
    void setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<MultiLLMOrchestrator>> orchestrators_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    int maxOrchestrators_;
    std::string orchestrationStrategy_;
    std::string loadBalancingStrategy_;

    // Request tracking
    std::map<std::string, std::string> requestToOrchestrator_;
    std::map<std::string, std::chrono::system_clock::time_point> requestStartTime_;

    // LLM tracking
    std::map<std::string, std::vector<std::string>> llmToOrchestrators_;

    // Helper methods
    bool validateOrchestratorCreation(const OrchestrationConfig& config);
    bool validateRequestParameters(const std::map<std::string, std::string>& parameters);
    std::string generateOrchestratorId();
    bool cleanupOrchestrator(const std::string& orchestratorId);
    void updateSystemMetrics();
    bool findBestOrchestrator(const std::string& prompt, const std::map<std::string, std::string>& parameters, std::string& bestOrchestratorId);
    bool executeOnOrchestrator(const std::string& orchestratorId, const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    std::vector<std::string> selectOrchestratorsForRequest(const std::string& prompt, const std::map<std::string, std::string>& parameters);
    bool validateSystemConfiguration();
    bool optimizeSystemConfiguration();
    bool balanceSystemLoad();
};

// Global multi-LLM orchestration system
class GlobalMultiLLMOrchestrationSystem {
public:
    static GlobalMultiLLMOrchestrationSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<MultiLLMOrchestratorManager> getOrchestratorManager();
    std::shared_ptr<MultiLLMOrchestrator> createOrchestrator(const OrchestrationConfig& config);
    bool destroyOrchestrator(const std::string& orchestratorId);
    std::shared_ptr<MultiLLMOrchestrator> getOrchestrator(const std::string& orchestratorId);

    // Quick access methods
    std::future<AggregatedResult> processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    AggregatedResult processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters);
    std::vector<std::shared_ptr<MultiLLMOrchestrator>> getAllOrchestrators();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalMultiLLMOrchestrationSystem();
    ~GlobalMultiLLMOrchestrationSystem();

    std::shared_ptr<MultiLLMOrchestratorManager> orchestratorManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace orchestration
} // namespace cogniware
