#ifndef MSMARTCOMPUTE_ENHANCED_CUDA_KERNELS_H
#define MSMARTCOMPUTE_ENHANCED_CUDA_KERNELS_H

#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <curand_kernel.h>
#include <vector>
#include <memory>
#include <string>

namespace cogniware {

// Kernel configuration constants
constexpr int TILE_SIZE = 32;
constexpr int MAX_BLOCK_SIZE = 1024;
constexpr int WARP_SIZE = 32;
constexpr float M_PI = 3.14159265358979323846f;

// Enhanced Kernel Manager Class
class EnhancedCUDAKernelManager {
public:
    static EnhancedCUDAKernelManager& getInstance();
    
    // Initialization and configuration
    bool initialize();
    void shutdown();
    bool setOptimizationLevel(int level);
    bool enableTensorCores();
    bool disableTensorCores();
    bool enableMixedPrecision();
    bool disableMixedPrecision();
    
    // Matrix operations
    bool matrixMultiply(
        const void* A, const void* B, void* C,
        int M, int N, int K,
        cudaDataType_t dataType,
        float alpha = 1.0f, float beta = 0.0f,
        cudaStream_t stream = 0
    );
    
    bool batchMatrixMultiply(
        const void* A, const void* B, void* C,
        int batchSize, int M, int N, int K,
        cudaDataType_t dataType,
        float alpha = 1.0f, float beta = 0.0f,
        cudaStream_t stream = 0
    );
    
    // Convolution operations
    bool convolutionForward(
        const void* input, const void* filter, void* output,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding,
        cudaDataType_t dataType,
        cudaStream_t stream = 0
    );
    
    bool convolutionBackward(
        const void* gradOutput, const void* input, const void* filter,
        void* gradInput, void* gradFilter,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding,
        cudaDataType_t dataType,
        cudaStream_t stream = 0
    );
    
