#include "activation_kernels.h"
#include "cuda_utils.h"
#include <spdlog/spdlog.h>

namespace msmartcompute {
namespace llm_inference {

// CUDA kernel for ReLU activation
__global__ void reluKernel(float* output, const float* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = max(0.0f, input[idx]);
    }
}

__global__ void reluKernel(half* output, const half* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = __hmax(__float2half(0.0f), input[idx]);
    }
}

// CUDA kernel for GELU activation
__global__ void geluKernel(float* output, const float* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = input[idx];
        output[idx] = 0.5f * x * (1.0f + tanhf(sqrtf(2.0f / M_PI) * (x + 0.044715f * x * x * x)));
    }
}

__global__ void geluKernel(half* output, const half* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = __half2float(input[idx]);
        output[idx] = __float2half(0.5f * x * (1.0f + tanhf(sqrtf(2.0f / M_PI) * (x + 0.044715f * x * x * x))));
    }
}

// CUDA kernel for SiLU (Swish) activation
__global__ void siluKernel(float* output, const float* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = input[idx];
        output[idx] = x / (1.0f + expf(-x));
    }
}

__global__ void siluKernel(half* output, const half* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = __half2float(input[idx]);
        output[idx] = __float2half(x / (1.0f + expf(-x)));
    }
}

// CUDA kernel for Tanh activation
__global__ void tanhKernel(float* output, const float* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = tanhf(input[idx]);
    }
}

__global__ void tanhKernel(half* output, const half* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = __float2half(tanhf(__half2float(input[idx])));
    }
}

// CUDA kernel for Sigmoid activation
__global__ void sigmoidKernel(float* output, const float* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = 1.0f / (1.0f + expf(-input[idx]));
    }
}

__global__ void sigmoidKernel(half* output, const half* input, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = __half2float(input[idx]);
        output[idx] = __float2half(1.0f / (1.0f + expf(-x)));
    }
}

// CUDA kernel for Softmax activation
__global__ void softmaxKernel(float* output, const float* input, int batch_size, int seq_len, int hidden_size) {
    int batch_idx = blockIdx.x;
    int seq_idx = blockIdx.y;
    int tid = threadIdx.x;
    
    extern __shared__ float sdata[];
    
    // Load input data
    if (tid < hidden_size) {
        sdata[tid] = input[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid];
    }
    __syncthreads();
    
    // Find maximum value
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset && tid + offset < hidden_size) {
            sdata[tid] = max(sdata[tid], sdata[tid + offset]);
        }
        __syncthreads();
    }
    
    float max_val = sdata[0];
    __syncthreads();
    
    // Compute exp and sum
    if (tid < hidden_size) {
        sdata[tid] = expf(input[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid] - max_val);
    }
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset && tid + offset < hidden_size) {
            sdata[tid] += sdata[tid + offset];
        }
        __syncthreads();
    }
    
    float sum = sdata[0];
    __syncthreads();
    
    // Normalize
    if (tid < hidden_size) {
        output[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid] = sdata[tid] / sum;
    }
}

__global__ void softmaxKernel(half* output, const half* input, int batch_size, int seq_len, int hidden_size) {
    int batch_idx = blockIdx.x;
    int seq_idx = blockIdx.y;
    int tid = threadIdx.x;
    
    extern __shared__ float sdata[];
    
    // Load input data
    if (tid < hidden_size) {
        sdata[tid] = __half2float(input[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid]);
    }
    __syncthreads();
    
    // Find maximum value
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset && tid + offset < hidden_size) {
            sdata[tid] = max(sdata[tid], sdata[tid + offset]);
        }
        __syncthreads();
    }
    
    float max_val = sdata[0];
    __syncthreads();
    
    // Compute exp and sum
    if (tid < hidden_size) {
        sdata[tid] = expf(__half2float(input[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid]) - max_val);
    }
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset && tid + offset < hidden_size) {
            sdata[tid] += sdata[tid + offset];
        }
        __syncthreads();
    }
    
    float sum = sdata[0];
    __syncthreads();
    
    // Normalize
    if (tid < hidden_size) {
        output[batch_idx * seq_len * hidden_size + seq_idx * hidden_size + tid] = __float2half(sdata[tid] / sum);
    }
}

// Kernel launcher implementations
void launchReLU(float* output, const float* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    reluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchReLU(half* output, const half* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    reluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchGELU(float* output, const float* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    geluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchGELU(half* output, const half* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    geluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSiLU(float* output, const float* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    siluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSiLU(half* output, const half* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    siluKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchTanh(float* output, const float* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    tanhKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchTanh(half* output, const half* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    tanhKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSigmoid(float* output, const float* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    sigmoidKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSigmoid(half* output, const half* input, int size, cudaStream_t stream) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    sigmoidKernel<<<num_blocks, block_size, 0, stream>>>(output, input, size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSoftmax(float* output, const float* input, int batch_size, int seq_len, int hidden_size, cudaStream_t stream) {
    dim3 block(256);
    dim3 grid(batch_size, seq_len);
    size_t shared_mem_size = hidden_size * sizeof(float);
    
    softmaxKernel<<<grid, block, shared_mem_size, stream>>>(output, input, batch_size, seq_len, hidden_size);
    CUDA_CHECK(cudaGetLastError());
}

void launchSoftmax(half* output, const half* input, int batch_size, int seq_len, int hidden_size, cudaStream_t stream) {
    dim3 block(256);
    dim3 grid(batch_size, seq_len);
    size_t shared_mem_size = hidden_size * sizeof(float);
    
    softmaxKernel<<<grid, block, shared_mem_size, stream>>>(output, input, batch_size, seq_len, hidden_size);
    CUDA_CHECK(cudaGetLastError());
}

// Generic activation launcher
void launchActivation(float* output, const float* input, int size, ActivationType type, cudaStream_t stream) {
    switch (type) {
        case ActivationType::RELU:
            launchReLU(output, input, size, stream);
            break;
        case ActivationType::GELU:
            launchGELU(output, input, size, stream);
            break;
        case ActivationType::SILU:
            launchSiLU(output, input, size, stream);
            break;
        case ActivationType::TANH:
            launchTanh(output, input, size, stream);
            break;
        case ActivationType::SIGMOID:
            launchSigmoid(output, input, size, stream);
            break;
        default:
            throw std::runtime_error("Unsupported activation type");
    }
}

void launchActivation(half* output, const half* input, int size, ActivationType type, cudaStream_t stream) {
    switch (type) {
        case ActivationType::RELU:
            launchReLU(output, input, size, stream);
            break;
        case ActivationType::GELU:
            launchGELU(output, input, size, stream);
            break;
        case ActivationType::SILU:
            launchSiLU(output, input, size, stream);
            break;
        case ActivationType::TANH:
            launchTanh(output, input, size, stream);
            break;
        case ActivationType::SIGMOID:
            launchSigmoid(output, input, size, stream);
            break;
        default:
            throw std::runtime_error("Unsupported activation type");
    }
}

} // namespace llm_inference
} // namespace msmartcompute
