#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>

namespace cogniware {

// Common model configuration structure
struct ModelConfig {
    std::string modelId;
    std::string modelType;
    std::string modelPath;
    std::map<std::string, std::string> parameters;
    bool enableGpu;
    int maxBatchSize;
    float memoryLimit;
    std::string quantizationType;
    bool enableDynamicBatching;
    std::map<std::string, float> resourceLimits;
};

// Model inference request structure
struct InferenceRequest {
    std::string requestId;
    std::string modelId;
    std::vector<float> inputData;
    std::map<std::string, std::string> parameters;
    bool requireConfidence;
    bool requireEmbeddings;
    int maxTokens;
    float temperature;
};

// Model inference response structure
struct InferenceResponse {
    std::string requestId;
    std::string modelId;
    std::vector<float> outputData;
    float confidence;
    std::vector<float> embeddings;
    std::map<std::string, float> metadata;
    bool success;
    std::string errorMessage;
};

// Model training request structure
struct TrainingRequest {
    std::string requestId;
    std::string modelId;
    std::vector<float> trainingData;
    std::vector<float> validationData;
    std::map<std::string, std::string> parameters;
    int epochs;
    float learningRate;
    std::string optimizer;
    std::string lossFunction;
};

// Model training response structure
struct TrainingResponse {
    std::string requestId;
    std::string modelId;
    float finalLoss;
    std::map<std::string, float> metrics;
    bool success;
    std::string errorMessage;
};

// Model status structure
struct ModelStatus {
    std::string modelId;
    bool isLoaded;
    bool isTraining;
    float memoryUsage;
    float gpuUtilization;
    int currentBatchSize;
    std::map<std::string, float> resourceUtilization;
    std::string currentState;
};

// Model interface class
class IModelInterface {
public:
    virtual ~IModelInterface() = default;

    // Model lifecycle management
    virtual bool initialize(const ModelConfig& config) = 0;
    virtual bool shutdown() = 0;
    virtual bool loadModel() = 0;
    virtual bool unloadModel() = 0;

    // Model operations
    virtual InferenceResponse inference(const InferenceRequest& request) = 0;
    virtual TrainingResponse train(const TrainingRequest& request) = 0;
    virtual bool saveModel(const std::string& path) = 0;
    virtual bool loadModelFromPath(const std::string& path) = 0;

    // Model status and monitoring
    virtual ModelStatus getStatus() const = 0;
    virtual bool updateConfig(const ModelConfig& config) = 0;
    virtual std::map<std::string, float> getMetrics() const = 0;

    // Resource management
    virtual bool allocateResources() = 0;
    virtual bool releaseResources() = 0;
    virtual bool optimizeResources() = 0;
};

// Model factory interface
class IModelFactory {
public:
    virtual ~IModelFactory() = default;
    virtual std::shared_ptr<IModelInterface> createModel(const ModelConfig& config) = 0;
    virtual bool registerModelType(const std::string& type, 
                                 std::function<std::shared_ptr<IModelInterface>(const ModelConfig&)> factory) = 0;
};

} // namespace cogniware 