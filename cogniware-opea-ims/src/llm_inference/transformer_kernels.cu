#include "../include/llm_inference/transformer_kernels.h"
#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cooperative_groups.h>
#include <spdlog/spdlog.h>

namespace msmartcompute {
namespace llm_inference {

// Helper functions for CUDA error checking
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            spdlog::error("CUDA error at {}:{}: {}", __FILE__, __LINE__, cudaGetErrorString(error)); \
            return false; \
        } \
    } while(0)

// Attention kernel
__global__ void attentionKernel(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    size_t batch_size,
    size_t seq_length,
    size_t num_heads,
    size_t head_dim,
    float scale
) {
    using namespace cooperative_groups;
    thread_block block = this_thread_block();
    thread_block_tile<32> tile = tiled_partition<32>(block);

    const size_t tid = threadIdx.x;
    const size_t bid = blockIdx.x;
    const size_t head_idx = bid / (batch_size * seq_length);
    const size_t batch_idx = (bid % (batch_size * seq_length)) / seq_length;
    const size_t seq_idx = bid % seq_length;

    // Load query
    float q[32];
    if (tid < head_dim) {
        q[tid] = query[head_idx * head_dim + tid] * scale;
    }
    block.sync();

    // Compute attention scores
    float scores[32];
    for (size_t i = 0; i < seq_length; i += 32) {
        if (i + tid < seq_length) {
            float score = 0.0f;
            for (size_t j = 0; j < head_dim; ++j) {
                score += q[j] * key[i * head_dim + j];
            }
            scores[tid] = score;
        }
    }
    block.sync();

    // Apply softmax
    float max_score = -INFINITY;
    for (size_t i = 0; i < seq_length; i += 32) {
        if (i + tid < seq_length) {
            max_score = max(max_score, scores[tid]);
        }
    }
    max_score = block.reduce(max_score, [](float a, float b) { return max(a, b); });

    float sum_exp = 0.0f;
    for (size_t i = 0; i < seq_length; i += 32) {
        if (i + tid < seq_length) {
            scores[tid] = exp(scores[tid] - max_score);
            sum_exp += scores[tid];
        }
    }
    sum_exp = block.reduce(sum_exp, [](float a, float b) { return a + b; });

    for (size_t i = 0; i < seq_length; i += 32) {
        if (i + tid < seq_length) {
            scores[tid] /= sum_exp;
        }
    }
    block.sync();

    // Compute weighted sum of values
    float output_val[32];
    for (size_t i = 0; i < head_dim; i += 32) {
        if (i + tid < head_dim) {
            float sum = 0.0f;
            for (size_t j = 0; j < seq_length; ++j) {
                sum += scores[j] * value[j * head_dim + i + tid];
            }
            output_val[tid] = sum;
        }
    }
    block.sync();

    // Store output
    if (tid < head_dim) {
        output[head_idx * head_dim + tid] = output_val[tid];
    }
}

// FFN kernel
__global__ void ffnKernel(
    float* output,
    const float* input,
    const float* up_weight,
    const float* down_weight,
    size_t batch_size,
    size_t seq_length,
    size_t hidden_size,
    size_t intermediate_size
) {
    const size_t tid = threadIdx.x;
    const size_t bid = blockIdx.x;
    const size_t batch_idx = bid / seq_length;
    const size_t seq_idx = bid % seq_length;

    // First layer (up projection)
    float intermediate[32];
    for (size_t i = 0; i < intermediate_size; i += 32) {
        if (i + tid < intermediate_size) {
            float sum = 0.0f;
            for (size_t j = 0; j < hidden_size; ++j) {
                sum += input[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + j] * 
                       up_weight[j * intermediate_size + i + tid];
            }
            intermediate[tid] = sum;
        }
    }
    __syncthreads();

    // GELU activation
    for (size_t i = 0; i < intermediate_size; i += 32) {
        if (i + tid < intermediate_size) {
            float x = intermediate[tid];
            intermediate[tid] = 0.5f * x * (1.0f + tanh(sqrt(2.0f / M_PI) * (x + 0.044715f * x * x * x)));
        }
    }
    __syncthreads();

    // Second layer (down projection)
    for (size_t i = 0; i < hidden_size; i += 32) {
        if (i + tid < hidden_size) {
            float sum = 0.0f;
            for (size_t j = 0; j < intermediate_size; ++j) {
                sum += intermediate[j] * down_weight[j * hidden_size + i + tid];
            }
            output[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i + tid] = sum;
        }
    }
}

// Layer normalization kernel
__global__ void layerNormKernel(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    size_t batch_size,
    size_t seq_length,
    size_t hidden_size
) {
    using namespace cooperative_groups;
    thread_block block = this_thread_block();
    thread_block_tile<32> tile = tiled_partition<32>(block);

    const size_t tid = threadIdx.x;
    const size_t bid = blockIdx.x;
    const size_t batch_idx = bid / seq_length;
    const size_t seq_idx = bid % seq_length;

    // Compute mean
    float sum = 0.0f;
    for (size_t i = tid; i < hidden_size; i += blockDim.x) {
        sum += input[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i];
    }
    sum = block.reduce(sum, [](float a, float b) { return a + b; });
    float mean = sum / hidden_size;

    // Compute variance
    float sq_sum = 0.0f;
    for (size_t i = tid; i < hidden_size; i += blockDim.x) {
        float diff = input[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i] - mean;
        sq_sum += diff * diff;
    }
    sq_sum = block.reduce(sq_sum, [](float a, float b) { return a + b; });
    float variance = sq_sum / hidden_size;

    // Normalize and scale
    for (size_t i = tid; i < hidden_size; i += blockDim.x) {
        float normalized = (input[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i] - mean) / 
                          sqrt(variance + 1e-5f);
        output[batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i] = 
            normalized * weight[i] + bias[i];
    }
}

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
) {
    dim3 block(32);
    dim3 grid(batch_size * seq_length * num_heads);
    
    attentionKernel<<<grid, block, 0, stream>>>(
        output, query, key, value,
        batch_size, seq_length, num_heads, head_dim, scale
    );
    
    CUDA_CHECK(cudaGetLastError());
    return true;
}

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
) {
    dim3 block(32);
    dim3 grid(batch_size * seq_length);
    
    ffnKernel<<<grid, block, 0, stream>>>(
        output, input, up_weight, down_weight,
        batch_size, seq_length, hidden_size, intermediate_size
    );
    
    CUDA_CHECK(cudaGetLastError());
    return true;
}

bool launchLayerNorm(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    size_t batch_size,
    size_t seq_length,
    size_t hidden_size,
    cudaStream_t stream
) {
    dim3 block(32);
    dim3 grid(batch_size * seq_length);
    
    layerNormKernel<<<grid, block, 0, stream>>>(
        output, input, weight, bias,
        batch_size, seq_length, hidden_size
    );
    
    CUDA_CHECK(cudaGetLastError());
    return true;
}

} // namespace llm_inference
} // namespace msmartcompute 