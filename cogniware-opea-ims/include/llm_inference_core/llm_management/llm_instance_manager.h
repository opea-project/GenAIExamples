#pragma once

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>
#include "llm_inference_core/transformer/transformer_block.h"

namespace cogniware {

class LLMInstance {
public:
    LLMInstance(const std::string& modelId,
                const std::string& modelPath,
                const TransformerBlock::Config& config);
    ~LLMInstance();

    // Model loading and initialization
    bool loadModel();
    bool initialize();
    
    // Inference
    bool generate(const std::vector<int>& inputIds,
                 std::vector<int>& outputIds,
                 int maxLength,
                 float temperature = 1.0f,
                 int topK = 50,
                 float topP = 0.9f);
    
    // Model information
    const std::string& getModelId() const { return modelId_; }
    const std::string& getModelPath() const { return modelPath_; }
    const TransformerBlock::Config& getConfig() const { return config_; }
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    std::string modelId_;
    std::string modelPath_;
    TransformerBlock::Config config_;
    std::unique_ptr<TransformerBlock> transformer_;
    std::string lastError_;
    
    // Helper methods
    bool loadWeights();
    bool initializeTransformer();
    void cleanup();
};

class LLMInstanceManager {
public:
    static LLMInstanceManager& getInstance();

    // Delete copy constructor and assignment operator
    LLMInstanceManager(const LLMInstanceManager&) = delete;
    LLMInstanceManager& operator=(const LLMInstanceManager&) = delete;

    // Instance management
    std::shared_ptr<LLMInstance> createInstance(const std::string& modelId,
                                              const std::string& modelPath,
                                              const TransformerBlock::Config& config);
    bool removeInstance(const std::string& modelId);
    std::shared_ptr<LLMInstance> getInstance(const std::string& modelId);
    
    // Instance information
    size_t getTotalInstances() const;
    std::vector<std::string> getLoadedModelIds() const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    LLMInstanceManager();
    ~LLMInstanceManager();

    std::unordered_map<std::string, std::shared_ptr<LLMInstance>> instances_;
    mutable std::mutex mutex_;
    std::string lastError_;
};

} // namespace cogniware 