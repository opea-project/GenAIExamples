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
namespace parallel {

// LLM execution modes
enum class LLMExecutionMode {
    SEQUENTIAL,             // Sequential execution
    PARALLEL,               // Parallel execution
    PIPELINED,              // Pipelined execution
    STREAMING,              // Streaming execution
    BATCH,                  // Batch execution
    HYBRID                  // Hybrid execution
};

// LLM execution status
enum class LLMExecutionStatus {
    IDLE,                   // LLM is idle
    LOADING,                // LLM is loading
    READY,                  // LLM is ready
    EXECUTING,              // LLM is executing
    COMPLETED,              // LLM execution completed
    ERROR,                  // LLM execution error
    SUSPENDED               // LLM is suspended
};

// LLM execution priority
enum class LLMPriority {
    LOW = 0,                // Low priority
    NORMAL = 1,              // Normal priority
    HIGH = 2,                // High priority
    CRITICAL = 3             // Critical priority
};

// LLM execution configuration
struct LLMExecutionConfig {
    std::string llmId;                       // LLM identifier
    std::string modelPath;                   // Model file path
    std::string modelType;                   // Model type (GPT, BERT, etc.)
    size_t maxSequenceLength;                // Maximum sequence length
    size_t batchSize;                        // Batch size
    size_t numLayers;                        // Number of layers
    size_t hiddenSize;                       // Hidden size
    size_t numHeads;                         // Number of attention heads
    float learningRate;                      // Learning rate
    LLMExecutionMode mode;                   // Execution mode
    LLMPriority priority;                    // Execution priority
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// LLM execution request
struct LLMExecutionRequest {
    std::string requestId;                   // Request identifier
    std::string llmId;                       // LLM identifier
    std::string inputText;                   // Input text
    std::vector<std::string> inputTokens;    // Input tokens
    size_t maxOutputLength;                  // Maximum output length
    float temperature;                       // Sampling temperature
    float topP;                              // Top-p sampling
    int topK;                                // Top-k sampling
    bool streamOutput;                       // Stream output flag
    std::string prompt;                      // System prompt
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::milliseconds timeout;     // Request timeout
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// LLM execution response
struct LLMExecutionResponse {
    std::string requestId;                   // Request identifier
    std::string llmId;                       // LLM identifier
    bool success;                            // Execution success
    std::string outputText;                  // Output text
    std::vector<std::string> outputTokens;   // Output tokens
    size_t inputLength;                      // Input length
    size_t outputLength;                     // Output length
    float latency;                           // Execution latency (seconds)
    float throughput;                        // Throughput (tokens/second)
    std::string error;                       // Error message if failed
    std::chrono::system_clock::time_point completedAt; // Completion time
};

// LLM execution context
struct LLMExecutionContext {
    std::string contextId;                   // Context identifier
    std::string llmId;                       // LLM identifier
    std::vector<std::string> conversationHistory; // Conversation history
    size_t maxContextLength;                 // Maximum context length
    bool maintainContext;                    // Maintain context flag
    std::map<std::string, std::string> metadata; // Context metadata
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// LLM execution interface
class LLMExecutor {
public:
    virtual ~LLMExecutor() = default;

    // LLM lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // LLM management
    virtual std::string getLLMId() const = 0;
    virtual LLMExecutionStatus getStatus() const = 0;
    virtual LLMExecutionConfig getConfig() const = 0;
    virtual bool updateConfig(const LLMExecutionConfig& config) = 0;

    // Execution operations
    virtual std::future<LLMExecutionResponse> executeAsync(const LLMExecutionRequest& request) = 0;
    virtual LLMExecutionResponse execute(const LLMExecutionRequest& request) = 0;
    virtual bool cancelExecution(const std::string& requestId) = 0;
    virtual std::vector<std::string> getActiveRequests() const = 0;
    virtual bool isRequestActive(const std::string& requestId) const = 0;

    // Context management
    virtual std::string createContext(const LLMExecutionContext& context) = 0;
    virtual bool updateContext(const std::string& contextId, const LLMExecutionContext& context) = 0;
    virtual bool deleteContext(const std::string& contextId) = 0;
    virtual LLMExecutionContext getContext(const std::string& contextId) const = 0;
    virtual std::vector<std::string> getAllContexts() const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setPriority(LLMPriority priority) = 0;
    virtual LLMPriority getPriority() const = 0;
    virtual bool setExecutionMode(LLMExecutionMode mode) = 0;
    virtual LLMExecutionMode getExecutionMode() const = 0;
};

// Advanced LLM executor implementation
class AdvancedLLMExecutor : public LLMExecutor {
public:
    AdvancedLLMExecutor(const LLMExecutionConfig& config);
    ~AdvancedLLMExecutor() override;

    // LLM lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // LLM management
    std::string getLLMId() const override;
    LLMExecutionStatus getStatus() const override;
    LLMExecutionConfig getConfig() const override;
    bool updateConfig(const LLMExecutionConfig& config) override;

    // Execution operations
    std::future<LLMExecutionResponse> executeAsync(const LLMExecutionRequest& request) override;
    LLMExecutionResponse execute(const LLMExecutionRequest& request) override;
    bool cancelExecution(const std::string& requestId) override;
    std::vector<std::string> getActiveRequests() const override;
    bool isRequestActive(const std::string& requestId) const override;

    // Context management
    std::string createContext(const LLMExecutionContext& context) override;
    bool updateContext(const std::string& contextId, const LLMExecutionContext& context) override;
    bool deleteContext(const std::string& contextId) override;
    LLMExecutionContext getContext(const std::string& contextId) const override;
    std::vector<std::string> getAllContexts() const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setPriority(LLMPriority priority) override;
    LLMPriority getPriority() const override;
    bool setExecutionMode(LLMExecutionMode mode) override;
    LLMExecutionMode getExecutionMode() const override;

