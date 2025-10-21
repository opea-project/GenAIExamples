#ifndef MSMARTCOMPUTE_CUDA_KERNEL_MANAGER_H
#define MSMARTCOMPUTE_CUDA_KERNEL_MANAGER_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <memory>
#include <vector>
#include <string>
#include <unordered_map>
#include <mutex>

namespace cogniware {

/**
 * @brief CUDA kernel configuration
 */
struct KernelConfig {
    bool useTensorCores;
    bool useMixedPrecision;
    int blockSize;
    int numBlocks;
    cudaStream_t stream;
};

/**
 * @brief CUDA kernel manager class
 */
class CUDAKernelManager {
public:
    static CUDAKernelManager& getInstance();

    // Kernel management
    bool initialize(const KernelConfig& config);
    void shutdown();
    bool setKernelConfig(const KernelConfig& config);
    KernelConfig getKernelConfig() const;

    // Tensor core operations
    bool enableTensorCores();
    void disableTensorCores();
    bool areTensorCoresEnabled() const;

    // Mixed precision operations
    bool enableMixedPrecision();
    void disableMixedPrecision();
    bool isMixedPrecisionEnabled() const;

    // Matrix multiplication
    bool matrixMultiply(
        const void* A, const void* B, void* C,
        int m, int n, int k,
        cudaDataType_t dataType
    );

    // Convolution operations
    bool convolutionForward(
        const void* input, const void* filter, void* output,
        int batchSize, int inChannels, int outChannels,
        int height, int width, int kernelSize,
        int stride, int padding,
        cudaDataType_t dataType
    );

    // Activation functions
    bool applyActivation(
        void* data, int size,
        const std::string& activationType,
        cudaDataType_t dataType
    );

    // Batch normalization
    bool batchNormalization(
        void* data, const void* gamma, const void* beta,
        void* runningMean, void* runningVar,
        int batchSize, int channels, int spatialSize,
        float momentum, float epsilon,
        cudaDataType_t dataType
    );

    // Attention mechanism
    bool selfAttention(
        const void* query, const void* key, const void* value,
        void* output,
        int batchSize, int seqLen, int headSize, int numHeads,
        cudaDataType_t dataType
    );

private:
    CUDAKernelManager() = default;
    ~CUDAKernelManager() = default;
    CUDAKernelManager(const CUDAKernelManager&) = delete;
    CUDAKernelManager& operator=(const CUDAKernelManager&) = delete;

    // CUDA resources
    cublasHandle_t cublasHandle_;
    cudnnHandle_t cudnnHandle_;
    cudaStream_t stream_;

    // Configuration
    KernelConfig config_;
    std::mutex mutex_;

    // Helper methods
    bool initializeCUDAResources();
    void cleanupCUDAResources();
    bool checkTensorCoreSupport() const;
    bool checkMixedPrecisionSupport() const;
    cublasComputeType_t getComputeType() const;
    cudnnDataType_t getCudnnDataType(cudaDataType_t dataType) const;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_KERNEL_MANAGER_H 