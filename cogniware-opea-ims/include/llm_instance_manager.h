#ifndef LLM_INSTANCE_MANAGER_H
#define LLM_INSTANCE_MANAGER_H

#include <string>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <vector>
#include "model_loader.h"
#include "transformer_block.h"

namespace cogniware {

class LLMInstance {
public:
    LLMInstance(const std::string& model_id);
    ~LLMInstance();

    // Model loading and initialization
    bool loadModel(const std::string& path, const std::string& format);
    bool initialize();

    // Inference
    bool generate(
        const std::string& prompt,
        std::string& output,
        size_t max_tokens,
        float temperature,
        float top_p,
        int top_k
    );

    // Status and information
    bool isLoaded() const;
    const std::string& getModelId() const;
    size_t getContextLength() const;
    size_t getParameterCount() const;

private:
    // Internal state
    std::string model_id_;
    std::unique_ptr<ModelLoader> model_loader_;
    std::vector<std::unique_ptr<TransformerBlock>> transformer_blocks_;
    bool is_loaded_;

    // Memory management
    float* input_embeddings_;
    float* output_embeddings_;
    float* workspace_;
    size_t workspace_size_;

    // CUDA stream
    cudaStream_t stream_;
};

class LLMInstanceManager {
public:
    static LLMInstanceManager& getInstance();

    // Instance management
    std::shared_ptr<LLMInstance> createInstance(const std::string& model_id);
    bool removeInstance(const std::string& model_id);
    std::shared_ptr<LLMInstance> getInstance(const std::string& model_id);

    // Resource management
    size_t getTotalInstances() const;
    size_t getTotalParameters() const;
    size_t getTotalVRAMUsage() const;

    // Instance status
    std::vector<std::string> getLoadedModelIds() const;
    bool isModelLoaded(const std::string& model_id) const;

private:
    LLMInstanceManager();
    ~LLMInstanceManager();

    // Prevent copying
    LLMInstanceManager(const LLMInstanceManager&) = delete;
    LLMInstanceManager& operator=(const LLMInstanceManager&) = delete;

    // Instance tracking
    std::unordered_map<std::string, std::shared_ptr<LLMInstance>> instances_;
    mutable std::mutex instances_mutex_;
};

} // namespace cogniware

#endif // LLM_INSTANCE_MANAGER_H 