    // Attention operations
    bool multiHeadAttention(
        const void* query, const void* key, const void* value,
        void* output, void* attentionWeights,
        int batchSize, int seqLength, int numHeads, int headDim,
        float scale = 1.0f,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Activation functions
    bool applyActivation(
        void* data, int size,
        const std::string& activationType,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool applyReLU(void* data, int size, float slope = 0.0f, cudaStream_t stream = 0);
    bool applyGELU(void* data, int size, cudaStream_t stream = 0);
    bool applySwish(void* data, int size, cudaStream_t stream = 0);
    bool applySigmoid(void* data, int size, cudaStream_t stream = 0);
    bool applyTanh(void* data, int size, cudaStream_t stream = 0);
    
    // Normalization operations
    bool layerNormalization(
        void* output, const void* input, const void* gamma, const void* beta,
        int batchSize, int seqLength, int hiddenSize,
        float epsilon = 1e-5f,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool batchNormalization(
        void* output, const void* input, const void* gamma, const void* beta,
        void* runningMean, void* runningVar,
        int batchSize, int channels, int spatialSize,
        float momentum = 0.1f, float epsilon = 1e-5f,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Dropout operations
    bool dropout(
        void* output, const void* input, void* mask,
        int size, float dropoutRate, unsigned int seed,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Optimizer operations
    bool adamOptimizer(
        void* params, const void* gradients, void* m, void* v,
        int size, float learningRate, float beta1, float beta2, float epsilon, int step,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool sgdOptimizer(
        void* params, const void* gradients,
        int size, float learningRate, float momentum = 0.0f,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Loss functions
    bool crossEntropyLoss(
        void* loss, const void* logits, const int* targets,
        int batchSize, int numClasses,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool mseLoss(
        void* loss, const void* predictions, const void* targets,
        int size,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Utility operations
    bool softmax(
        void* output, const void* input,
        int batchSize, int seqLength,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool memoryCopy(
        void* dst, const void* src, int size,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    bool memorySet(
        void* data, int size, float value,
        cudaDataType_t dataType = CUDA_R_32F,
        cudaStream_t stream = 0
    );
    
    // Performance monitoring
    struct KernelStats {
        float executionTime;
        float memoryBandwidth;
        float computeThroughput;
        int occupancy;
    };
    
    KernelStats getKernelStats() const;
    void resetKernelStats();
    
    // Error handling
    std::string getLastError() const;
    void clearLastError();

private:
    EnhancedCUDAKernelManager() = default;
    ~EnhancedCUDAKernelManager() = default;
    
    // Disable copy constructor and assignment operator
    EnhancedCUDAKernelManager(const EnhancedCUDAKernelManager&) = delete;
    EnhancedCUDAKernelManager& operator=(const EnhancedCUDAKernelManager&) = delete;
    
    // Internal state
    bool initialized_ = false;
    bool tensorCoresEnabled_ = false;
    bool mixedPrecisionEnabled_ = false;
    int optimizationLevel_ = 2;
    
    // Performance tracking
    mutable KernelStats stats_;
    mutable std::string lastError_;
    
    // Helper functions
    dim3 calculateOptimalGrid(int size, int blockSize = 256) const;
    dim3 calculateOptimalGrid2D(int width, int height, int blockSize = 256) const;
    dim3 calculateOptimalGrid3D(int width, int height, int depth, int blockSize = 256) const;
    
    bool checkDataType(cudaDataType_t dataType) const;
    bool checkMemoryAlignment(const void* ptr, size_t size) const;
    void updateStats(float executionTime, size_t memorySize, int numOperations);
};

// Kernel launcher functions (for direct kernel calls)
namespace kernel_launcher {
    
    // Matrix multiplication launchers
    void launchMatrixMultiply(
        const float* A, const float* B, float* C,
        int M, int N, int K,
        float alpha = 1.0f, float beta = 0.0f,
        cudaStream_t stream = 0
    );
    
    void launchMatrixMultiplyHalf(
        const __half* A, const __half* B, __half* C,
        int M, int N, int K,
        float alpha = 1.0f, float beta = 0.0f,
        cudaStream_t stream = 0
    );
    
    // Convolution launchers
    void launchConvolutionForward(
        const float* input, const float* filter, float* output,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding,
        cudaStream_t stream = 0
    );
    
    // Attention launchers
    void launchMultiHeadAttention(
        const float* query, const float* key, const float* value,
        float* output, float* attentionWeights,
        int batchSize, int seqLength, int numHeads, int headDim,
        float scale = 1.0f,
        cudaStream_t stream = 0
    );
    
    // Activation launchers
    void launchReLU(float* data, int size, float slope = 0.0f, cudaStream_t stream = 0);
    void launchGELU(float* data, int size, cudaStream_t stream = 0);
    void launchSwish(float* data, int size, cudaStream_t stream = 0);
    
    // Normalization launchers
    void launchLayerNorm(
        float* output, const float* input, const float* gamma, const float* beta,
        int batchSize, int seqLength, int hiddenSize, float epsilon = 1e-5f,
        cudaStream_t stream = 0
    );
    
    // Dropout launcher
    void launchDropout(
        float* output, const float* input, float* mask,
        int size, float dropoutRate, unsigned int seed,
        cudaStream_t stream = 0
    );
    
    // Optimizer launchers
    void launchAdamOptimizer(
        float* params, float* gradients, float* m, float* v,
        int size, float learningRate, float beta1, float beta2, float epsilon, int step,
        cudaStream_t stream = 0
    );
    
    // Loss launchers
    void launchCrossEntropyLoss(
        float* loss, const float* logits, const int* targets,
        int batchSize, int numClasses,
        cudaStream_t stream = 0
    );
    
    // Utility launchers
    void launchSoftmax(
        float* output, const float* input,
        int batchSize, int seqLength,
        cudaStream_t stream = 0
    );
    
    void launchMemoryCopy(float* dst, const float* src, int size, cudaStream_t stream = 0);
    void launchMemorySet(float* data, int size, float value, cudaStream_t stream = 0);
    
} // namespace kernel_launcher

// Performance profiling utilities
class KernelProfiler {
public:
    static KernelProfiler& getInstance();
    
    void startProfiling(const std::string& kernelName);
    void endProfiling();
    
    struct ProfileResult {
        std::string kernelName;
        float executionTime;
        size_t memorySize;
        int numOperations;
        cudaStream_t stream;
    };
    
    std::vector<ProfileResult> getProfileResults() const;
    void clearProfileResults();
    
    void enableProfiling(bool enable = true);
    bool isProfilingEnabled() const;

private:
    KernelProfiler() = default;
    ~KernelProfiler() = default;
    
    bool profilingEnabled_ = false;
    std::vector<ProfileResult> results_;
    std::string currentKernel_;
    cudaEvent_t startEvent_, endEvent_;
};

} // namespace cogniware

// CUDA kernel declarations (extern "C" for CUDA compiler)
extern "C" {
    // Matrix multiplication kernels
    __global__ void enhancedMatrixMultiplyKernel(
        const float* A, const float* B, float* C,
        int M, int N, int K,
        float alpha, float beta
    );
    
    __global__ void enhancedMatrixMultiplyKernelHalf(
        const __half* A, const __half* B, __half* C,
        int M, int N, int K,
        float alpha, float beta
    );
    
    // Convolution kernels
    __global__ void enhancedConvolutionForwardKernel(
        const float* input, const float* filter, float* output,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding, int outHeight, int outWidth
    );
    
    // Attention kernels
    __global__ void enhancedMultiHeadAttentionKernel(
        const float* query, const float* key, const float* value,
        float* output, float* attention_weights,
        int batchSize, int seqLength, int numHeads, int headDim,
        float scale
    );
    
    // Activation kernels
    __global__ void enhancedReLUKernel(float* data, int size, float slope);
    __global__ void enhancedGELUKernel(float* data, int size);
    __global__ void enhancedSwishKernel(float* data, int size);
    
    // Normalization kernels
    __global__ void enhancedLayerNormKernel(
        float* output, const float* input, const float* gamma, const float* beta,
        int batchSize, int seqLength, int hiddenSize, float epsilon
    );
    
    // Dropout kernel
    __global__ void enhancedDropoutKernel(
        float* output, const float* input, float* mask,
        int size, float dropoutRate, unsigned int seed
    );
    
    // Optimizer kernels
    __global__ void enhancedAdamOptimizerKernel(
        float* params, float* gradients, float* m, float* v,
        int size, float learningRate, float beta1, float beta2, float epsilon, int step
    );
    
    // Loss kernels
    __global__ void enhancedCrossEntropyLossKernel(
        float* loss, const float* logits, const int* targets,
        int batchSize, int numClasses
    );
    
    // Memory kernels
    __global__ void enhancedMemoryCopyKernel(float* dst, const float* src, int size);
    __global__ void enhancedMemorySetKernel(float* data, int size, float value);
    
    // Utility kernels
    __global__ void enhancedSoftmaxKernel(
        float* output, const float* input, int batchSize, int seqLength
    );
    
    // Batch processing kernels
    __global__ void enhancedBatchMatrixMultiplyKernel(
        const float* A, const float* B, float* C,
        int batchSize, int M, int N, int K,
        float alpha, float beta
    );
}

#endif // MSMARTCOMPUTE_ENHANCED_CUDA_KERNELS_H 