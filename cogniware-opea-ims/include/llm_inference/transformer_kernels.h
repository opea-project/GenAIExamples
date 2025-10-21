#pragma once

#include <cuda_runtime.h>

namespace cogniware {
namespace llm_inference {

// Kernel launcher functions
bool launchAttention(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    size_t batch_size,
    size_t seq_length,
    size_t num_heads,
    size_t head_dim,
    float scale,
    cudaStream_t stream
);

bool launchFFN(
    float* output,
    const float* input,
    const float* up_weight,
    const float* down_weight,
    size_t batch_size,
    size_t seq_length,
    size_t hidden_size,
    size_t intermediate_size,
    cudaStream_t stream
);

bool launchLayerNorm(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    size_t batch_size,
    size_t seq_length,
    size_t hidden_size,
    cudaStream_t stream
);

} // namespace llm_inference
} // namespace cogniware 