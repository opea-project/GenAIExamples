#include "cuda_kernel_manager.h"
#include <spdlog/spdlog.h>

namespace msmartcompute {

CUDAKernelManager& CUDAKernelManager::getInstance() {
    static CUDAKernelManager instance;
    return instance;
}

bool CUDAKernelManager::initialize(const KernelConfig& config) {
    config_ = config;
    
    // Initialize CUDA
    cudaError_t cudaStatus = cudaSetDevice(config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    // Initialize cuDNN
    cudnnStatus_t cudnnStatus = cudnnCreate(&cudnnHandle_);
    if (cudnnStatus != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuDNN handle: {}", cudnnGetErrorString(cudnnStatus));
        return false;
    }
    
    // Initialize cuBLAS
    cublasStatus_t cublasStatus = cublasCreate(&cublasHandle_);
    if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to create cuBLAS handle: {}", cublasStatus);
        return false;
    }
    
    // Create streams
    for (int i = 0; i < config_.numStreams; ++i) {
        cudaStream_t stream;
        cudaStatus = cudaStreamCreate(&stream);
        if (cudaStatus != cudaSuccess) {
            spdlog::error("Failed to create CUDA stream: {}", cudaGetErrorString(cudaStatus));
            return false;
        }
        streams_.push_back(stream);
    }
    
    // Enable tensor cores if supported
    if (config_.useTensorCores) {
        cublasStatus = cublasSetMathMode(cublasHandle_, CUBLAS_TENSOR_OP_MATH);
        if (cublasStatus != CUBLAS_STATUS_SUCCESS) {
            spdlog::warn("Failed to enable tensor cores: {}", cublasStatus);
        }
    }
    
    return true;
}

void CUDAKernelManager::shutdown() {
    // Destroy streams
    for (auto stream : streams_) {
        cudaStreamDestroy(stream);
    }
    streams_.clear();
    
    // Destroy handles
    cudnnDestroy(cudnnHandle_);
    cublasDestroy(cublasHandle_);
}

bool CUDAKernelManager::setKernelConfig(const KernelConfig& config) {
    config_ = config;
    
    // Update tensor core settings
    if (config_.useTensorCores) {
        cublasStatus_t status = cublasSetMathMode(cublasHandle_, CUBLAS_TENSOR_OP_MATH);
        if (status != CUBLAS_STATUS_SUCCESS) {
            spdlog::warn("Failed to enable tensor cores: {}", status);
            return false;
        }
    } else {
        cublasStatus_t status = cublasSetMathMode(cublasHandle_, CUBLAS_DEFAULT_MATH);
        if (status != CUBLAS_STATUS_SUCCESS) {
            spdlog::warn("Failed to disable tensor cores: {}", status);
            return false;
        }
    }
    
    return true;
}

KernelConfig CUDAKernelManager::getKernelConfig() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

bool CUDAKernelManager::enableTensorCores() {
    cublasStatus_t status = cublasSetMathMode(cublasHandle_, CUBLAS_TENSOR_OP_MATH);
    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to enable tensor cores: {}", status);
        return false;
    }
    return true;
}

bool CUDAKernelManager::disableTensorCores() {
    cublasStatus_t status = cublasSetMathMode(cublasHandle_, CUBLAS_DEFAULT_MATH);
    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Failed to disable tensor cores: {}", status);
        return false;
    }
    return true;
}

bool CUDAKernelManager::areTensorCoresEnabled() const {
    return config_.useTensorCores;
}

bool CUDAKernelManager::enableMixedPrecision() {
    if (!checkMixedPrecisionSupport()) {
        spdlog::error("Mixed precision not supported on this device");
        return false;
    }

    config_.useMixedPrecision = true;
    return true;
}

void CUDAKernelManager::disableMixedPrecision() {
    config_.useMixedPrecision = false;
}

bool CUDAKernelManager::isMixedPrecisionEnabled() const {
    return config_.useMixedPrecision;
}

bool CUDAKernelManager::matrixMultiply(
    const void* A, const void* B, void* C,
    int m, int n, int k,
    cudaDataType_t dataType
) {
    std::lock_guard<std::mutex> lock(mutex_);

    const float alpha = 1.0f;
    const float beta = 0.0f;

    cublasOperation_t transA = CUBLAS_OP_N;
    cublasOperation_t transB = CUBLAS_OP_N;

    cublasStatus_t status;
    if (dataType == CUDA_R_16F && config_.useMixedPrecision) {
        status = cublasHgemm(
            cublasHandle_, transA, transB,
            m, n, k,
            reinterpret_cast<const __half*>(&alpha),
            reinterpret_cast<const __half*>(A), m,
            reinterpret_cast<const __half*>(B), k,
            reinterpret_cast<const __half*>(&beta),
            reinterpret_cast<__half*>(C), m
        );
    } else {
        status = cublasSgemm(
            cublasHandle_, transA, transB,
            m, n, k,
            &alpha,
            reinterpret_cast<const float*>(A), m,
            reinterpret_cast<const float*>(B), k,
            &beta,
            reinterpret_cast<float*>(C), m
        );
    }

    if (status != CUBLAS_STATUS_SUCCESS) {
        spdlog::error("Matrix multiplication failed: {}", cublasGetErrorString(status));
        return false;
    }

    return true;
}

