#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <mutex>
#include <queue>
#include <functional>
#include <atomic>
#include "cuda_specialized_kernels.h"

namespace cogniware {

// Structure to hold inference results from individual LLMs
struct InferenceResult {
    std::string modelId;
    std::string response;
    float confidence;
    std::vector<float> embeddings;
    std::map<std::string, float> metadata;
    bool isComplete;
};

// Structure to hold collated results
struct CollatedResult {
    std::string finalResponse;
    std::vector<InferenceResult> individualResults;
    std::map<std::string, float> aggregatedMetadata;
    float overallConfidence;
    bool isComplete;
};

// Structure for inference configuration
struct InferenceConfig {
    std::vector<std::string> modelIds;
    float confidenceThreshold;
    int maxParallelInferences;
    bool enableKnowledgeSharing;
    bool enableCrossModelValidation;
    int timeoutMs;
    std::string aggregationStrategy;
};

// Structure for knowledge sharing configuration
struct KnowledgeSharingConfig {
    bool enableEmbeddingSharing;
    bool enableResponseSharing;
    bool enableMetadataSharing;
    float similarityThreshold;
    int maxSharedContext;
    std::string sharingStrategy;
};

class InferenceOrchestrator {
public:
    static InferenceOrchestrator& getInstance();

    // Initialization and configuration
    bool initialize(const InferenceConfig& config);
    void shutdown();
    bool setConfig(const InferenceConfig& config);
    bool setKnowledgeSharingConfig(const KnowledgeSharingConfig& config);

    // Inference management
    bool startInference(const std::string& query, std::function<void(const CollatedResult&)> callback);
    bool stopInference(const std::string& inferenceId);
    bool pauseInference(const std::string& inferenceId);
    bool resumeInference(const std::string& inferenceId);

    // Knowledge sharing
    bool shareKnowledge(const std::string& sourceModelId, const std::string& targetModelId, 
                       const std::vector<float>& embeddings);
    bool updateSharedContext(const std::string& modelId, const std::vector<float>& context);
    bool validateSharedKnowledge(const std::string& modelId, const std::vector<float>& knowledge);

    // Result management
    CollatedResult getCollatedResult(const std::string& inferenceId);
    std::vector<InferenceResult> getIndividualResults(const std::string& inferenceId);
    bool isInferenceComplete(const std::string& inferenceId);

    // Monitoring and statistics
    void enableMonitoring(bool enable);
    void setStatusCallback(std::function<void(const std::string&, float)> callback);
    void printStats() const;

private:
    InferenceOrchestrator() = default;
    ~InferenceOrchestrator() = default;
    InferenceOrchestrator(const InferenceOrchestrator&) = delete;
    InferenceOrchestrator& operator=(const InferenceOrchestrator&) = delete;

    // Internal methods
    void inferenceLoop();
    void processInferenceQueue();
    void collateResults(const std::string& inferenceId);
    void validateResults(const std::string& inferenceId);
    void aggregateMetadata(const std::string& inferenceId);
    void updateSharedKnowledge();
    void cleanupCompletedInferences();

    // Member variables
    InferenceConfig config_;
    KnowledgeSharingConfig sharingConfig_;
    std::mutex mutex_;
    std::atomic<bool> running_{false};
    std::thread inferenceThread_;
    std::queue<std::string> inferenceQueue_;
    std::map<std::string, CollatedResult> results_;
    std::map<std::string, std::vector<float>> sharedContext_;
    std::map<std::string, std::vector<float>> sharedEmbeddings_;
    std::map<std::string, std::function<void(const CollatedResult&)>> callbacks_;
    std::atomic<bool> monitoringEnabled_{false};
    std::function<void(const std::string&, float)> statusCallback_;
};

} // namespace cogniware 