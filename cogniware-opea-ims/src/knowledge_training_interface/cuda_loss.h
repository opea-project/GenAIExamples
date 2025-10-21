#ifndef MSMARTCOMPUTE_CUDA_LOSS_H
#define MSMARTCOMPUTE_CUDA_LOSS_H

#include "training_control_hooks.h"
#include <cuda_runtime.h>
#include <thrust/device_vector.h>
#include <memory>

namespace cogniware {

class CUDACrossEntropyLoss : public ILossFunction {
public:
    CUDACrossEntropyLoss();
    ~CUDACrossEntropyLoss();

    float compute(const std::vector<float>& outputs, const std::vector<float>& targets) override;

private:
    cudaStream_t stream_;
    thrust::device_vector<float> deviceOutputs_;
    thrust::device_vector<float> deviceTargets_;
    thrust::device_vector<float> deviceLoss_;
};

class CUDAMSELoss : public ILossFunction {
public:
    CUDAMSELoss();
    ~CUDAMSELoss();

    float compute(const std::vector<float>& outputs, const std::vector<float>& targets) override;

private:
    cudaStream_t stream_;
    thrust::device_vector<float> deviceOutputs_;
    thrust::device_vector<float> deviceTargets_;
    thrust::device_vector<float> deviceLoss_;
};

class CUDABinaryCrossEntropyLoss : public ILossFunction {
public:
    CUDABinaryCrossEntropyLoss();
    ~CUDABinaryCrossEntropyLoss();

    float compute(const std::vector<float>& outputs, const std::vector<float>& targets) override;

private:
    cudaStream_t stream_;
    thrust::device_vector<float> deviceOutputs_;
    thrust::device_vector<float> deviceTargets_;
    thrust::device_vector<float> deviceLoss_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_LOSS_H 