    // Advanced features
    bool suspend();
    bool resume();
    bool migrate(const std::string& targetNodeId);
    bool clone(const std::string& newLLMId);
    bool scale(size_t newBatchSize, size_t newMaxSequenceLength);
    bool optimize();
    std::map<std::string, std::string> getResourceInfo() const;
    bool validateResources() const;
    bool preloadModel();
    bool unloadModel();
    bool isModelLoaded() const;

private:
    // Internal state
    LLMExecutionConfig config_;
    LLMExecutionStatus status_;
    bool initialized_;
    LLMPriority priority_;
    LLMExecutionMode executionMode_;
    std::mutex executorMutex_;
    std::atomic<bool> profilingEnabled_;

    // Request tracking
    std::map<std::string, std::future<LLMExecutionResponse>> activeRequests_;
    std::map<std::string, std::atomic<bool>> requestCancelled_;
    std::mutex requestMutex_;

    // Context management
    std::map<std::string, LLMExecutionContext> contexts_;
    std::mutex contextMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // CUDA resources
    cudaStream_t executorStream_;
    void* deviceMemory_;
    size_t deviceMemorySize_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool allocateDeviceMemory(size_t size);
    void deallocateDeviceMemory();
    bool loadModel();
    void unloadModel();
    bool validateRequest(const LLMExecutionRequest& request);
    void updatePerformanceMetrics();
    LLMExecutionResponse executeInternal(const LLMExecutionRequest& request);
    void cleanupRequest(const std::string& requestId);
    std::string generateContextId();
    bool validateContext(const LLMExecutionContext& context);
};

// Parallel LLM execution manager
class ParallelLLMExecutionManager {
public:
    ParallelLLMExecutionManager();
    ~ParallelLLMExecutionManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // LLM management
    std::shared_ptr<LLMExecutor> createLLM(const LLMExecutionConfig& config);
    bool destroyLLM(const std::string& llmId);
    std::shared_ptr<LLMExecutor> getLLM(const std::string& llmId);
    std::vector<std::shared_ptr<LLMExecutor>> getAllLLMs();
    std::vector<std::shared_ptr<LLMExecutor>> getLLMsByPriority(LLMPriority priority);
    std::vector<std::shared_ptr<LLMExecutor>> getLLMsByMode(LLMExecutionMode mode);

    // Execution management
    std::future<LLMExecutionResponse> executeAsync(const LLMExecutionRequest& request);
    LLMExecutionResponse execute(const LLMExecutionRequest& request);
    bool cancelExecution(const std::string& requestId);
    bool cancelAllExecutions();
    std::vector<std::string> getActiveRequests();
    std::vector<std::string> getActiveRequestsByLLM(const std::string& llmId);

    // Parallel execution
    std::vector<LLMExecutionResponse> executeParallel(const std::vector<LLMExecutionRequest>& requests);
    std::vector<LLMExecutionResponse> executePipelined(const std::vector<LLMExecutionRequest>& requests);
    std::vector<LLMExecutionResponse> executeBatch(const std::vector<LLMExecutionRequest>& requests);
    std::vector<LLMExecutionResponse> executeHybrid(const std::vector<LLMExecutionRequest>& requests);

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleLLMs();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getLLMCounts();
    std::map<std::string, double> getExecutionMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMaxLLMs(int maxLLMs);
    int getMaxLLMs() const;
    void setExecutionPolicy(const std::string& policy);
    std::string getExecutionPolicy() const;
    void setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<LLMExecutor>> llms_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    int maxLLMs_;
    std::string executionPolicy_;
    std::string loadBalancingStrategy_;

    // Execution tracking
    std::map<std::string, std::string> requestToLLM_;
    std::map<std::string, std::chrono::system_clock::time_point> requestStartTime_;

    // Helper methods
    bool validateLLMCreation(const LLMExecutionConfig& config);
    bool validateExecutionRequest(const LLMExecutionRequest& request);
    std::string generateLLMId();
    bool cleanupLLM(const std::string& llmId);
    void updateSystemMetrics();
    bool findBestLLM(const LLMExecutionRequest& request, std::string& bestLLMId);
    bool executeOnLLM(const std::string& llmId, const LLMExecutionRequest& request);
    std::vector<std::string> selectLLMsForParallelExecution(const std::vector<LLMExecutionRequest>& requests);
    std::vector<std::string> selectLLMsForPipelinedExecution(const std::vector<LLMExecutionRequest>& requests);
    std::vector<std::string> selectLLMsForBatchExecution(const std::vector<LLMExecutionRequest>& requests);
    std::vector<std::string> selectLLMsForHybridExecution(const std::vector<LLMExecutionRequest>& requests);
};

// Global parallel LLM execution system
class GlobalParallelLLMExecutionSystem {
public:
    static GlobalParallelLLMExecutionSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<ParallelLLMExecutionManager> getExecutionManager();
    std::shared_ptr<LLMExecutor> createLLM(const LLMExecutionConfig& config);
    bool destroyLLM(const std::string& llmId);
    std::shared_ptr<LLMExecutor> getLLM(const std::string& llmId);

    // Quick access methods
    std::future<LLMExecutionResponse> executeAsync(const LLMExecutionRequest& request);
    LLMExecutionResponse execute(const LLMExecutionRequest& request);
    std::vector<LLMExecutionResponse> executeParallel(const std::vector<LLMExecutionRequest>& requests);
    std::vector<std::shared_ptr<LLMExecutor>> getAllLLMs();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalParallelLLMExecutionSystem();
    ~GlobalParallelLLMExecutionSystem();

    std::shared_ptr<ParallelLLMExecutionManager> executionManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace parallel
} // namespace cogniware
