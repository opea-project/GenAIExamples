#pragma once

#include <vector>
#include <cuda_runtime.h>
#include "../cuda_runtime/matrix_vector_ops.h"

namespace cogniware {
namespace llm_inference {

// Sampling configuration
struct SamplingConfig {
    float temperature;
    float top_p;
    int top_k;
    bool use_nucleus_sampling;
    bool use_temperature;
    bool use_top_k;
    float repetition_penalty;
    float presence_penalty;
    float frequency_penalty;
    int min_tokens;
    int max_tokens;
    std::vector<int> stop_sequences;
};

// Sampling strategies
enum class SamplingStrategy {
    GREEDY,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    BEAM_SEARCH
};

// Sampling result
struct SamplingResult {
    std::vector<int> token_ids;
    std::vector<float> logits;
    float score;
    bool is_finished;
};

class SamplingStrategy {
public:
    virtual ~SamplingStrategy() = default;
    virtual SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) = 0;
};

// Concrete sampling strategies
class GreedySampling : public SamplingStrategy {
public:
    SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) override;
};

class TemperatureSampling : public SamplingStrategy {
public:
    SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) override;
};

class TopKSampling : public SamplingStrategy {
public:
    SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) override;
};

class TopPSampling : public SamplingStrategy {
public:
    SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) override;
};

class BeamSearchSampling : public SamplingStrategy {
public:
    SamplingResult sample(
        const float* logits,
        size_t vocab_size,
        const std::vector<int>& input_ids,
        const SamplingConfig& config,
        cudaStream_t stream = nullptr
    ) override;
};

// Sampling strategy factory
class SamplingStrategyFactory {
public:
    static std::unique_ptr<SamplingStrategy> createStrategy(SamplingStrategy type);
};

// Helper functions
inline std::unique_ptr<SamplingStrategy> createSamplingStrategy(SamplingStrategy type) {
    return SamplingStrategyFactory::createStrategy(type);
}

inline SamplingResult sampleTokens(
    const float* logits,
    size_t vocab_size,
    const std::vector<int>& input_ids,
    const SamplingConfig& config,
    SamplingStrategy type = SamplingStrategy::TEMPERATURE,
    cudaStream_t stream = nullptr
) {
    auto strategy = createSamplingStrategy(type);
    return strategy->sample(logits, vocab_size, input_ids, config, stream);
}

} // namespace llm_inference
} // namespace cogniware
