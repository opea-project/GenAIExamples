#pragma once

#include <cuda_runtime.h>
#include <cuda_fp16.h>

namespace cogniware {
namespace llm_inference {

// Attention types
enum class AttentionType {
    SELF_ATTENTION,
    CROSS_ATTENTION,
    GROUPED_QUERY_ATTENTION,
    SLIDING_WINDOW_ATTENTION
};

// Attention configuration
struct AttentionConfig {
    int batch_size;
    int num_heads;
    int head_dim;
    int seq_len;
    int kv_seq_len;
    float scale;
    bool use_causal_mask;
    bool use_alibi;
    bool use_rotary;
    int rotary_dim;
    float rotary_base;
    int sliding_window_size;
    int num_kv_heads;  // For grouped query attention
};

// Kernel launcher functions
void launchAttention(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

void launchAttention(
    half* output,
    const half* query,
    const half* key,
    const half* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

// Flash attention implementation (if available)
void launchFlashAttention(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

void launchFlashAttention(
    half* output,
    const half* query,
    const half* key,
    const half* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

// Memory-efficient attention implementation
void launchMemoryEfficientAttention(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

void launchMemoryEfficientAttention(
    half* output,
    const half* query,
    const half* key,
    const half* value,
    const AttentionConfig& config,
    cudaStream_t stream = nullptr
);

// Rotary position embedding
void applyRotaryEmbedding(
    float* output,
    const float* input,
    int batch_size,
    int seq_len,
    int num_heads,
    int head_dim,
    int rotary_dim,
    float rotary_base,
    cudaStream_t stream = nullptr
);

void applyRotaryEmbedding(
    half* output,
    const half* input,
    int batch_size,
    int seq_len,
    int num_heads,
    int head_dim,
    int rotary_dim,
    float rotary_base,
    cudaStream_t stream = nullptr
);

// ALiBi position bias
void applyAlibiBias(
    float* output,
    const float* input,
    int batch_size,
    int num_heads,
    int seq_len,
    int kv_seq_len,
    cudaStream_t stream = nullptr
);

void applyAlibiBias(
    half* output,
    const half* input,
    int batch_size,
    int num_heads,
    int seq_len,
    int kv_seq_len,
    cudaStream_t stream = nullptr
);

} // namespace llm_inference
} // namespace cogniware
