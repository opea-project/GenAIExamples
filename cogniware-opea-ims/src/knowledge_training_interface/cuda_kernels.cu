#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <thrust/device_vector.h>
#include <thrust/host_vector.h>
#include <thrust/execution_policy.h>
#include <thrust/transform.h>
#include <thrust/reduce.h>
#include <thrust/functional.h>
#include <thrust/iterator/zip_iterator.h>
#include <thrust/tuple.h>
#include <curand_kernel.h>
#include <cublas_v2.h>
#include <cusolverDn.h>

namespace msmartcompute {
namespace cuda {

// CUDA error checking macro
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            fprintf(stderr, "CUDA error at %s:%d: %s\n", \
                    __FILE__, __LINE__, cudaGetErrorString(error)); \
            exit(EXIT_FAILURE); \
        } \
    } while(0)

// Forward pass kernel
__global__ void forwardKernel(
    const float* input,
    const float* weights,
    float* output,
    int batchSize,
    int inputSize,
    int outputSize
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < batchSize * outputSize) {
        int batch = idx / outputSize;
        int outIdx = idx % outputSize;
        float sum = 0.0f;
        
        for (int i = 0; i < inputSize; i++) {
            sum += input[batch * inputSize + i] * weights[i * outputSize + outIdx];
        }
        
        output[idx] = sum;
    }
}

// Backward pass kernel
__global__ void backwardKernel(
    const float* input,
    const float* gradOutput,
    float* gradWeights,
    float* gradInput,
    int batchSize,
    int inputSize,
    int outputSize,
    float learningRate
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < inputSize * outputSize) {
        int inIdx = idx / outputSize;
        int outIdx = idx % outputSize;
        float grad = 0.0f;
        
        for (int b = 0; b < batchSize; b++) {
            grad += input[b * inputSize + inIdx] * gradOutput[b * outputSize + outIdx];
        }
        
        gradWeights[idx] -= learningRate * grad;
    }
}

// Loss computation kernel
__global__ void computeLossKernel(
    const float* output,
    const float* target,
    float* loss,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float diff = output[idx] - target[idx];
        loss[idx] = 0.5f * diff * diff;  // MSE loss
    }
}

// Activation function kernels
__global__ void reluKernel(float* data, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        data[idx] = max(0.0f, data[idx]);
    }
}

__global__ void reluGradKernel(
    const float* data,
    const float* grad,
    float* output,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = data[idx] > 0.0f ? grad[idx] : 0.0f;
    }
}

// Optimizer kernels
__global__ void adamUpdateKernel(
    float* weights,
    float* momentum,
    float* velocity,
    const float* gradients,
    int size,
    float learningRate,
    float beta1,
    float beta2,
    float epsilon,
    int step
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        momentum[idx] = beta1 * momentum[idx] + (1.0f - beta1) * gradients[idx];
        velocity[idx] = beta2 * velocity[idx] + (1.0f - beta2) * gradients[idx] * gradients[idx];
        
        float mHat = momentum[idx] / (1.0f - powf(beta1, step));
        float vHat = velocity[idx] / (1.0f - powf(beta2, step));
        
        weights[idx] -= learningRate * mHat / (sqrtf(vHat) + epsilon);
    }
}

// Batch normalization kernels
__global__ void batchNormForwardKernel(
    const float* input,
    float* output,
    const float* gamma,
    const float* beta,
    float* runningMean,
    float* runningVar,
    int batchSize,
    int channels,
    int spatialSize,
    float momentum,
    float epsilon
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < batchSize * channels * spatialSize) {
        int c = (idx / spatialSize) % channels;
        float mean = runningMean[c];
        float var = runningVar[c];
        
        float normalized = (input[idx] - mean) / sqrtf(var + epsilon);
        output[idx] = gamma[c] * normalized + beta[c];
    }
}

// Attention mechanism kernels
__global__ void selfAttentionKernel(
    const float* query,
    const float* key,
    const float* value,
    float* output,
    int batchSize,
    int seqLen,
    int headSize,
    int numHeads
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < batchSize * seqLen * headSize) {
        int b = idx / (seqLen * headSize);
        int s = (idx / headSize) % seqLen;
        int h = idx % headSize;
        
        float sum = 0.0f;
        for (int t = 0; t < seqLen; t++) {
            float score = 0.0f;
            for (int d = 0; d < headSize; d++) {
                score += query[b * seqLen * headSize + s * headSize + d] *
                        key[b * seqLen * headSize + t * headSize + d];
            }
            score /= sqrtf(headSize);
            
            for (int d = 0; d < headSize; d++) {
                sum += score * value[b * seqLen * headSize + t * headSize + d];
            }
        }
        output[idx] = sum;
    }
}

// Dropout kernel
__global__ void dropoutKernel(
    float* data,
    float* mask,
    int size,
    float dropoutRate,
    curandState* states
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float random = curand_uniform(&states[idx]);
        mask[idx] = random > dropoutRate ? 1.0f : 0.0f;
        data[idx] *= mask[idx];
    }
}

// Metric computation kernels
__global__ void computeAccuracyKernel(
    const float* output,
    const float* target,
    float* accuracy,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        int pred = roundf(output[idx]);
        int actual = roundf(target[idx]);
        accuracy[idx] = (pred == actual) ? 1.0f : 0.0f;
    }
}

__global__ void computePrecisionKernel(
    const float* output,
    const float* target,
    float* precision,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        int pred = roundf(output[idx]);
        int actual = roundf(target[idx]);
        precision[idx] = (pred == 1 && actual == 1) ? 1.0f : 0.0f;
    }
}

// CUDA stream and handle management
class CUDAManager {
public:
    static CUDAManager& getInstance() {
        static CUDAManager instance;
        return instance;
    }

    cublasHandle_t getCublasHandle() { return cublasHandle_; }
    cusolverDnHandle_t getCusolverHandle() { return cusolverHandle_; }
    cudaStream_t getStream() { return stream_; }

private:
    CUDAManager() {
        CUDA_CHECK(cublasCreate(&cublasHandle_));
        CUDA_CHECK(cusolverDnCreate(&cusolverHandle_));
        CUDA_CHECK(cudaStreamCreate(&stream_));
    }

    ~CUDAManager() {
        cublasDestroy(cublasHandle_);
        cusolverDnDestroy(cusolverHandle_);
        cudaStreamDestroy(stream_);
    }

    cublasHandle_t cublasHandle_;
    cusolverDnHandle_t cusolverHandle_;
    cudaStream_t stream_;
};

} // namespace cuda
} // namespace msmartcompute 