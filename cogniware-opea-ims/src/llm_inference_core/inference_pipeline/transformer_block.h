#pragma once

#include <memory>
#include <vector>
#include <cuda_runtime.h>
#include "../cuda_runtime/matrix_vector_ops.h"
#include "kv_cache_manager.h"

namespace cogniware {
namespace llm_inference {

// Transformer block configuration
struct TransformerBlockConfig {
    size_t hidden_size;
    size_t num_attention_heads;
    size_t intermediate_size;
    size_t max_sequence_length;
    float dropout_rate;
    bool use_fp16;
    bool use_bias;
    bool use_layer_norm;
    bool use_residual;
    std::string activation_type;
};

// Attention configuration
struct AttentionConfig {
    size_t num_heads;
    size_t head_dim;
    size_t hidden_size;
    float attention_dropout;
    bool use_bias;
    bool use_rotary_embeddings;
    bool use_alibi;
    float rotary_embedding_base;
    int rotary_embedding_dim;
};

// Feed-forward configuration
struct FeedForwardConfig {
    size_t hidden_size;
    size_t intermediate_size;
    float dropout_rate;
    bool use_bias;
    std::string activation_type;
};

class TransformerBlock {
public:
    TransformerBlock(const TransformerBlockConfig& config);
    ~TransformerBlock();

    // Forward pass
    void forward(
        float* output,
        const float* input,
        const float* attention_mask,
        const KVCacheEntry& kv_cache,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream = nullptr
    );

    void forward(
        half* output,
        const half* input,
        const half* attention_mask,
        const KVCacheEntry& kv_cache,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream = nullptr
    );

    // Weight management
    void loadWeights(const std::string& path);
    void saveWeights(const std::string& path) const;
    void initializeWeights();

    // Configuration
    const TransformerBlockConfig& getConfig() const;
    void setConfig(const TransformerBlockConfig& config);

    // Memory management
    size_t getParameterSize() const;
    size_t getActivationSize(size_t batch_size, size_t sequence_length) const;

private:
    // Internal helper functions
    void initializeAttention();
    void initializeFeedForward();
    void validateConfig(const TransformerBlockConfig& config);
    void allocateBuffers(size_t batch_size, size_t sequence_length);

    // Attention operations
    void computeAttention(
        float* output,
        const float* input,
        const float* attention_mask,
        const KVCacheEntry& kv_cache,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream
    );

    void computeAttention(
        half* output,
        const half* input,
        const half* attention_mask,
        const KVCacheEntry& kv_cache,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream
    );

    // Feed-forward operations
    void computeFeedForward(
        float* output,
        const float* input,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream
    );

    void computeFeedForward(
        half* output,
        const half* input,
        size_t batch_size,
        size_t sequence_length,
        cudaStream_t stream
    );

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline std::unique_ptr<TransformerBlock> createTransformerBlock(
    const TransformerBlockConfig& config
) {
    return std::make_unique<TransformerBlock>(config);
}

} // namespace llm_inference
} // namespace cogniware
