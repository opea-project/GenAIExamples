#ifndef MSMARTCOMPUTE_CUDA_SPECIALIZED_KERNELS_H
#define MSMARTCOMPUTE_CUDA_SPECIALIZED_KERNELS_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <vector>
#include <memory>
#include <string>
#include <unordered_map>

namespace cogniware {

/**
 * @brief Configuration for specialized kernels
 */
struct SpecializedKernelConfig {
    bool useTensorCores;
    bool useMixedPrecision;
    int blockSize;
    int numBlocks;
    cudaStream_t stream;
    
    // Transformer specific
    int numHeads;
    int headDim;
    int seqLength;
    float dropoutRate;
    
    // CNN specific
    int kernelSize;
    int stride;
    int padding;
    int dilation;
    
    // RNN specific
    int hiddenSize;
    int numLayers;
    bool bidirectional;
    
    // Image processing specific
    int imageWidth;
    int imageHeight;
    int numChannels;
    
    // Video processing specific
    int frameCount;
    int frameRate;
};

/**
 * @brief Base class for specialized kernels
 */
class CUDASpecializedKernel {
public:
    virtual ~CUDASpecializedKernel() = default;
    virtual bool initialize(const SpecializedKernelConfig& config) = 0;
    virtual void shutdown() = 0;
    virtual bool execute() = 0;
};

/**
 * @brief Transformer kernel implementation
 */
class CUDATransformerKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // Transformer specific operations
    bool selfAttention(float* query, float* key, float* value, float* output);
    bool multiHeadAttention(float* input, float* output);
    bool feedForward(float* input, float* output);
    bool layerNorm(float* input, float* output);
    bool dropout(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cublasHandle_t cublasHandle_;
    SpecializedKernelConfig config_;
};

/**
 * @brief CNN kernel implementation
 */
class CUDACNNKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // CNN specific operations
    bool convolution(float* input, float* kernel, float* output);
    bool pooling(float* input, float* output);
    bool batchNorm(float* input, float* output);
    bool activation(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cudnnTensorDescriptor_t inputDesc_;
    cudnnFilterDescriptor_t filterDesc_;
    cudnnConvolutionDescriptor_t convDesc_;
    cudnnPoolingDescriptor_t poolDesc_;
    cudnnActivationDescriptor_t activationDesc_;
    SpecializedKernelConfig config_;
};

/**
 * @brief RNN kernel implementation
 */
class CUDARNNKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // RNN specific operations
    bool lstm(float* input, float* output);
    bool gru(float* input, float* output);
    bool rnn(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cudnnRNNDescriptor_t rnnDesc_;
    cudnnTensorDescriptor_t inputDesc_;
    cudnnTensorDescriptor_t outputDesc_;
    SpecializedKernelConfig config_;
};

/**
 * @brief Image processing kernel implementation
 */
class CUDAImageProcessingKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // Image processing specific operations
    bool resize(float* input, float* output);
    bool rotate(float* input, float* output);
    bool filter(float* input, float* kernel, float* output);
    bool normalize(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cudnnTensorDescriptor_t inputDesc_;
    cudnnTensorDescriptor_t outputDesc_;
    SpecializedKernelConfig config_;
};

/**
 * @brief Video processing kernel implementation
 */
class CUDAVideoProcessingKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // Video processing specific operations
    bool frameExtraction(float* input, float* output);
    bool motionEstimation(float* frame1, float* frame2, float* output);
    bool temporalFiltering(float* input, float* output);
    bool frameInterpolation(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cudnnTensorDescriptor_t inputDesc_;
    cudnnTensorDescriptor_t outputDesc_;
    SpecializedKernelConfig config_;
};

/**
 * @brief Training kernel implementation
 */
class CUDATrainingKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // Training specific operations
    bool forwardPass(float* input, float* output);
    bool backwardPass(float* input, float* output);
    bool updateWeights(float* weights, float* gradients);
    bool computeLoss(float* predictions, float* targets, float* loss);
    
private:
    cudnnHandle_t cudnnHandle_;
    cublasHandle_t cublasHandle_;
    SpecializedKernelConfig config_;
};

/**
 * @brief Pre-trained model kernel implementation
 */
class CUDAPreTrainedModelKernel : public CUDASpecializedKernel {
public:
    bool initialize(const SpecializedKernelConfig& config) override;
    void shutdown() override;
    bool execute() override;
    
    // Pre-trained model specific operations
    bool loadModel(const std::string& modelPath);
    bool saveModel(const std::string& modelPath);
    bool inference(float* input, float* output);
    bool fineTune(float* input, float* output);
    
private:
    cudnnHandle_t cudnnHandle_;
    cublasHandle_t cublasHandle_;
    std::unordered_map<std::string, void*> modelWeights_;
    SpecializedKernelConfig config_;
};

/**
 * @brief Specialized kernel manager
 */
class CUDASpecializedKernelManager {
public:
    static CUDASpecializedKernelManager& getInstance();
    
    bool initialize(const SpecializedKernelConfig& config);
    void shutdown();
    
    // Kernel management
    std::shared_ptr<CUDASpecializedKernel> createKernel(const std::string& type);
    void destroyKernel(const std::string& type);
    
    // Kernel operations
    bool executeKernel(const std::string& type);
    
private:
    CUDASpecializedKernelManager() = default;
    ~CUDASpecializedKernelManager() = default;
    CUDASpecializedKernelManager(const CUDASpecializedKernelManager&) = delete;
    CUDASpecializedKernelManager& operator=(const CUDASpecializedKernelManager&) = delete;
    
    std::unordered_map<std::string, std::shared_ptr<CUDASpecializedKernel>> kernels_;
    SpecializedKernelConfig config_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_SPECIALIZED_KERNELS_H 