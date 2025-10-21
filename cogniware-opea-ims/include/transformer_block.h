#ifndef TRANSFORMER_BLOCK_H
#define TRANSFORMER_BLOCK_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <memory>
#include "gpu_memory_manager.h"

namespace cogniware {

class TransformerBlock {
public:
    TransformerBlock(size_t hidden_size, size_t num_heads, size_t intermediate_size);
    ~TransformerBlock();

    // Initialize with weights
    bool initialize(const float* weights, size_t layer_idx);

    // Forward pass
    bool forward(
        float* output,
        const float* input,
        size_t batch_size,
        size_t seq_length,
        cudaStream_t stream = nullptr
    );

    // Get memory requirements
    size_t getWorkspaceSize(size_t batch_size, size_t seq_length) const;
    size_t getKVCacheSize(size_t batch_size, size_t seq_length) const;

    // KV cache management
    bool allocateKVCache(size_t batch_size, size_t seq_length);
    void freeKVCache();
    bool updateKVCache(size_t batch_size, size_t seq_length);

private:
    // CUDA kernels
    bool computeAttention(
        float* output,
        const float* query,
        const float* key,
        const float* value,
        size_t batch_size,
        size_t seq_length,
        cudaStream_t stream
    );

    bool computeFFN(
        float* output,
        const float* input,
        size_t batch_size,
        size_t seq_length,
        cudaStream_t stream
    );

    bool computeLayerNorm(
        float* output,
        const float* input,
        const float* weight,
        const float* bias,
        size_t batch_size,
        size_t seq_length,
        cudaStream_t stream
    );

    // Internal state
    size_t hidden_size_;
    size_t num_heads_;
    size_t intermediate_size_;
    size_t head_dim_;

    // Weights
    float* query_weight_;
    float* key_weight_;
    float* value_weight_;
    float* output_weight_;
    float* ffn_up_weight_;
    float* ffn_down_weight_;
    float* layer_norm1_weight_;
    float* layer_norm1_bias_;
    float* layer_norm2_weight_;
    float* layer_norm2_bias_;

    // KV cache
    float* key_cache_;
    float* value_cache_;
    size_t cache_batch_size_;
    size_t cache_seq_length_;

    // Workspace
    float* workspace_;
    size_t workspace_size_;

    // CUDA handles
    cublasHandle_t cublas_handle_;
};

} // namespace cogniware

#endif // TRANSFORMER_BLOCK_H 