bool CUDAKernelManager::convolutionForward(
    const void* input, const void* filter, void* output,
    int batchSize, int inChannels, int outChannels,
    int height, int width, int kernelSize,
    int stride, int padding,
    cudaDataType_t dataType
) {
    std::lock_guard<std::mutex> lock(mutex_);

    cudnnTensorDescriptor_t inputDesc, outputDesc;
    cudnnFilterDescriptor_t filterDesc;
    cudnnConvolutionDescriptor_t convDesc;
    cudnnConvolutionFwdAlgo_t algo;
    size_t workspaceSize = 0;
    void* workspace = nullptr;

    // Create descriptors
    cudnnCreateTensorDescriptor(&inputDesc);
    cudnnCreateTensorDescriptor(&outputDesc);
    cudnnCreateFilterDescriptor(&filterDesc);
    cudnnCreateConvolutionDescriptor(&convDesc);

    // Set tensor descriptors
    cudnnSetTensor4dDescriptor(
        inputDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        batchSize,
        inChannels,
        height,
        width
    );

    cudnnSetFilter4dDescriptor(
        filterDesc,
        getCudnnDataType(dataType),
        CUDNN_TENSOR_NCHW,
        outChannels,
        inChannels,
        kernelSize,
        kernelSize
    );

    cudnnSetConvolution2dDescriptor(
        convDesc,
        padding, padding,
        stride, stride,
        1, 1,
        CUDNN_CROSS_CORRELATION,
        getCudnnDataType(dataType)
    );

    // Get output dimensions
    int outHeight, outWidth;
    cudnnGetConvolution2dForwardOutputDim(
        convDesc,
        inputDesc,
        filterDesc,
        &batchSize,
        &outChannels,
        &outHeight,
        &outWidth
    );

    cudnnSetTensor4dDescriptor(
        outputDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        batchSize,
        outChannels,
        outHeight,
        outWidth
    );

    // Find best algorithm
    cudnnConvolutionFwdAlgoPerf_t perfResults;
    int returnedAlgoCount;
    cudnnFindConvolutionForwardAlgorithm(
        cudnnHandle_,
        inputDesc,
        filterDesc,
        convDesc,
        outputDesc,
        1,
        &returnedAlgoCount,
        &perfResults
    );
    algo = perfResults.algo;

    // Get workspace size
    cudnnGetConvolutionForwardWorkspaceSize(
        cudnnHandle_,
        inputDesc,
        filterDesc,
        convDesc,
        outputDesc,
        algo,
        &workspaceSize
    );

    if (workspaceSize > 0) {
        cudaMalloc(&workspace, workspaceSize);
    }

    // Perform convolution
    const float alpha = 1.0f;
    const float beta = 0.0f;

    cudnnStatus_t status = cudnnConvolutionForward(
        cudnnHandle_,
        &alpha,
        inputDesc, input,
        filterDesc, filter,
        convDesc,
        algo,
        workspace,
        workspaceSize,
        &beta,
        outputDesc, output
    );

    // Cleanup
    if (workspace) {
        cudaFree(workspace);
    }
    cudnnDestroyTensorDescriptor(inputDesc);
    cudnnDestroyTensorDescriptor(outputDesc);
    cudnnDestroyFilterDescriptor(filterDesc);
    cudnnDestroyConvolutionDescriptor(convDesc);

    if (status != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Convolution forward failed: {}", cudnnGetErrorString(status));
        return false;
    }

    return true;
}

bool CUDAKernelManager::applyActivation(
    void* data, int size,
    const std::string& activationType,
    cudaDataType_t dataType
) {
    std::lock_guard<std::mutex> lock(mutex_);

    cudnnActivationDescriptor_t activationDesc;
    cudnnTensorDescriptor_t dataDesc;

    cudnnCreateActivationDescriptor(&activationDesc);
    cudnnCreateTensorDescriptor(&dataDesc);

    cudnnActivationMode_t mode;
    if (activationType == "relu") {
        mode = CUDNN_ACTIVATION_RELU;
    } else if (activationType == "sigmoid") {
        mode = CUDNN_ACTIVATION_SIGMOID;
    } else if (activationType == "tanh") {
        mode = CUDNN_ACTIVATION_TANH;
    } else {
        spdlog::error("Unsupported activation type: {}", activationType);
        return false;
    }

    cudnnSetActivationDescriptor(
        activationDesc,
        mode,
        CUDNN_NOT_PROPAGATE_NAN,
        0.0
    );

    cudnnSetTensor4dDescriptor(
        dataDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        1, 1, 1, size
    );

    const float alpha = 1.0f;
    const float beta = 0.0f;

    cudnnStatus_t status = cudnnActivationForward(
        cudnnHandle_,
        activationDesc,
        &alpha,
        dataDesc, data,
        &beta,
        dataDesc, data
    );

    cudnnDestroyActivationDescriptor(activationDesc);
    cudnnDestroyTensorDescriptor(dataDesc);

    if (status != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Activation forward failed: {}", cudnnGetErrorString(status));
        return false;
    }

    return true;
}

