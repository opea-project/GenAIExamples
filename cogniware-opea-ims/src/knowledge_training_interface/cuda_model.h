#ifndef MSMARTCOMPUTE_CUDA_MODEL_H
#define MSMARTCOMPUTE_CUDA_MODEL_H

#include "training_control_hooks.h"
#include <cuda_runtime.h>
#include <thrust/device_vector.h>
#include <memory>
#include <vector>

namespace cogniware {

class CUDAModel : public IModel {
public:
    CUDAModel(const std::vector<int>& layerSizes);
    ~CUDAModel();

    std::vector<float> forward(const DataBatch& batch) override;
    void backward(float loss) override;
    bool save(const std::string& path) const override;
    bool load(const std::string& path) override;

    // Additional CUDA-specific methods
    void setDevice(int deviceId);
    void enableMixedPrecision(bool enable);
    void setDropoutRate(float rate);
    void setBatchNormMomentum(float momentum);

private:
    // Layer structure
    struct Layer {
        thrust::device_vector<float> weights;
        thrust::device_vector<float> biases;
        thrust::device_vector<float> activations;
        thrust::device_vector<float> gradients;
        thrust::device_vector<float> momentum;
        thrust::device_vector<float> velocity;
        thrust::device_vector<float> gamma;  // For batch norm
        thrust::device_vector<float> beta;   // For batch norm
        thrust::device_vector<float> runningMean;
        thrust::device_vector<float> runningVar;
    };

    // Helper methods
    void initializeWeights();
    void initializeBatchNorm();
    void computeGradients(const thrust::device_vector<float>& outputGrad);
    void updateWeights(float learningRate);
    void applyDropout(thrust::device_vector<float>& data);
    void applyBatchNorm(Layer& layer, bool training);
    void applyActivation(Layer& layer, const std::string& activationType);
    void computeActivationGrad(Layer& layer, const std::string& activationType);

    // CUDA resources
    std::vector<Layer> layers_;
    thrust::device_vector<float> dropoutMask_;
    thrust::device_vector<curandState> randomStates_;
    cudaStream_t stream_;
    cublasHandle_t cublasHandle_;
    cusolverDnHandle_t cusolverHandle_;

    // Configuration
    std::vector<int> layerSizes_;
    int currentDevice_;
    bool mixedPrecision_;
    float dropoutRate_;
    float batchNormMomentum_;
    bool trainingMode_;

    // Memory management
    void allocateDeviceMemory();
    void freeDeviceMemory();
    void synchronizeDevice();
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_MODEL_H 