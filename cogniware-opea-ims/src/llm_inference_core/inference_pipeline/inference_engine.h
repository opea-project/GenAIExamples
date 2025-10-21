#pragma once

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <cuda_runtime.h>
#include "../cuda_runtime/cuda_stream_manager.h"
#include "../cuda_runtime/gpu_memory_manager.h"
#include "kv_cache_manager.h"
#include "sampling_strategies.h"
#include "transformer_block.h"

namespace cogniware {
namespace llm_inference {

// Forward declarations
class ModelConfig;
class Tokenizer;

// Inference engine configuration
struct InferenceConfig {
    int max_batch_size;
    int max_sequence_length;
    int num_attention_heads;
    int hidden_size;
    int num_layers;
    float temperature;
    float top_p;
    int top_k;
    bool use_cache;
    bool use_fp16;
    std::string model_path;
    std::string tokenizer_path;
};

// Inference statistics
struct InferenceStats {
    size_t total_tokens_processed;
    size_t total_sequences;
    float average_latency;
    float peak_memory_usage;
    std::unordered_map<std::string, float> layer_latencies;
};

class InferenceEngine {
public:
    static InferenceEngine& getInstance();

    // Prevent copying
    InferenceEngine(const InferenceEngine&) = delete;
    InferenceEngine& operator=(const InferenceEngine&) = delete;

    // Initialization and cleanup
    void initialize(const InferenceConfig& config);
    void cleanup();

    // Model loading and unloading
    void loadModel(const std::string& model_path);
    void unloadModel();

    // Inference operations
    std::vector<int> generate(
        const std::vector<int>& input_ids,
        int max_length,
        const SamplingConfig& sampling_config = SamplingConfig()
    );

    std::vector<std::vector<int>> batchGenerate(
        const std::vector<std::vector<int>>& input_ids,
        int max_length,
        const SamplingConfig& sampling_config = SamplingConfig()
    );

    // Cache management
    void clearCache();
    void setCacheSize(size_t size);
    size_t getCacheSize() const;

    // Statistics and monitoring
    InferenceStats getStats() const;
    void resetStats();
    void enableProfiling(bool enable);

    // Device management
    void setDevice(int device_id);
    int getCurrentDevice() const;

private:
    InferenceEngine();
    ~InferenceEngine();

    // Internal helper functions
    void initializeCUDA();
    void initializeModel();
    void initializeTokenizer();
    void validateConfig(const InferenceConfig& config);
    void updateStats(const InferenceStats& stats);

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline InferenceEngine& getInferenceEngine() {
    return InferenceEngine::getInstance();
}

inline void initializeInference(const InferenceConfig& config) {
    getInferenceEngine().initialize(config);
}

inline void cleanupInference() {
    getInferenceEngine().cleanup();
}

inline std::vector<int> generateText(
    const std::vector<int>& input_ids,
    int max_length,
    const SamplingConfig& sampling_config = SamplingConfig()
) {
    return getInferenceEngine().generate(input_ids, max_length, sampling_config);
}

inline std::vector<std::vector<int>> batchGenerateText(
    const std::vector<std::vector<int>>& input_ids,
    int max_length,
    const SamplingConfig& sampling_config = SamplingConfig()
) {
    return getInferenceEngine().batchGenerate(input_ids, max_length, sampling_config);
}

inline void clearInferenceCache() {
    getInferenceEngine().clearCache();
}

inline InferenceStats getInferenceStats() {
    return getInferenceEngine().getStats();
}

} // namespace llm_inference
} // namespace cogniware
