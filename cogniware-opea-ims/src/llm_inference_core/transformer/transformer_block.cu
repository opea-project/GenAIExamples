#include "llm_inference_core/transformer/transformer_block.h"
#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cooperative_groups.h>

namespace msmartcompute {

namespace cg = cooperative_groups;

// Helper functions for CUDA kernels
__device__ float gelu(float x) {
    return 0.5f * x * (1.0f + tanhf(sqrtf(2.0f / M_PI) * (x + 0.044715f * x * x * x)));
}

__device__ float silu(float x) {
    return x / (1.0f + expf(-x));
}

// Layer normalization kernel
__global__ void layerNormKernel(const float* input,
                              float* output,
                              const float* scale,
                              const float* bias,
                              int hiddenSize,
                              float epsilon = 1e-5f) {
    int tid = threadIdx.x;
    int bid = blockIdx.x;
    
    extern __shared__ float sdata[];
    float* mean = sdata;
    float* var = &sdata[1];
    
    // Compute mean
    float sum = 0.0f;
    for (int i = tid; i < hiddenSize; i += blockDim.x) {
        sum += input[bid * hiddenSize + i];
    }
    sum = blockReduceSum(sum);
    
    if (tid == 0) {
        *mean = sum / hiddenSize;
    }
    __syncthreads();
    
    // Compute variance
    float sqSum = 0.0f;
    for (int i = tid; i < hiddenSize; i += blockDim.x) {
        float diff = input[bid * hiddenSize + i] - *mean;
        sqSum += diff * diff;
    }
    sqSum = blockReduceSum(sqSum);
    
    if (tid == 0) {
        *var = sqSum / hiddenSize + epsilon;
    }
    __syncthreads();
    
    // Normalize and scale
    for (int i = tid; i < hiddenSize; i += blockDim.x) {
        float normalized = (input[bid * hiddenSize + i] - *mean) / sqrtf(*var);
        output[bid * hiddenSize + i] = scale[i] * normalized + bias[i];
    }
}

// Self-attention kernel
__global__ void attentionKernel(const float* input,
                              float* output,
                              const float* weights,
                              float* kv_cache,
                              int batchSize,
                              int seqLength,
                              int hiddenSize,
                              int numHeads,
                              float scale) {
    int tid = threadIdx.x;
    int bid = blockIdx.x;
    
    // Compute Q, K, V projections
    float* q = input + bid * hiddenSize;
    float* k = input + bid * hiddenSize + hiddenSize;
    float* v = input + bid * hiddenSize + 2 * hiddenSize;
    
    // Compute attention scores
    float* scores = output + bid * numHeads * seqLength;
    for (int h = 0; h < numHeads; ++h) {
        for (int i = tid; i < seqLength; i += blockDim.x) {
            float score = 0.0f;
            for (int j = 0; j < hiddenSize / numHeads; ++j) {
                score += q[h * (hiddenSize / numHeads) + j] * k[i * (hiddenSize / numHeads) + j];
            }
            scores[h * seqLength + i] = score * scale;
        }
    }
    __syncthreads();
    
    // Apply softmax
    for (int h = 0; h < numHeads; ++h) {
        float maxScore = -INFINITY;
        for (int i = tid; i < seqLength; i += blockDim.x) {
            maxScore = max(maxScore, scores[h * seqLength + i]);
        }
        maxScore = blockReduceMax(maxScore);
        
        float sum = 0.0f;
        for (int i = tid; i < seqLength; i += blockDim.x) {
            scores[h * seqLength + i] = expf(scores[h * seqLength + i] - maxScore);
            sum += scores[h * seqLength + i];
        }
        sum = blockReduceSum(sum);
        
        for (int i = tid; i < seqLength; i += blockDim.x) {
            scores[h * seqLength + i] /= sum;
        }
    }
    __syncthreads();
    
    // Compute output
    float* out = output + bid * hiddenSize;
    for (int h = 0; h < numHeads; ++h) {
        for (int i = tid; i < hiddenSize / numHeads; i += blockDim.x) {
            float sum = 0.0f;
            for (int j = 0; j < seqLength; ++j) {
                sum += scores[h * seqLength + j] * v[j * (hiddenSize / numHeads) + i];
            }
            out[h * (hiddenSize / numHeads) + i] = sum;
        }
    }
}

// Feed-forward network kernel
__global__ void ffnKernel(const float* input,
                         float* output,
                         const float* weights1,
                         const float* weights2,
                         int hiddenSize,
                         int intermediateSize,
                         const char* activationType) {
    int tid = threadIdx.x;
    int bid = blockIdx.x;
    
    // First layer
    float* intermediate = output + bid * intermediateSize;
    for (int i = tid; i < intermediateSize; i += blockDim.x) {
        float sum = 0.0f;
        for (int j = 0; j < hiddenSize; ++j) {
            sum += input[bid * hiddenSize + j] * weights1[j * intermediateSize + i];
        }
        
        // Apply activation
        if (strcmp(activationType, "gelu") == 0) {
            intermediate[i] = gelu(sum);
        } else if (strcmp(activationType, "silu") == 0) {
            intermediate[i] = silu(sum);
        } else {
            intermediate[i] = sum;  // Linear activation
        }
    }
    __syncthreads();
    
    // Second layer
    float* out = output + bid * hiddenSize;
    for (int i = tid; i < hiddenSize; i += blockDim.x) {
        float sum = 0.0f;
        for (int j = 0; j < intermediateSize; ++j) {
            sum += intermediate[j] * weights2[j * hiddenSize + i];
        }
        out[i] = sum;
    }
}

// Helper function for block reduction
template<typename T>
__device__ T blockReduceSum(T val) {
    cg::thread_block block = cg::this_thread_block();
    T sum = val;
    
    for (int offset = block.size() / 2; offset > 0; offset /= 2) {
        sum += block.shfl_down(sum, offset);
    }
    
    return sum;
}

template<typename T>
__device__ T blockReduceMax(T val) {
    cg::thread_block block = cg::this_thread_block();
    T max_val = val;
    
    for (int offset = block.size() / 2; offset > 0; offset /= 2) {
        max_val = max(max_val, block.shfl_down(max_val, offset));
    }
    
    return max_val;
}

bool TransformerBlock::launchLayerNormKernel(const float* input,
                                           float* output,
                                           int batchSize,
                                           int seqLength,
                                           cudaStream_t stream) {
    int blockSize = 256;
    int numBlocks = batchSize * seqLength;
    int sharedMemSize = 2 * sizeof(float);  // For mean and variance
    
    layerNormKernel<<<numBlocks, blockSize, sharedMemSize, stream>>>(
        input, output,
        d_weights_,  // Scale
        d_weights_ + config_.hiddenSize,  // Bias
        config_.hiddenSize
    );
    
    cudaError_t error = cudaGetLastError();
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return false;
    }
    
