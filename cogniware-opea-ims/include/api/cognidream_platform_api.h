#ifndef MSMARTCOMPUTE_COGNIDREAM_PLATFORM_API_H
#define MSMARTCOMPUTE_COGNIDREAM_PLATFORM_API_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <unordered_map>
#include <nlohmann/json.hpp>
#include <cuda_runtime.h>

namespace cogniware {

// Forward declarations
class EnhancedDriver;

// API Request/Response structures
struct APIRequest {
    std::string method;
    std::string endpoint;
    nlohmann::json data;
    std::string sessionId;
    std::string userId;
    std::chrono::system_clock::time_point timestamp;
};

struct APIResponse {
    bool success;
    int statusCode;
    nlohmann::json data;
    std::string errorMessage;
    std::chrono::milliseconds processingTime;
};

// Model configuration
struct ModelConfig {
    std::string modelId;
    std::string modelType;
    std::string modelPath;
    int maxBatchSize;
    int maxSequenceLength;
    bool enableQuantization;
    bool enableTensorCores;
    bool enableMixedPrecision;
    nlohmann::json parameters;
};

// Inference request
struct InferenceRequest {
    std::string requestId;
    std::string modelId;
    std::vector<std::vector<float>> inputData;
    int batchSize;
    int sequenceLength;
    std::string dataType;
    nlohmann::json options;
};

// Inference response
struct InferenceResponse {
    std::string requestId;
    bool success;
    std::vector<std::vector<float>> outputData;
    float inferenceTime;
    std::string errorMessage;
};

// Training request
struct TrainingRequest {
    std::string requestId;
    std::string modelId;
    std::vector<std::vector<float>> trainingData;
    std::vector<std::vector<float>> labels;
    int epochs;
    float learningRate;
    std::string optimizer;
    std::string lossFunction;
    nlohmann::json hyperparameters;
};

// Training response
struct TrainingResponse {
    std::string requestId;
    bool success;
    float finalLoss;
    std::vector<float> lossHistory;
    float trainingTime;
    std::string errorMessage;
};

// Resource management
struct ResourceAllocation {
    std::string allocationId;
    std::string userId;
    int gpuId;
    size_t memorySize;
    int computeUnits;
    std::chrono::system_clock::time_point startTime;
    std::chrono::system_clock::time_point endTime;
};

// Performance metrics
struct PerformanceMetrics {
    float gpuUtilization;
    float memoryUtilization;
    float temperature;
    float powerUsage;
    float throughput;
    float latency;
    int activeRequests;
    int queuedRequests;
};

// CogniDream Platform API Class
class CogniDreamPlatformAPI {
public:
    static CogniDreamPlatformAPI& getInstance();
    
    // Disable copy constructor and assignment operator
    CogniDreamPlatformAPI(const CogniDreamPlatformAPI&) = delete;
    CogniDreamPlatformAPI& operator=(const CogniDreamPlatformAPI&) = delete;
    
    // Initialization and configuration
    bool initialize(const nlohmann::json& config);
    void shutdown();
    bool isInitialized() const;
    
    // Model management
    bool loadModel(const ModelConfig& config);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;
    std::vector<std::string> getLoadedModels() const;
    
    // Inference operations
    InferenceResponse executeInference(const InferenceRequest& request);
    std::string queueInference(const InferenceRequest& request);
    InferenceResponse getInferenceResult(const std::string& requestId);
    bool cancelInference(const std::string& requestId);
    
    // Training operations
    TrainingResponse executeTraining(const TrainingRequest& request);
    std::string queueTraining(const TrainingRequest& request);
    TrainingResponse getTrainingResult(const std::string& requestId);
    bool cancelTraining(const std::string& requestId);
    
    // Resource management
    ResourceAllocation allocateResources(const std::string& userId, size_t memorySize, int computeUnits);
    bool deallocateResources(const std::string& allocationId);
    std::vector<ResourceAllocation> getUserAllocations(const std::string& userId) const;
    
    // Performance monitoring
    PerformanceMetrics getPerformanceMetrics() const;
    nlohmann::json getDetailedMetrics() const;
    bool enableMetricsCollection(bool enable = true);
    
    // Session management
    std::string createSession(const std::string& userId, const std::string& modelId);
    bool endSession(const std::string& sessionId);
    bool isSessionValid(const std::string& sessionId) const;
    
    // Batch operations
    std::vector<InferenceResponse> executeBatchInference(const std::vector<InferenceRequest>& requests);
    std::vector<TrainingResponse> executeBatchTraining(const std::vector<TrainingRequest>& requests);
    
    // Optimization
    bool optimizeModel(const std::string& modelId, const nlohmann::json& optimizationConfig);
    bool quantizeModel(const std::string& modelId, const std::string& quantizationType);
    
    // Error handling
    std::string getLastError() const;
    void clearLastError();
    
    // Configuration
    nlohmann::json getConfiguration() const;
    bool updateConfiguration(const nlohmann::json& config);

private:
    CogniDreamPlatformAPI() = default;
    ~CogniDreamPlatformAPI() = default;
    
    // Internal state
    bool initialized_ = false;
    std::unique_ptr<EnhancedDriver> driver_;
    
    // Model management
    std::unordered_map<std::string, ModelConfig> loadedModels_;
    std::unordered_map<std::string, std::vector<float>> modelWeights_;
    
    // Request management
    std::unordered_map<std::string, InferenceRequest> pendingInferences_;
    std::unordered_map<std::string, TrainingRequest> pendingTraining_;
    std::unordered_map<std::string, InferenceResponse> completedInferences_;
    std::unordered_map<std::string, TrainingResponse> completedTraining_;
    
    // Resource management
    std::unordered_map<std::string, ResourceAllocation> resourceAllocations_;
    
    // Session management
    std::unordered_map<std::string, std::string> sessions_; // sessionId -> userId
    
    // Performance tracking
    PerformanceMetrics currentMetrics_;
    std::vector<PerformanceMetrics> metricsHistory_;
    bool metricsCollectionEnabled_ = true;
    
    // Error handling
    mutable std::string lastError_;
    mutable std::mutex errorMutex_;
    
    // Threading
    mutable std::mutex mutex_;
    std::thread requestProcessor_;
    std::thread metricsCollector_;
    bool running_ = false;
    
    // Internal methods
    void processRequests();
    void collectMetrics();
    bool validateRequest(const InferenceRequest& request) const;
    bool validateRequest(const TrainingRequest& request) const;
    void updateMetrics();
    nlohmann::json serializeMetrics() const;
};

// High-level convenience functions
namespace cognidream_api {
    
    // Quick inference
    std::vector<std::vector<float>> quickInference(
        const std::string& modelId,
        const std::vector<std::vector<float>>& inputData,
        const nlohmann::json& options = {}
    );
    
    // Quick training
    bool quickTraining(
        const std::string& modelId,
        const std::vector<std::vector<float>>& trainingData,
        const std::vector<std::vector<float>>& labels,
        int epochs = 10,
        float learningRate = 0.001f
    );
    
    // Model utilities
    bool saveModel(const std::string& modelId, const std::string& path);
    bool loadModelFromPath(const std::string& modelId, const std::string& path);
    nlohmann::json getModelInfo(const std::string& modelId);
    
    // Performance utilities
    PerformanceMetrics getCurrentMetrics();
    nlohmann::json getMetricsHistory(int maxEntries = 100);
    bool setPerformanceTargets(const nlohmann::json& targets);
    
} // namespace cognidream_api

} // namespace cogniware

#endif // MSMARTCOMPUTE_COGNIDREAM_PLATFORM_API_H 