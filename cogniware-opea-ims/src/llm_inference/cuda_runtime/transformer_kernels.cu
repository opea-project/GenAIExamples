#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cooperative_groups.h>
#include <cuda_fp16.h>

namespace msmartcompute {

// Constants for kernel configurations
constexpr int BLOCK_SIZE = 256;
constexpr int WARP_SIZE = 32;
constexpr int MAX_THREADS_PER_BLOCK = 1024;

// Helper function to get grid dimensions
__host__ __forceinline__ dim3 getGridDim(int num_blocks) {
    return dim3((num_blocks + BLOCK_SIZE - 1) / BLOCK_SIZE);
}

// Layer normalization kernel
__global__ void layerNormKernel(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    int batch_size,
    int seq_length,
    int hidden_size,
    float epsilon = 1e-5f
) {
    using namespace cooperative_groups;
    auto block = this_thread_block();
    auto warp = tiled_partition<WARP_SIZE>(block);

    const int tid = threadIdx.x;
    const int idx = blockIdx.x * blockDim.x + tid;
    const int batch_idx = idx / (seq_length * hidden_size);
    const int seq_idx = (idx / hidden_size) % seq_length;
    const int hidden_idx = idx % hidden_size;

    if (batch_idx >= batch_size || seq_idx >= seq_length || hidden_idx >= hidden_size) {
        return;
    }

    // Compute mean
    float sum = 0.0f;
    float sum_sq = 0.0f;
    for (int i = 0; i < hidden_size; i += WARP_SIZE) {
        const int offset = batch_idx * seq_length * hidden_size + seq_idx * hidden_size + i;
        if (i + warp.thread_rank() < hidden_size) {
            const float val = input[offset + warp.thread_rank()];
            sum += val;
            sum_sq += val * val;
        }
    }
    sum = warp.reduce(sum, plus<float>());
    sum_sq = warp.reduce(sum_sq, plus<float>());
    
    const float mean = sum / hidden_size;
    const float var = sum_sq / hidden_size - mean * mean;
    const float inv_std = rsqrtf(var + epsilon);

    // Normalize and scale
    const int out_idx = batch_idx * seq_length * hidden_size + seq_idx * hidden_size + hidden_idx;
    const float normalized = (input[out_idx] - mean) * inv_std;
    output[out_idx] = normalized * weight[hidden_idx] + bias[hidden_idx];
}

// Attention kernel
__global__ void attentionKernel(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    int batch_size,
    int seq_length,
    int num_heads,
    int head_dim,
    float scale
) {
    using namespace cooperative_groups;
    auto block = this_thread_block();
    auto warp = tiled_partition<WARP_SIZE>(block);

    const int tid = threadIdx.x;
    const int idx = blockIdx.x * blockDim.x + tid;
    const int batch_idx = idx / (seq_length * num_heads * head_dim);
    const int seq_idx = (idx / (num_heads * head_dim)) % seq_length;
    const int head_idx = (idx / head_dim) % num_heads;
    const int dim_idx = idx % head_dim;

    if (batch_idx >= batch_size || seq_idx >= seq_length || 
        head_idx >= num_heads || dim_idx >= head_dim) {
        return;
    }

    // Compute attention scores
    float attention_score = 0.0f;
    for (int k = 0; k < seq_length; ++k) {
        float qk = 0.0f;
        for (int d = 0; d < head_dim; d += WARP_SIZE) {
            if (d + warp.thread_rank() < head_dim) {
                const int q_offset = batch_idx * seq_length * num_heads * head_dim + 
                                   seq_idx * num_heads * head_dim + 
                                   head_idx * head_dim + d + warp.thread_rank();
                const int k_offset = batch_idx * seq_length * num_heads * head_dim + 
                                   k * num_heads * head_dim + 
                                   head_idx * head_dim + d + warp.thread_rank();
                qk += query[q_offset] * key[k_offset];
            }
        }
        qk = warp.reduce(qk, plus<float>());
        attention_score += qk * scale;
    }

    // Apply softmax
    attention_score = __expf(attention_score);
    float sum_exp = 0.0f;
    for (int k = 0; k < seq_length; ++k) {
        sum_exp += attention_score;
    }
    attention_score /= sum_exp;

    // Compute output
    float out_val = 0.0f;
    for (int k = 0; k < seq_length; ++k) {
        for (int d = 0; d < head_dim; d += WARP_SIZE) {
            if (d + warp.thread_rank() < head_dim) {
                const int v_offset = batch_idx * seq_length * num_heads * head_dim + 
                                   k * num_heads * head_dim + 
                                   head_idx * head_dim + d + warp.thread_rank();
                out_val += attention_score * value[v_offset];
            }
        }
    }
    out_val = warp.reduce(out_val, plus<float>());

    const int out_idx = batch_idx * seq_length * num_heads * head_dim + 
                       seq_idx * num_heads * head_dim + 
                       head_idx * head_dim + dim_idx;
    output[out_idx] = out_val;
}

// Feed-forward network kernel
__global__ void ffnKernel(
    float* output,
    const float* input,
    const float* up_weight,
    const float* down_weight,
    int batch_size,
    int seq_length,
    int hidden_size,
    int intermediate_size
) {
    using namespace cooperative_groups;
    auto block = this_thread_block();
    auto warp = tiled_partition<WARP_SIZE>(block);

    const int tid = threadIdx.x;
    const int idx = blockIdx.x * blockDim.x + tid;
    const int batch_idx = idx / (seq_length * hidden_size);
    const int seq_idx = (idx / hidden_size) % seq_length;
    const int hidden_idx = idx % hidden_size;

    if (batch_idx >= batch_size || seq_idx >= seq_length || hidden_idx >= hidden_size) {
        return;
    }

    // First layer (up projection)
    float intermediate[WARP_SIZE];
    for (int i = 0; i < intermediate_size; i += WARP_SIZE) {
        float sum = 0.0f;
        for (int j = 0; j < hidden_size; ++j) {
            const int in_idx = batch_idx * seq_length * hidden_size + seq_idx * hidden_size + j;
            const int weight_idx = j * intermediate_size + i + warp.thread_rank();
            if (i + warp.thread_rank() < intermediate_size) {
                sum += input[in_idx] * up_weight[weight_idx];
            }
        }
        intermediate[warp.thread_rank()] = sum;
        warp.sync();

        // Apply GELU activation
        if (i + warp.thread_rank() < intermediate_size) {
            intermediate[warp.thread_rank()] = 0.5f * intermediate[warp.thread_rank()] * 
                (1.0f + tanhf(0.797885f * (intermediate[warp.thread_rank()] + 
                0.044715f * intermediate[warp.thread_rank()] * intermediate[warp.thread_rank()])));
        }
    }

    // Second layer (down projection)
    float out_val = 0.0f;
    for (int i = 0; i < intermediate_size; ++i) {
        const int weight_idx = i * hidden_size + hidden_idx;
        out_val += intermediate[i] * down_weight[weight_idx];
    }

    const int out_idx = batch_idx * seq_length * hidden_size + seq_idx * hidden_size + hidden_idx;
    output[out_idx] = out_val;
}

// Host wrapper functions
void launchLayerNorm(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    int batch_size,
    int seq_length,
    int hidden_size,
    cudaStream_t stream
) {
    const int num_blocks = batch_size * seq_length * hidden_size;
    layerNormKernel<<<getGridDim(num_blocks), BLOCK_SIZE, 0, stream>>>(
        output, input, weight, bias, batch_size, seq_length, hidden_size
    );
}

void launchAttention(
    float* output,
    const float* query,
    const float* key,
    const float* value,
    int batch_size,
    int seq_length,
    int num_heads,
    int head_dim,
    float scale,
    cudaStream_t stream
) {
    const int num_blocks = batch_size * seq_length * num_heads * head_dim;
    attentionKernel<<<getGridDim(num_blocks), BLOCK_SIZE, 0, stream>>>(
        output, query, key, value, batch_size, seq_length, num_heads, head_dim, scale
    );
}

void launchFFN(
    float* output,
    const float* input,
    const float* up_weight,
    const float* down_weight,
    int batch_size,
    int seq_length,
    int hidden_size,
    int intermediate_size,
    cudaStream_t stream
) {
    const int num_blocks = batch_size * seq_length * hidden_size;
    ffnKernel<<<getGridDim(num_blocks), BLOCK_SIZE, 0, stream>>>(
        output, input, up_weight, down_weight, 
        batch_size, seq_length, hidden_size, intermediate_size
    );
}

} // namespace msmartcompute 