    return true;
}

bool TransformerBlock::launchAttentionKernel(const float* input,
                                           float* output,
                                           int batchSize,
                                           int seqLength,
                                           cudaStream_t stream) {
    int blockSize = 256;
    int numBlocks = batchSize;
    float scale = 1.0f / sqrtf(config_.hiddenSize / config_.numHeads);
    
    attentionKernel<<<numBlocks, blockSize, 0, stream>>>(
        input, output,
        d_weights_,
        d_kv_cache_,
        batchSize,
        seqLength,
        config_.hiddenSize,
        config_.numHeads,
        scale
    );
    
    cudaError_t error = cudaGetLastError();
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return false;
    }
    
    return true;
}

bool TransformerBlock::launchFFNKernel(const float* input,
                                     float* output,
                                     int batchSize,
                                     int seqLength,
                                     cudaStream_t stream) {
    int blockSize = 256;
    int numBlocks = batchSize;
    
    ffnKernel<<<numBlocks, blockSize, 0, stream>>>(
        input, output,
        d_weights_,  // First layer weights
        d_weights_ + config_.hiddenSize * config_.intermediateSize,  // Second layer weights
        config_.hiddenSize,
        config_.intermediateSize,
        config_.activationType.c_str()
    );
    
    cudaError_t error = cudaGetLastError();
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return false;
    }
    
    return true;
}

} // namespace msmartcompute 