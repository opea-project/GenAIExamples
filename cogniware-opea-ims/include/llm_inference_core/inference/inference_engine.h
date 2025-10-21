#pragma once

#include "llm_inference_core/model/model_manager.h"
#include "llm_inference_core/tokenizer_interface/base_tokenizer.h"
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <unordered_map>
#include <functional>

namespace cogniware {
namespace llm_inference {
    class TokenizerFactory;
}

struct InferenceRequest {
    std::string modelId;
    std::string prompt;
    size_t maxTokens;
    float temperature;
    float topP;
    size_t numBeams;
    bool streamOutput;
};

struct InferenceResponse {
    std::string generatedText;
    size_t numTokens;
    float latency;
    bool success;
    std::string error;
};

class InferenceEngine {
public:
    static InferenceEngine& getInstance();

    // Delete copy constructor and assignment operator
    InferenceEngine(const InferenceEngine&) = delete;
    InferenceEngine& operator=(const InferenceEngine&) = delete;

    // Initialization
    bool initialize();
    void shutdown();
    
    // Inference
    InferenceResponse processRequest(const InferenceRequest& request);
    bool streamResponse(const InferenceRequest& request,
                       std::function<void(const std::string&)> callback);
    
    // Model management
    bool loadModel(const ModelConfig& config);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;
    
    // Statistics
    ModelStats getModelStats(const std::string& modelId) const;
    size_t getTotalInferences() const;
    float getAverageLatency() const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    InferenceEngine();
    ~InferenceEngine();

    // Helper methods
    bool validateRequest(const InferenceRequest& request);
    bool prepareModel(const std::string& modelId);
    void updateStatistics(const std::string& modelId,
                         size_t tokens,
                         float latency);
    
    // CUDA and tokenizer initialization
    bool initializeCUDA();
    bool initializeTokenizerFactory();
    
    // Tokenizer management
    std::shared_ptr<llm_inference::BaseTokenizer> getTokenizer(const std::string& modelId);
    
    // Inference execution
    bool runInference(const std::string& modelId,
                     const std::vector<int>& inputTokens,
                     std::vector<int>& outputTokens,
                     const InferenceRequest& request);
    
    bool runStreamingInference(const std::string& modelId,
                              const std::vector<int>& inputTokens,
                              const InferenceRequest& request,
                              std::function<void(const std::vector<int>&)> tokenCallback);
    
    // Model manager reference
    ModelManager& modelManager_;
    
    // Tokenizer management
    std::unordered_map<std::string, std::shared_ptr<llm_inference::BaseTokenizer>> tokenizers_;
    std::unique_ptr<llm_inference::TokenizerFactory> tokenizerFactory_;
    
    // CUDA state
    bool cudaInitialized_;
    
    // Statistics
    size_t totalInferences_;
    float totalLatency_;
    
    // Thread safety
    mutable std::mutex mutex_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 