bool CUDAKernelManager::batchNormalization(
    void* data, const void* gamma, const void* beta,
    void* runningMean, void* runningVar,
    int batchSize, int channels, int spatialSize,
    float momentum, float epsilon,
    cudaDataType_t dataType
) {
    std::lock_guard<std::mutex> lock(mutex_);

    cudnnTensorDescriptor_t dataDesc, bnDesc;
    cudnnCreateTensorDescriptor(&dataDesc);
    cudnnCreateTensorDescriptor(&bnDesc);

    cudnnSetTensor4dDescriptor(
        dataDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        batchSize,
        channels,
        spatialSize,
        spatialSize
    );

    cudnnSetTensor4dDescriptor(
        bnDesc,
        CUDNN_TENSOR_NCHW,
        getCudnnDataType(dataType),
        1,
        channels,
        1,
        1
    );

    const float alpha = 1.0f;
    const float beta = 0.0f;

    cudnnStatus_t status = cudnnBatchNormalizationForwardTraining(
        cudnnHandle_,
        CUDNN_BATCHNORM_SPATIAL,
        &alpha,
        &beta,
        dataDesc, data,
        dataDesc, data,
        bnDesc,
        gamma,
        beta,
        momentum,
        runningMean,
        runningVar,
        epsilon,
        nullptr,
        nullptr
    );

    cudnnDestroyTensorDescriptor(dataDesc);
    cudnnDestroyTensorDescriptor(bnDesc);

    if (status != CUDNN_STATUS_SUCCESS) {
        spdlog::error("Batch normalization failed: {}", cudnnGetErrorString(status));
        return false;
    }

    return true;
}

bool CUDAKernelManager::selfAttention(
    const void* query, const void* key, const void* value,
    void* output,
    int batchSize, int seqLen, int headSize, int numHeads,
    cudaDataType_t dataType
) {
    std::lock_guard<std::mutex> lock(mutex_);

    // Compute attention scores: Q * K^T
    void* attentionScores;
    cudaMalloc(&attentionScores, batchSize * numHeads * seqLen * seqLen * sizeof(float));

    if (!matrixMultiply(
        query, key,
        attentionScores,
        batchSize * numHeads * seqLen,
        seqLen,
        headSize,
        dataType
    )) {
        cudaFree(attentionScores);
        return false;
    }

    // Scale attention scores
    const float scale = 1.0f / std::sqrt(static_cast<float>(headSize));
    cublasSscal(
        cublasHandle_,
        batchSize * numHeads * seqLen * seqLen,
        &scale,
        reinterpret_cast<float*>(attentionScores),
        1
    );

    // Apply softmax to attention scores
    if (!applyActivation(
        attentionScores,
        batchSize * numHeads * seqLen * seqLen,
        "softmax",
        dataType
    )) {
        cudaFree(attentionScores);
        return false;
    }

    // Compute weighted sum: attention_scores * V
    if (!matrixMultiply(
        attentionScores,
        value,
        output,
        batchSize * numHeads * seqLen,
        headSize,
        seqLen,
        dataType
    )) {
        cudaFree(attentionScores);
        return false;
    }

    cudaFree(attentionScores);
    return true;
}

bool CUDAKernelManager::checkTensorCoreSupport() const {
    int deviceId;
    cudaGetDevice(&deviceId);
    
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, deviceId);
    
    // Check if device supports tensor cores (compute capability >= 7.0)
    return (prop.major > 7 || (prop.major == 7 && prop.minor >= 0));
}

bool CUDAKernelManager::checkMixedPrecisionSupport() const {
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, 0);
    return prop.major >= 7;  // Volta architecture or newer
}

cublasComputeType_t CUDAKernelManager::getComputeType() const {
    if (config_.useTensorCores && config_.useMixedPrecision) {
        return CUBLAS_COMPUTE_32F_FAST_TF32;
    } else if (config_.useTensorCores) {
        return CUBLAS_COMPUTE_32F;
    } else {
        return CUBLAS_COMPUTE_32F;
    }
}

cudnnDataType_t CUDAKernelManager::getCudnnDataType(cudaDataType_t dataType) const {
    switch (dataType) {
        case CUDA_R_16F:
            return CUDNN_DATA_HALF;
        case CUDA_R_32F:
            return CUDNN_DATA_FLOAT;
        case CUDA_R_64F:
            return CUDNN_DATA_DOUBLE;
        default:
            return CUDNN_DATA_FLOAT;
    }
}

} // namespace msmartcompute 